#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

#FIXME: When the user attempts to run a dirty simulation (i.e., a simulation
#with unsaved changes), the GUI should prompt the user as to whether or not
#they would like to save those changes *BEFORE* running the simulation. In
#theory, we should be able to reuse existing "sim_conf" functionality to do so.

#FIXME: When the application closure signal is emitted (e.g., from the
#QApplication.aboutToQuit() signal and/or QMainWindow.closeEvent() handler), the
#following logic should be performed (in order):
#
#1. In the QMainWindow.closeEvent() handler only:
#   * When the user attempts to close the application when one or more threads
#     are currently running, a warning dialog should be displayed to the user
#     confirming this action.
#2. If any workers are currently running:
#   * The stop() signal of each such worker should be emitted.
#   * The slot handling this application closure event should then block for a
#     reasonable amount of time (say, 100ms?) for this worker to gracefully
#     terminate. If this worker fails to do so, more drastic measures may be
#     necessary. (Gulp.)
#3. If any threads are currently running (e.g., as testable via the
#   guithreadpool.is_working() tester), these threads should be terminated as
#   gracefully as feasible.
#
#Note the QThreadPool.waitForDone(), which may assist us. If we do call that
#function, we'll absolutely need to pass a reasonable timeout; if this timeout
#is hit, the thread pool will need to be forcefully terminated. *shrug*
#FIXME: Gracefully terminate worker threads that are still running at
#application shutdown. Ideally, this should reduce to simply:
#
#* Defining a new "QBetseeSimmer" slot whose corresponding signal is emitted at
#  application shutdown.
#* Connect this slot to that signal in QBetseeSimmer._init_connections().
#* In this slot (in order):
#  * If "_worker" is non-None:
#    * Directly call the _worker.stop() method.
#    * Wait for this method to emit the "stopped" signal.

#FIXME: Improve the underlying exporting simulation subcommands in BETSE (e.g.,
#"betse plot seed") to perform routine progress callbacks.

#FIXME: Note in a more appropriate docstring somewhere that the text overlaid
#onto the progress bar is only conditionally displayed depending on the current
#style associated with this bar. Specifically, the official documentation notes:
#
#    Note that whether or not the text is drawn is dependent on the style.
#    Currently CDE, CleanLooks, Motif, and Plastique draw the text. Mac, Windows
#    and WindowsXP style do not.
#
#For orthogonality with native applications, it's probably best to accept this
#constraint as is and intentionally avoid setting a misson-critical format on
#progress bars. Nonetheless, this *DOES* appear to be circumventable by manually
#overlaying a "QLabel" widget over the "QProgressBar" widget in question. For
#details, see the following StackOverflow answer (which, now that I peer closely
#at it, appears to be quite incorrect... but, something's better than nothing):
#    https://stackoverflow.com/a/28816650/2809027

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, QObject, Slot  #, Signal
from betse.exceptions import BetseSimUnstableException
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.py import pyref
from betse.util.type import enums
from betse.util.type.cls import classes
from betse.util.type.text import strs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import (
    BetseeSimmerException, BetseeSimmerBetseException)
# from betsee.guimetadata import SCRIPT_BASENAME
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunphase import (
    QBetseeSimmerPhaseABC,
    QBetseeSimmerPhaseSeed,
    QBetseeSimmerPhaseInit,
    QBetseeSimmerPhaseSim,
)
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState,
    SIM_PHASE_KIND_TO_NAME,
    SIMMER_STATE_TO_STATUS_VERBOSE,
    SIMMER_STATES_FIXED,
    SIMMER_STATES_FLUID,
    # MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS,
    # EXPORTING_TYPE_TO_STATUS_DETAILS,
)
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.gui.simtab.run.work import guisimrunworkqueue
from betsee.util.thread import guithread
from betsee.util.thread.pool import guipoolthread

