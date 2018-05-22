#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

#FIXME: When the user attempts to run a dirty simulation (i.e., a simulation
#with unsaved changes), the GUI should prompt the user as to whether or not they
#would like to save those changes *BEFORE* running the simulation. In theory, we
#should be able to reuse existing "sim_conf" functionality to do so.

#FIXME: When the application closure signal is emmited (e.g., from the
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
#   guithreadpool.is_worker() tester), these threads should be terminated as
#   gracefully as feasible.
#
#Note the QThreadPool.waitForDone(), which may assist us. If we do call that
#function, we'll absolutely need to pass a reasonable timeout; if this timeout
#is hit, the thread pool will need to be forcefully terminated. *shrug*

#FIXME: *O.K.* Ultimately, the long-term solution will be to leverage the
#standard "multiprocessing" package in concert with the third-party "dill"
#package to isolate a BETSE simulator subcommand to be run to a separate
#process. Why? The GIL. That said, a great deal of the work required to
#facilate multiprocess-style communication between BETSE and BETSEE is the exact
#same work required to facilitate multithreading-style communication between
#BETSE and BETSEE. Ergo, we do the latter first; then we switch to the former.
#It's non-ideal, of course, but everything on hand is non-ideal. This is the
#best we have on hand.
#
#Note that the "multiprocessing" module has different means of facilitating
#interprocess communication. The two most prominent are the event-based API
#defined by "multiprocessing.Event" and the "pickle" and/or "dill"-based API
#defined by... something. Further research is clearly required here.
#
#Note also that I examined numerous alternatives. The "concurrent.futures"
#submodule is particularly inapplicable, as it leverages the prototypical
#cloud-based map + reduce paradigm. Completely useless for our purposes, sadly.
#
#That said, there may yet be a better way than "multiprocessing" + "dill" -- but
#we have to yet to discover it. If such an improved solution does exist, it will
#almost certainly be a third-party alternative to "multiprocessing". Our
#suspicion is that we almost certainly want to adopt the "multiprocessing" +
#"dill" solution as a first-draft solution for all of the obvious reasons:
#"multiprocessing" is standard and we already require and love "dill", so no
#additional dependencies are required. That's incredibly nice, really.

#FIXME: Refactor to leverage threading via the new "work" subpackage as follows:
#
#* Preserve most existing attributes and properties of this class. That said...
#* Remove the three methods in the "QUEUERS" subsection from *ALL* submodules,
#  possibly excluding the _start_worker_queued_next() method -- which we might want to
#  preserve *ONLY* in this submodule. Even then, that method should still be
#  removed from all other submodules.
#* Refactor the "_worker_queue" variable from a deque of phases to a deque of
#  simulator workers produced by the "work.guisimrunworkqueue" submodule.
#* In the __init__() method:
#  * Define a new "_PHASE_KIND_TO_PHASE" dictionary mapping from phase types to
#    simulator phases: e.g.,
#
#      # Rename the "self._phases" sequence to "self._PHASES" as well, please.
#      self._PHASE_KIND_TO_PHASE = {
#          SimPhaseKind.SEED: self._phase_seed, ...
#      }
#
#* Refactor the critical _phase_working() property to:
#  * Get the "kind" property of the leading worker in "_worker_queue".
#  * Map this property to the corresponding phase via "_PHASE_KIND_TO_PHASE".
#* Refactor the _start_worker_queued_next() method as follows:
#  * For the first worker in "_worker_queue":
#    * Emit a signal connected to the start() slot of that worker. (Probably
#      just a signal of that same worker named "start_signal", for brevity.)
#  * ...that's it. Crazy, eh?
#* Define a new private _handle_worker_finished() slot of this simulator. This
#  slot should receive a "QBetseeSimmerWorkerABC" instance as follows:
#  * Validate that the leading item of "_worker_queue" is the passed worker.
#  * Pop this worker from "_worker_queue".
#  * If "_worker_queue" is non-empty, then:
#    * Call the _start_worker_queued_next() method.
#* In the _init_connections() method:
#  * Iterate over each possible worker (e.g., "_worker_seed"). This may merit a
#    new "_WORKERS" sequence or possibly even "_PHASE_KIND_TO_WORKER" map.
#  * For each possible worker:
#    * Connect the finished() signal emitted by that worker to
#      _handle_worker_finished() slot.
#
#Severely non-trivial, but awesome nonetheless.
#
#I'm all out of bubblegum. Let's do this.

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

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Slot  #, Signal
from betse.exceptions import BetseSimUnstableException
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.text import strs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import (
    BetseeSimmerException, BetseeSimmerBetseException)