# ....................{ CLASSES                           }....................
class QBetseeSimmer(QBetseeSimmerStatefulABC):
    '''
    High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
    *and* controlling the execution of simulation phases).

    This simulator maintains all state required to interactively manage these
    subcommands (e.g., ``betse sim``, ``betse plot init``), including:

    * A queue of all simulation subcommands to be interactively run.
    * Whether or not a simulation subcommand is currently being run.
    * The state of the currently run simulation subcommand (if any), including:
      * Visualization (typically, Vmem animation) of the most recent step
        completed for this subcommand.
      * Textual status describing this step in human-readable language.
      * Numeric progress as a relative function of the total number of steps
        required by this subcommand.

    Attributes (Private: Non-widgets)
    ----------
    _sim_conf : QBetseeSimConf
        Object encapsulating high-level simulation configuration state.

    Attributes (Private: Phase)
    ----------
    _PHASES : SequenceTypes
        Immutable sequence of all simulator phase controllers (e.g.,
        :attr:`_phase_seed`), needed for iteration over these controllers. For
        sanity, these phases are ordered is simulation order such that:
        * The seed phase is listed *before* the initialization phase.
        * The initialization phase is listed *before* the simulation phase.
    _PHASE_KIND_TO_PHASE : MappingType
        Dictionary mapping from phase type to simulator phase.
    _phase_seed : QBetseeSimmerPhaseSeed
        Controller for all simulator widgets pertaining to the seed phase.
    _phase_init : QBetseeSimmerPhaseInit
        Controller for all simulator widgets pertaining to the initialization
        phase.
    _phase_sim : QBetseeSimmerPhaseSim
        Controller for all simulator widgets pertaining to the simulation
        phase.

    Attributes (Private: Thread)
    ----------
    _thread : QBetseeWorkerThread
        Thread controller owning all simulator workers (i.e.,
        :class:`QBetseeSimmerWorkerABC` instances responsible for running
        queued simulation subcommands in a multithreaded manner).

    Attributes (Private: Thread: Worker)
    ----------
    _worker : {QBetseeSimmerWorkerABC, NoneType}
        Weak reference to the currently working simulator worker if any *or*
        ``None`` otherwise (i.e., if no worker is currently working), allowing
        this worker to be gracefully halted on application shutdown. Note that
        this worker's thread pool owns this worker and therefore fully manages
        this worker's lifecycle. Preserving a strong (i.e., standard) rather
        than weak reference to this worker would induce a subtle race condition
        between Qt's explicit deletion and Python's implicit garbage collection
        of this worker on completion.
    _worker_phase : {QBetseeSimmerPhaseABC, NoneType}
        **Currently working simulator phase** (i.e., phase that is being
        modelled or exported by the currently working simulator worker) if any
        *or* ``None`` otherwise (i.e., if no worker is currently working).
    _workers_cls : {QueueType, NoneType}
        **Simulator worker subclass queue** (i.e., double-ended queue of all
        simulator worker subclasses to be subsequently instantiated and run in
        a multithreaded manner by this simulator, such that each worker runs a
        simulation subcommand whose corresponding checkbox is checked) if this
        simulator has started one or more such workers *or* ``None`` otherwise
        (i.e., if no such workers have been started).

    Attributes (Private: Widgets)
    ----------
    _action_sim_run_start_or_resume : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_start_or_resume`
        action.
    _action_pause : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_pause` action.
    _action_stop : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_stop` action.
    _player_progress : QProgressBar
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_progress` widget.
    _player_toolbar : QFrame
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_toolbar_frame`
        frame containing only the :class:`QToolBar` controlling this
        simulation.
    _status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_status` label,
        synopsizing the current state of this simulator.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        self._action_sim_run_start_or_resume = None
        self._action_pause = None
        self._action_stop = None
        self._player_toolbar = None
        self._worker = None
        self._worker_phase = None
        self._workers_cls = None
        self._status = None

        #FIXME: Unconvinced we still require this attribute. Consider removal.
        self._player_progress = None

        # Initialize all phases of this simulator.
        self._init_phases()


    def _init_phases(self) -> None:
        '''
        Initialize all phases of this simulator.
        '''

        # Simulator phase controllers.
        self._phase_seed = QBetseeSimmerPhaseSeed(self)
        self._phase_init = QBetseeSimmerPhaseInit(self)
        self._phase_sim  = QBetseeSimmerPhaseSim(self)

        # Dictionary mapping from phase type to simulator phase.
        self._PHASE_KIND_TO_PHASE = {
            SimPhaseKind.SEED: self._phase_seed,
            SimPhaseKind.INIT: self._phase_init,
            SimPhaseKind.SIM:  self._phase_sim,
        }

        # Sequence of all simulator phases. For iterability, these phases are
        # intentionally listed in simulation order.
        self._PHASES = (self._phase_seed, self._phase_init, self._phase_sim)


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Finalize this simulator's initialization, owned by the passed main
        window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulator.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Initialize all widgets concerning simulator state.
        self._init_widgets(main_window)

        # Connect all relevant signals and slots *AFTER* initializing these
        # widgets, as the former typically requires the latter.
        self._init_connections(main_window)



    @type_check
    def _init_widgets(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (*not* always owned by this object) concerning this
        simulator.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow`
            widget.
        '''

        # Log this initialization.
        logs.log_debug('Sanitizing simulator state...')

        # Classify variables of this main window required by this simulator.
        self._action_sim_run_start_or_resume = (
            main_window.action_sim_run_start_or_resume)
        self._action_pause    = main_window.action_sim_run_pause
        self._action_stop     = main_window.action_sim_run_stop
        self._player_progress = main_window.sim_run_player_progress
        self._player_toolbar  = main_window.sim_run_player_toolbar_frame
        self._status          = main_window.sim_run_player_status

        #FIXME: Non-ideal. Ideally, this simulator would only retain
        #fine-grained references to specific attributes of this simulation
        #configurator -- ideally, via signal-slot connections.
        #FIXME: Indeed, we only appear to require the "self._sim_conf.p"
        #variable. If we recall correctly, the "Parameters" object referred to
        #by this variable should remain alive throughout the whole application
        #lifecycle. If this is indeed the case, then we can simply preserve:
        #    self._p = main_window.sim_conf.p
        self._sim_conf = main_window.sim_conf

        # Initialize all phases (in arbitrary order).
        for phase in self._PHASES:
            phase.init(main_window)

        #FIXME: Excise the following code block after hooking this high-level
        #simulator GUI into the low-level "simrunner" submodule.

        # Avoid displaying detailed status for the currently queued subcommand,
        # as the low-level BETSE codebase lacks sufficient hooks to update this
        # status in a sane manner.
        main_window.sim_run_player_substatus_group.hide()


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulator.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow`
            widget.
        '''

        # Connect each such action to this object's corresponding slot.
        self._action_sim_run_start_or_resume.triggered.connect(
            self._start_or_resume_phase)
        self._action_pause.triggered.connect(self._pause_phase)
        self._action_stop.triggered.connect(self._stop_phase)

        # For each possible phase...
        for phase in self._PHASES:
            # Connect this phase's signals to this object's equivalent slots.
            phase.set_state_signal.connect(self._set_phase_state)

            # Initialize the state of this phase *AFTER* connecting these
            # slots, implicitly initializing the state of this simulator.
            phase.update_state()

    # ..................{ PROPERTIES ~ bool : public        }..................
    @property
    def is_queued(self) -> bool:
        '''
        ``True`` only if one or more simulator phases are currently queued for
        modelling and/or exporting.
        '''

        # Return true only if one or more phases are queued.
        return any(phase.is_queued for phase in self._PHASES)

    # ..................{ PROPERTIES ~ bool : private       }..................
    @property
    def _is_working(self) -> bool:
        '''
        ``True`` only if some simulator worker is currently running.

        Equivalently, this method returns ``True`` only if this simulator is
        currently modelling or exporting some queued simulation phase.
        '''

        # Return true only if a non-empty queue of all phases to be run
        # currently exists. The lifecycle of this queue is managed in a just in
        # time (JIT) manner corresponding exactly to whether or not the
        # simulator is running. Specifically:
        #
        # * This queue defaults to "None".
        # * The _start_or_resume_phase() slot instantiates this queue on first
        #   running a new queue of simulator phases.
        # * The _stop_phase() slot reverts this queue back to "None".
        #
        # For efficiency, return this queue reduced to a boolean -- equivalent
        # to this less efficient (but more readable) pair of tests:
        #
        #    return self._workers_cls is not None and len(self._workers_cls)
        return bool(self._workers_cls)

    # ..................{ EXCEPTIONS                        }..................
    def _die_if_working(self) -> None:
        '''
        Raise an exception if some simulator worker is currently working.

        See Also
        ----------
        :meth:`_is_working`
            Further details.
        '''

        if self._is_working:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer', 'Simulation currently running.'))


    def _die_unless_working(self) -> None:
        '''
        Raise an exception unless some simulator worker is currently working.

        Equivalently, this method raises an exception if *no* simulator worker
        is currently working.

        See Also
        ----------
        :meth:`_is_working`
            Further details.
        '''

        if not self._is_working:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer', 'No simulation currently running.'))

    # ..................{ PROPERTIES ~ phase : state        }..................
    #FIXME: Consider replacing this dynamic property with direct access of the
    #underlying "self._worker_phase.state" attribute. This property doesn't
    #appear to actually do anything justifying this being a property.

    # This trivial property getter exists only so that the corresponding
    # non-trivial property setter may be defined.
    @property
    def _worker_phase_state(self) -> SimmerState:
        '''
        State of the queued simulator phase that is currently **running**
        (i.e., either being modelled or exported by this simulator) if any *or*
        raise an exception otherwise.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`_is_working` property
        is ``True``).

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
              :attr:`_workers_cls` is either ``None`` or empty).

        See Also
        ----------
        :meth:`_worker_phase`
            Further details.
        '''

        return self._worker_phase.state


    @_worker_phase_state.setter
    @type_check
    def _worker_phase_state(self, state: SimmerState) -> None:
        '''
        Set the state of the queued simulator phase that is currently
        **running** (i.e., either being modelled or exported by this simulator)
        if any to the passed state *or* raise an exception otherwise.

        This property setter additionally sets the state of this simulator to
        the passed state, avoiding subtle desynchronization issues between the
        state of this phase and this simulator. If a queued simulator phase is
        currently running, this simulator's state is *always* the state of this
        phase.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`_is_working` property
        is ``True``).

        Parameters
        ----------
        state: SimmerState
            New state to set this phase to.

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
            :attr:`_workers_cls` is either ``None`` or empty).

        See Also
        ----------
        :meth:`_worker_phase_state`
            Further details.
        '''

        #FIXME: This may now induce infinite recursion. *sigh*

        # Set the state of the currently running phase to this state.
        self._worker_phase.state = state

        # Set the state of this simulator to the same state.
        # self.state = state

    # ..................{ SLOTS ~ action : simulator        }..................
    # Slots connected to signals emitted by "QAction" objects specific to the
    # currently running simulator worker if any.

    #FIXME: Rewrite documentation to note the considerably changed behaviour.
    @Slot(bool)
    def _start_or_resume_phase(self) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling the checkable :class:`QPushButton` widget
        corresponding to the :attr:`_action_start_or_resume_phase` variable.

        This slot runs the currently queued phase by either:

        * If this phase is currently paused, resuming this phase.
        * Else, starting this phase.
        '''

        #FIXME: Raise an exception if either:
        #
        #* No phase is currently queued.
        #* A phase is currently working. Sadly, the _die_if_working() method
        #  doesn't quite appear to correspond to that condition and hence should
        #  probably be renamed to _die_if_working_or_paused(). We need a more
        #  specific _die_if_working() validator.

        # If a simulator phase is currently working, raise an exception.
        # self._die_if_working()

        #FIXME: Implement us up, please.
        # If some simulator worker was previously working before being paused,
        # resume this worker.
        if self._is_working:
            pass
        # Else, no simulator worker was previously working. In this case...
        else:
            # Initialize the queue of simulator phases to be run.
            self._enqueue_worker_types()

            # Iteratively run each such phase.
            self._start_workers()

        #FIXME: Set the state of both this simulator *AND* the currently
        #running phase *AFTER* successfully running this phase above.
        # self._worker_phase_state = SimmerState.MODELLING
        # self._worker_phase_state = SimmerState.EXPORTING


    @Slot()
    def _pause_phase(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget associated
        with the :attr:`_action_pause` action.
        '''

        # If no simulator phase is currently working, raise an exception.
        self._die_unless_working()

        #FIXME: Actually pause the running subcommand here, please.

        # Set this simulator and the previously running phase to the paused
        # state *AFTER* successfully pausing this phase.
        self._worker_phase_state = SimmerState.PAUSED


    @Slot()
    def _stop_phase(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget associated
        with the :attr:`_action_stop` action.
        '''

        # If no simulator phase is currently working, raise an exception.
        self._die_unless_working()

        #FIXME: Actually halt the running subcommand here, please.

        # Uninitialize the queue of simulator phases to be run *AFTER*
        # successfully halting this phase.
        self._dequeue_workers()

    # ..................{ SLOTS ~ action : queue            }..................
    # Slots connected to signals emitted by "QAction" objects specific to the
    # queue of simulator phases to be run.

    @Slot(QObject)
    def _set_phase_state(self, phase: QBetseeSimmerPhaseABC) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically setting the current state of any simulator phase.

        Parameters
        ----------
        phase : QBetseeSimmerPhaseABC
            Simulator phase whose current state has been set.
        '''

        # Log this slot.
        logs.log_debug(
            'Simulator phase "%s" state updated to "%s"...',
            phase.name, enums.get_member_name_lowercase(phase.state))

        # If the current state of either:
        #
        # * This phase is fixed (i.e., high-priority) and hence superceding the
        #   current state of this simulator...
        # * This simulator is fluid (i.e., low-priority) and hence superceded
        #   by current state of this phase...
        if (
            phase.state in SIMMER_STATES_FIXED or
             self.state in SIMMER_STATES_FLUID
        ):
            # If this phase's new state is unqueued...
            if phase.state is SimmerState.UNQUEUED:
                # If one or more *OTHER* phases are still queued, ignore this
                # phase's change. Unqueueing is minimally low priority.
                if self.is_queued:
                    pass
                # Else, all phases are unqueued. Set the current state of this
                # simulator to also be unqueued.
                else:
                    self.state = SimmerState.UNQUEUED
            # Else, this phase's new state unconditionally takes precedence.
            # Set the current state of this simulator to this phase's new
            # state.
            else:
                self.state = phase.state

            # Update the state of simulator widgets *AFTER* setting this state.
            self._update_widgets()

    # ..................{ UPDATERS                          }..................
    def _update_widgets(self) -> None:

        # Enable (in arbitrary order):
        #
        # * All widgets controlling the currently queued phase only if one or
        #   more phases are currently queued.
        # * All widgets halting the currently running phase only if one or more
        #   phases are currently running.
        #
        # To reduce the likelihood of accidental interaction with widgets
        # intended to be disabled, do so *BEFORE* subsequent slot logic.
        self._player_toolbar.setEnabled(self.is_queued)

        #FIXME: Replace this line after implementing the _pause_phase() method
        #with something suitable and sane.
        self._action_pause.setEnabled(False)

        #FIXME: Uncomment this line and comment the following after
        #implementing the _stop_phase() method.
        # self._action_stop.setEnabled(self._is_working)
        self._action_stop.setEnabled(False)

        # Update the verbose status of this simulator.
        self._update_status()


    def _update_status(self) -> None:
        '''
        Update the text displayed by the :attr:`_status` label, verbosely
        synopsizing the current state of this simulator.
        '''

        # Unformatted template synopsizing the current state of this simulator.
        status_text_template = SIMMER_STATE_TO_STATUS_VERBOSE[self.state]

        # Text synopsizing the type of simulation phase run by the current
        # simulator worker if any *OR* an arbitrary placeholder otherwise. In
        # the latter case, this text is guaranteed to *NOT* be interpolated by
        # this template and is thus safely ignorable.
        phase_type_name = (
            SIM_PHASE_KIND_TO_NAME[self._worker.phase_kind]
            if self._is_working else
            'the nameless that shall not be named')

        # Text synopsizing the prior state of this simulator. To permit this
        # text to be interpolated into the middle of arbitrary sentences, the
        # first character of this text is lowercased.
        status_prior_text = strs.lowercase_char_first(self._status.text())

        # Unconditionally format this text with *ALL* possible format specifiers
        # interpolated into *ALL* possible instances of this text. By design,
        # format specifiers *NOT* interpolated into this text will be ignored.
        status_text = status_text_template.format(
            phase_type=phase_type_name,
            status_prior=status_prior_text,
        )

        # Set the text of the label displaying this synopsis to this text.
        self._status.setText(status_text)

    # ..................{ QUEUERS                           }..................
    def _enqueue_worker_types(self) -> None:
        '''
        Define the :attr:`_workers_cls` of all simulator workers to be run.

        This method enqueues (i.e., pushes onto this queue) all simulator
        phases for which the end user interactively checked at least one of the
        corresponding modelling and exporting checkboxes. For sanity, phases
        are enqueued in simulation order such that:

        * The seed phase is enqueued *before* the initialization phase.
        * The initialization phase is enqueued *before* the simulation phase.

        Raises
        ----------
        BetseeSimmerException
            If either:
            * No simulator phase is currently queued.
            * Some simulator phase is currently running (i.e.,
              :attr:`_workers_cls` is already defined to be non-``None``).
        '''

        # If this controller is *NOT* currently queued, raise an exception.
        self._die_unless_queued()

        # If some simulator phase is currently running, raise an exception.
        self._die_if_working()

        # Create this simulator worker queue.
        self._workers_cls = guisimrunworkqueue.enqueue_worker_types(
            phases=self._PHASES)


    #FIXME: In theory, this still seems useful. Consider calling this method
    #somewhere appropriate (e.g., from the simulator stop slot). If we actually
    #do so, augment this method's implementation to do something useful.
    def _dequeue_workers(self) -> None:
        '''
        Revert the :attr:`_workers_cls` to ``None``, effectively dequeueing
        (i.e., popping) all previously queued simulator workers.
        '''

        # Uninitialize this queue.
        self._workers_cls = None

    # ..................{ WORKERS ~ start                   }..................
    def _start_workers(self) -> None:
        '''
        Iteratively start each simulator worker enqueued by a prior call to the
        :meth:`_enqueue_worker_types` method.
        '''

        # If one or more workers are already working, raise an exception.
        guipoolthread.die_if_working()

        # Initiate iteration by starting the first enqueued worker and
        # connecting the stop signal emitted by that worker to a slot
        # iteratively repeating this process.
        self._start_worker_next_or_noop()


    def _start_worker_next_or_noop(self) -> None:
        '''
        Iteratively start the next simulator worker (i.e., head item of the
        :attr:`_workers_cls`) enqueued by a prior call to the
        :meth:`_enqueue_worker_types` method if this queue is non-empty *or*
        reduce to a noop otherwise (i.e., if this queue is empty).
        '''

        # If no workers remain to be run...
        if not self._is_working:
            # Log this completion.
            logs.log_debug(
                'Stopping simulator work from main thread "%d"...',
                guithread.get_current_thread_id())

            # Reduce to a noop.
            return
        # Else, one or more workers remain to be run.

        # Current simulator worker subclass to be instantiated. By the above
        # conditional, this worker subclass is guaranteed to exist.
        worker_type = self._workers_cls[0]

        # Log this start.
        logs.log_debug(
            'Spawning simulator worker "%s" from main thread "%d"...',
            classes.get_name(worker_type), guithread.get_current_thread_id())

        # Current simulator worker to be run, simulating a phase of the
        # currently loaded simulation defined by this configuration file.
        worker = worker_type(conf_filename=self._sim_conf.p.conf_filename)

        # Finalize this worker's initialization.
        worker.init(progress_bar=self._player_progress)

        # Preserve a weak reference to this worker *AFTER* finalizing this
        # worker's initialization but *BEFORE* performing any subsequent
        # logic possibly assuming this reference to exist (e.g., slots).
        self._worker = pyref.proxy_weak(worker)

        # Simulator phase acted upon by this worker.
        self._worker_phase = self._PHASE_KIND_TO_PHASE[worker_type.phase_kind]

        # Connect signals emitted by this worker to slots on this simulator.
        worker.signals.failed.connect(self._handle_worker_exception)
        worker.signals.finished.connect(self._handle_worker_completion)

        # Start this worker.
        guipoolthread.start_worker(worker)

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the started() signal of this worker. After all, this
        #should only be performed if this worker is indeed successfully started
        #within this thread -- which we have no way of guaranteeing here.

        # Set the state of both this simulator *AND* the currently
        # running phase *AFTER* successfully starting this worker.
        self._worker_phase_state = worker_type.simmer_state

    # ..................{ WORKERS ~ slot                    }..................
    # Slots connected to signals emitted by "QRunnable" workers.

    @Slot(Exception)
    def _handle_worker_exception(self, exception: Exception) -> None:
        '''
        Slot signalled on the currently running simulator worker erroneously
        raising an unexpected exception.

        This slot trivially handles this exception by re-raising this
        exception.  Since the only means of explicitly re-raising an exception
        exposed by Python 3.x is to encapsulate that exception inside another
        exception, this slot unconditionally raises a
        :class:`BetseeSimmerBetseException` exception encapsulating the passed
        exception.

        Parameters
        ----------
        exception : Exception
            Exception raised by this worker.

        Raises
        ----------
        BetseeSimmerBetseException
            Unconditionally encapsulates the passed exception.
        '''

        # If this exception signifies an instability, raise a human-readable
        # translated exception synopsizing this fact. This error is
        # sufficiently common to warrant a special case improving the user
        # experience (UX).
        if isinstance(exception, BetseSimUnstableException):
            raise BetseeSimmerBetseException(
                synopsis=QCoreApplication.translate(
                    'QBetseeSimmer',
                    'Simulation halted prematurely '
                    'due to computational instability.'),
            ) from exception
        # Else, fallback to raising a human-readable translated exception
        # synopsizing an unrecognized fatal error.
        #
        # Note that this case embeds an exegesis (i.e., detailed message) *NOT*
        # embedded in the prior case and hence requires unique handling.
        else:
            raise BetseeSimmerBetseException(
                synopsis=QCoreApplication.translate(
                    'QBetseeSimmer',
                    'Simulation halted prematurely with unexpected error:'),
                exegesis=str(exception),
            ) from exception


    #FIXME: Probably insufficient as is, sadly. Consider improving as follows:
    #
    #* Toggle the play button such that the play icon is now visible. The
    #  optimal means of implementing this and the following item might be to:
    #  set the state of the simulator to stopped by calling the
    #  _set_phase_state(). Since that internally calls the
    #  _update_widgets() method, that might suffice. (It's been some time.)
    #  * Actually, doesn't setting the "_worker_phase_state" property to
    #    "HALTED" already satisfy this here?
    #* Disable the stop button.
    #* Probably ensure that the worker queue is empty.
    @Slot(bool)
    def _handle_worker_completion(self, is_success: bool) -> None:
        '''
        Handle the completion of the most recently working simulator worker.

        Specifically, this method:

        * Sets the state of the corresponding simulator phase to stopped.
        * Pops this worker from the :attr:`_workers_cls`.
        * If this queue is non-empty, starts the next enqueued worker.

        Caveats
        ----------
        While this worker is guaranteed to have completed its worker at the
        time of this slot call, the parent thread pool of this worker is *not*
        guaranteed to have already deleted this worker and hence disconnected
        all signal-slot connections connected to this worker. In edge cases,
        this may result in two workers being concurrently instantiated and
        connected to -- one of which is guaranteed to be completed and hence no
        longer emitting signals and the other of which is starting and hence
        starting to emit signals.

        This is somewhat non-ideal. This method calls the
        :meth:`_start_worker_next_or_noop` method, which internally
        instantiates a new worker and connects pertinent worker signals and
        slots. To avoid conflict with the exact same signals and slots
        connected to this recently deleted worker, we would ideally maintain
        the contractual guarantee that at most one worker be instantiated and
        connected to at any given time.

        Sadly, doing so is infeasible. Workers are :attr:`QRunnable` rather
        than :attr:`QObject` instances; since only the latter provide the
        destroyed() signal, deciding exactly when any given worker is deleted
        is infeasible. Ergo, calling this method only *after* this worker's
        thread pool is guaranteed to have deleted this worker is infeasible.

        Nonetheless, note that this worker *is* typically deleted at the time
        of this call. The last logic performed by the
        :meth:`QBetseeThreadPoolWorker.run` method is to emit the
        :attr:`QBetseeThreadPoolWorkerSignals.finished` signal connected to the
        parent slot calling this method. Immediately after emitting that
        signal and returning, the parent thread pool of this worker is
        guaranteed to delete this worker. Ergo, exactly two workers are only
        ever instantiated and connected to for a negligible amount of time.
        '''

        # If no worker was working, raise an exception.
        self._die_unless_working()

        # Set this simulator and the previously working phase to halted
        # *BEFORE* nullifying all references to this worker.
        self._worker_phase_state = SimmerState.HALTED

        # Nullify all references to this worker for safety.
        self._worker = None
        self._worker_phase = None

        # Dequeue this worker (i.e., remove this worker's subclass from
        # the queue of worker subclasses to be instantiated and run).
        self._workers_cls.pop()

        # Start the next worker in the current queue of workers to be run
        # if any or reduce to a noop otherwise.
        self._start_worker_next_or_noop()