# from betsee.guimetadata import SCRIPT_BASENAME
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhase
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState,
    SIMMER_STATE_TO_STATUS_VERBOSE,
    SIMMER_STATES_FIXED,
    SIMMER_STATES_FLUID,
    # MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS,
    # EXPORTING_TYPE_TO_STATUS_DETAILS,
)
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.util.thread import guithread
from betsee.util.thread.pool import guipoolthread
from betsee.gui.simtab.run.work.guisimrunwork import (
    QBetseeSimmerWorkerSeed,
)
from collections import deque

# ....................{ CLASSES                            }....................
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
    _worker_queue : deque
        Queue of each **simulator phase** (i.e., :class:`QBetseeSimmerPhase`
        instance) that is either currently running or scheduled to be run if any
        *or* ``None`` otherwise (i.e., if no phase is running). If this queue is
        *not* ``None``, this queue is guaranteed to be non-empty such that:
        * The first item of this queue is the currently running phase.
        * All subsequent items if any are the phases scheduled to be run *after*
          the first item completes (in order).
        While this container is technically a double-ended queue (i.e., deque),
        Python provides *no* corresponding single-ended queue. Since the former
        generalizes the latter, utilizing the former in a single-ended manner
        suffices to replicate the behaviour of the latter. Ergo, a deque remains
        the most space- *and* time-efficient data structure for doing so.

    Attributes (Private: Phase)
    ----------
    _phases : SequenceTypes
        Immutable sequence of all simulator phase controllers (e.g.,
        :attr:`_phase_seed`), needed for iteration over these controllers. For
        sanity, these phases are ordered is simulation order such that:
        * The seed phase is listed *before* the initialization phase.
        * The initialization phase is listed *before* the simulation phase.
    _phase_seed : QBetseeSimmerPhase
        Controller for all simulator widgets pertaining to the seed phase.
    _phase_init : QBetseeSimmerPhase
        Controller for all simulator widgets pertaining to the initialization
        phase.
    _phase_sim : QBetseeSimmerPhase
        Controller for all simulator widgets pertaining to the simulation phase.

    Attributes (Private: Thread)
    ----------
    _thread : QBetseeWorkerThread
        Thread controller owning all simulator workers (i.e.,
        :class:`QBetseeSimmerWorkerABC` instances responsible for running queued
        simulation subcommands in a multithreaded manner).
    _workers : frozenset
        Immutable set of all simulator workers (e.g., :attr:`_worker_seed`),
        needed for iteration over these workers.
    _worker_seed : QBetseeSimmerWorkerSeed
        Simulator worker running the seed phase for this simulation.

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
        frame containing only the :class:`QToolBar` controlling this simulation.
    _status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_status` label,
        synopsizing the current state of this simulator.
    '''

    # ..................{ INITIALIZERS                       }..................
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
        self._player_progress = None
        self._player_toolbar = None
        self._worker_queue = None
        self._status = None

        # Initialize all phases of this simulator.
        self._init_phases()


    def _init_phases(self) -> None:
        '''
        Initialize all phases of this simulator.
        '''

        # Simulator phase controllers.
        self._phase_seed = QBetseeSimmerPhase(self)
        self._phase_init = QBetseeSimmerPhase(self)
        self._phase_sim  = QBetseeSimmerPhase(self)

        #FIXME: Non-ideal artifact of obsolete design. Refactor as follows:
        #
        #* Require a "phase_kind" parameter to be passed into the
        #  QBetseeSimmerPhase.init() method.
        #* Remove the "QBetseeSimmerPhase.kind" property.

        # Set the type of such phase. Since the QObject.__init__() method cannot
        # be redefined to accept subclass-specific parameters, these types
        # *MUST* be subsequently set as follows.
        self._phase_seed.kind = SimPhaseKind.SEED
        self._phase_init.kind = SimPhaseKind.INIT
        self._phase_sim .kind = SimPhaseKind.SIM

        # Sequence of all simulator phases. For sanity (e.g., during iteration),
        # these phases are intentionally listed in simulation order.
        self._phases = (self._phase_seed, self._phase_init, self._phase_sim)


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
        references to this main window on returning. References to child widgets
        (e.g., actions) of this window may be retained, however.

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
            Initialized application-specific parent :class:`QMainWindow` widget.
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
        self._sim_conf = main_window.sim_conf

        # Initialize all phases (in arbitrary order).
        for phase in self._phases:
            phase.init(main_window)

        #FIXME: Excise the following code block after hooking this high-level
        #simulator GUI into the low-level "simrunner" submodule.

        # Avoid displaying detailed status for the currently queued subcommand,
        # as the low-level BETSE codebase lacks sufficient hooks to update this
        # status in a sane manner.
        main_window.sim_run_player_substatus_group.hide()

        #FIXME: Re-enable after implementing queueing properly.
        main_window.sim_run_queue_group.setEnabled(False)


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
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Connect each such action to this object's corresponding slot.
        self._action_sim_run_start_or_resume.triggered.connect(
            self._start_or_resume_phase)
        self._action_pause.triggered.connect(self._pause_phase)
        self._action_stop.triggered.connect(self._stop_phase)

        # For each possible phase...
        for phase in self._phases:
            # Connect this phase's signals to this object's corresponding slots.
            phase.set_state_signal.connect(self._set_phase_state)

            # Initialize the state of this phase *AFTER* connecting these slots,
            # implicitly initializing the state of this simulator.
            phase.update_state()

    # ..................{ PROPERTIES ~ bool : public         }..................
    @property
    def is_queued(self) -> bool:
        '''
        ``True`` only if one or more simulator phases are currently queued for
        modelling and/or exporting.
        '''

        # Return true only if one or more phases are queued.
        return any(phase.is_queued for phase in self._phases)

    # ..................{ PROPERTIES ~ bool : private        }..................
    @property
    def _is_working(self) -> bool:
        '''
        ``True`` only if some queued simulator phase is currently **running**
        (i.e., either being modelled or exported by this simulator).
        '''

        # Return true only if a non-empty queue of all phases to be run
        # currently exists. The lifecycle of this queue is managed in a just in
        # time (JIT) manner corresponding exactly to whether or not the
        # simulator is running. Specifically:
        #
        # * This queue defaults to "None".
        # * The _start_or_resume_phase() slot instantiates this queue on first running
        #   a new queue of simulator phases.
        # * The _stop_phase() slot reverts this queue back to "None".
        #
        # For efficiency, return this queue reduced to a boolean -- equivalent
        # to this less efficient (but more readable) pair of tests:
        #
        #    return self._worker_queue is not None and len(self._worker_queue)
        return bool(self._worker_queue)

    # ..................{ PROPERTIES ~ phase                 }..................
    @property
    def _phase_working(self) -> QBetseeSimmerPhase:
        '''
        Queued simulator phase that is currently **running** (i.e., either being
        modelled or exported by this simulator) if any *or* raise an exception
        otherwise.

        Equivalently, this phase is the first item of the underlying queue of
        all simulator phases to be run.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`_is_working` property
        is ``True``).

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
              :attr:`_worker_queue` is either ``None`` or empty).
        '''

        # If *NO* simulator phase is currently running, raise an exception.
        self._die_unless_working()

        # Return true only if one or more phases are queued.
        return self._worker_queue[0]

    # ..................{ PROPERTIES ~ phase : state         }..................
    # This trivial property getter exists only so that the corresponding
    # non-trivial property setter may be defined.
    @property
    def _phase_working_state(self) -> SimmerState:
        '''
        State of the queued simulator phase that is currently **running** (i.e.,
        either being modelled or exported by this simulator) if any *or* raise
        an exception otherwise.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`_is_working` property
        is ``True``).

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
              :attr:`_worker_queue` is either ``None`` or empty).

        See Also
        ----------
        :meth:`_phase_working`
            Further details.
        '''

        return self._phase_working.state


    @_phase_working_state.setter
    @type_check
    def _phase_working_state(self, state: SimmerState) -> None:
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
              :attr:`_worker_queue` is either ``None`` or empty).

        See Also
        ----------
        :meth:`_phase_working_state`
            Further details.
        '''

        #FIXME: This may now induce infinite recursion. *sigh*

        # Set the state of the currently running phase to this state.
        self._phase_working.state = state

        # Set the state of this simulator to the same state.
        # self.state = state

    # ..................{ EXCEPTIONS                         }..................
    def _die_if_working(self) -> None:
        '''
        Raise an exception if some queued simulator phase is currently
        **running** (i.e., either being modelled or exported by this simulator).

        See Also
        ----------
        :meth:`_is_working`
            Further details.
        '''

        if self._is_working:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer', 'Simulator currently running.'))


    def _die_unless_working(self) -> None:
        '''
        Raise an exception unless some queued simulator phase is currently
        **running** (i.e., either being modelled or exported by this simulator).

        Equivalently, this method raises an exception if *no* queued simulator
        phase is currently running.

        See Also
        ----------
        :meth:`_is_working`
            Further details.
        '''

        if not self._is_working:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer', 'Simulator currently running.'))

    # ..................{ SLOTS ~ action : simulator         }..................
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
        # If some simulator phase was previously running before being
        # paused, resume this phase.
        if self._is_working:
            pass
        # Else, no simulator phase was previously running. In this case,
        # start the first queued phase.
        else:
            # Initialize the queue of simulator phases to be run.
            self.enqueue_running()

            # Iteratively run each such phase.
            self.run_enqueued()

        #FIXME: Set the state of both this simulator *AND* the currently
        #running phase *AFTER* successfully running this phase above.
        # self._phase_working_state = SimmerState.MODELLING
        # self._phase_working_state = SimmerState.EXPORTING


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
        self._phase_working_state = SimmerState.PAUSED


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
        self.dequeue_running()

    # ..................{ SLOTS ~ action : queue             }..................
    # Slots connected to signals emitted by "QAction" objects specific to the
    # queue of simulator phases to be run.

    @Slot(QObject)
    def _set_phase_state(self, phase: QBetseeSimmerPhase) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically setting the current state of any simulator phase.

        Parameters
        ----------
        phase : QBetseeSimmerPhase
            Simulator phase whose current state has been set.
        '''

        # Log this slot.
        logs.log_debug(
            'Simulator phase "%s" state updated to "%s"...',
            phase.name,
            enums.get_member_name_lowercase(phase.state))

        # If the current state of either:
        #
        # * This phase is fixed (i.e., high-priority) and hence superceding the
        #   current state of this simulator...
        # * This simulator is fluid (i.e., low-priority) and hence superceded by
        #   current state of this phase...
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
            # Else, this phase's new state unconditionally takes precedence. Set
            # the current state of this simulator to this phase's new state.
            else:
                self.state = phase.state

            # Update the state of simulator widgets *AFTER* setting this state.
            self._update_widgets()

    # ..................{ UPDATERS                           }..................
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

        #FIXME: Uncomment this line and comment the following after implementing
        #the _stop_phase() method.
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

        #FIXME: Actually set this text to the prior word (e.g., "seed",
        #"initialization"). We'll probably need to get our queue up and running.

        # Text signifying the type of currently running simulator phase if any
        # *OR* an arbitrary placeholder otherwise. In the latter case, this
        # text is guaranteed to *NOT* be interpolated into this template and is
        # thus safely ignorable.
        phase_type = 'Hunters sustained by the dream gain strength from blood echoes.'

        # Text synopsizing the prior state of this simulator. To permit this
        # text to be interpolated into the middle of arbitrary sentences, the
        # first character of this text is lowercased.
        status_prior_text = strs.lowercase_char_first(self._status.text())

        # Unconditionally format this text with *ALL* possible format specifiers
        # interpolated into *ALL* possible instances of this text. By design,
        # format specifiers *NOT* interpolated into this text will be ignored.
        status_text = status_text_template.format(
            phase_type=phase_type,
            status_prior=status_prior_text,
        )

        # Set the text of the label displaying this synopsis to this text.
        self._status.setText(status_text)

    # ..................{ SLOTS ~ worker                     }..................
    # Slots connected to signals emitted by "QRunnable" workers.

    @Slot(Exception)
    def _handle_worker_exception(self, exception: Exception) -> None:
        '''
        Slot signalled on the currently running simulator worker erroneously
        raising an unexpected exception.

        This slot trivially handles this exception by re-raising this exception.
        Since the only means of explicitly re-raising an exception exposed by
        Python 3.x is to encapsulate that exception inside another exception,
        this slot unconditionally raises a :class:`BetseeSimmerBetseException`
        exception encapsulating the passed exception.

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
        # translated exception synopsizing this fact. This error is sufficiently
        # common to warrant a special case improving the user experience (UX).
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


    #FIXME: Awful slot name and implementation, obviously. Refactor as follows:
    #* Rename to _handle_worker_completion().
    #* Rewrite to at least:
    #  * Toggle the play button such that the play icon is now visible. The
    #    optimal means of implementing this and the following item might be to:
    #    set the state of the simulator to stopped by calling the
    #    _set_phase_state(). Since that internally calls the
    #    _update_widgets() method, that might suffice. (It's been some time.)
    #  * Disable the stop button.
    #  * Probably ensure that the worker queue is empty.
    #Improving this slot should probably be our highest priority.
    @Slot(bool)
    def _handle_worker_completion(self, is_success: bool) -> None:

        # Set this simulator and the previously running phase to the halted
        # state *AFTER* successfully halting this phase.
        self._phase_working_state = SimmerState.HALTED

    # ..................{ QUEUERS                            }..................
    def enqueue_running(self) -> None:
        '''
        Define the :attr:`_worker_queue` queue of all simulator phases to be
        subsequently run.

        This method enqueues (i.e., pushes onto this queue) all simulator phases
        for which the end user interactively checked at least one of the
        corresponding modelling and exporting checkboxes. For sanity, phases are
        enqueued in simulation order such that:

        * The seed phase is enqueued *before* the initialization phase.
        * The initialization phase is enqueued *before* the simulation phase.

        Raises
        ----------
        BetseeSimmerException
            If either:
            * No simulator phase is currently queued.
            * Some simulator phase is currently running (i.e.,
              :attr:`_worker_queue` is already defined to be non-``None``).
        '''

        # Enqueue our superclass.
        super().enqueue_running()

        # If some simulator phase is currently running, raise an exception.
        self._die_if_working()

        # Initialize this queue to the empty double-ended queue (i.e., deque).
        self._worker_queue = deque()

        # For each possible phase...
        for phase in self._phases:
            # If this phase is currently queued for modelling or exporting...
            if phase.is_queued:
                # Record which actions this phase was queued for.
                phase.enqueue_running()

                # Enqueue this phase.
                self._worker_queue.append(phase)


    def dequeue_running(self) -> None:
        '''
        Revert the :attr:`_worker_queue` queue to ``None``, effectively
        dequeueing (i.e., popping from this queue) all previously queued
        simulator phases.
        '''

        # Dequeue our superclass.
        super().dequeue_running()

        # Uninitialize this queue.
        self._worker_queue = None

        # For each possible phase, forget which actions this phase was queued
        # for (if any). While technically optional, doing so should preserve
        # sanity by assisting in debugging.
        for phase in self._phases:
            phase.dequeue_running()


    def run_enqueued(self) -> None:
        '''
        Iteratively run each simulator phase enqueued (i.e., appended to the
        :attr:`_worker_queue` queue of such phases) by a prior call to the
        :meth:`enqueue_running` method.
        '''

        #FIXME: Refactor the following to leverage the "_worker_queue" deque.
        #See the "FIXME" above for exhaustive details.

        # Simulation runner run by all simulator workers.
        # from betse.science.simrunner import SimRunner
        # sim_runner = SimRunner(conf_filename=self._sim_conf.filename)

        #FIXME: Revive this, please.
        # # While one or more enqueued phases have yet to be run...
        # while self._is_working:
        #     # Enqueued simulator phase to be run.
        #     phase_queued = self._phase_working
        #
        #     # Run all actions previously enqueued for this phase (e.g.,
        #     # modelling, exporting).
        #     phase_queued.run_enqueued()
        #
        #     # Dequeue this phase *AFTER* successfully running these actions.
        #     self._worker_queue.pop()

        logs.log_debug(
            'Spawning simulator worker thread from main thread "%d"...',
            guithread.get_current_thread_id())

        # Simulator worker simulating one or more simulation phases of the
        # currently loaded simulation defined by this configuration file.
        worker = QBetseeSimmerWorkerSeed(
            conf_filename=self._sim_conf.p.conf_filename)

        # Connect signals emitted by this worker to slots on this simulator.
        worker.signals.failed.connect(self._handle_worker_exception)
        worker.signals.finished.connect(self._handle_worker_completion)

        # Connect progress signals emitted by this worker to slots on this
        # simulator's progress bar.
        worker.signals.progress_ranged.connect(self._player_progress.setRange)
        worker.signals.progressed.connect(self._player_progress.setValue)

        # Run this worker and thus this simulation phase.
        guipoolthread.run_worker(worker)
