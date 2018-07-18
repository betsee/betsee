#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

#FIXME: Wrest control over worker lifecycles from Qt. The current approach
#invites impossible-to-debug race conditions on worker destruction. To do so,
#refactor this submodule as follows:
#
#* Rename the low-level "_worker" reference to "_worker_ref".
#* Define a new high-level "_worker" property that:
#  * If "_worker_ref" is non-None, returns "_worker_ref".
#  * Else, raises a human-readable exception.
#  Note that, because of the GIL, the exception should *NEVER* be raised. Since
#  we're controlling worker lifecycles from Python now *AND* since Python is
#  inherently non-multi-threadable, we are now guaranteed of this worker
#  remaining alive for the duration of each slot call in this submodule. We
#  should probably explicitly note that this requires the GIL. Obviously, if we
#  ever move to a GIL-less interpreter (e.g., Super-Hyper-PyPy), then all
#  worker access would need to be explicitly locked behind a mutual exclusion
#  primitive. In any case, simple is the way to go for the moment.
#* Revise the "_worker_ref" docstring accordingly.
#* Globally change most references to "_worker_ref" to "_worker" instead.
#FIXME: After implementing the above, we'd might as well go the whole nine
#yards and also refactor our queue from a container of worker classes to a
#container of worker instances. Using classes appears to gain us nothing, while
#introducing a great deal of perverse complexity. (Which is bad.)

#FIXME: When the user attempts to run a dirty simulation (i.e., a simulation
#with unsaved changes), the GUI should prompt the user as to whether or not
#they would like to save those changes *BEFORE* running the simulation. In
#theory, we should be able to reuse existing "sim_conf" functionality to do so.

#FIXME: When the application closure signal is emitted (e.g., from the
#QApplication.aboutToQuit() signal and/or QMainWindow.closeEvent() handler),
#the following logic should be performed (in order):
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
from betse.util.type import enums
from betse.util.type.cls import classes
from betse.util.type.text import strs
from betse.util.type.types import type_check, WeakRefProxyTypes
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
    SIMMER_STATES_RUNNING,
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
    _worker : {WeakRefProxyTypes(QBetseeSimmerWorkerABC), NoneType}
        Weak reference to the current working simulator worker if any *or*
        ``None`` otherwise (i.e., if no worker is currently working), allowing
        this worker to be gracefully halted on application shutdown. Note that
        this worker's thread pool owns this worker and therefore fully manages
        this worker's lifecycle. Preserving a strong (i.e., standard) rather
        than weak reference to this worker would induce a subtle race condition
        between Qt's explicit deletion and Python's implicit garbage collection
        of this worker on completion. Note this reference may raise a
        :data:`ReferenceError` exception for the window of time immediately
        *after* this worker's completion and subsequent deletion by its thread
        pool but *before* the corresponding :meth:`_handle_worker_completion`
        slot handles this event.
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
    _action_toggle_work : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle_work`
        action.
    _action_stop_work : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_stop_work` action.
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
        self._action_toggle_work = None
        self._action_stop_work = None
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
        self._action_toggle_work     = main_window.action_sim_run_toggle_work
        self._action_stop_work     = main_window.action_sim_run_stop_work
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
        self._action_toggle_work.triggered.connect(self._toggle_work)
        self._action_stop_work.triggered.connect(self._stop_work)

        # For each possible phase...
        for phase in self._PHASES:
            # Connect this phase's signals to this object's equivalent slots.
            phase.set_state_signal.connect(self._set_phase_state)

            # Initialize the state of this phase *AFTER* connecting these
            # slots, thus implicitly initializing the state of this simulator.
            phase.update_state()

    # ..................{ PROPERTIES ~ bool                 }..................
    @property
    def is_queued(self) -> bool:

        # Return true only if one or more phases are queued.
        return any(phase.is_queued for phase in self._PHASES)


    @property
    def _is_workable(self) -> bool:
        '''
        ``True`` only if the simulator is **workable** (i.e., currently capable
        of performing work).

        Equivalently, this property evaluates to ``True`` only if the simulator
        is queued *or* working; in either case, the simulator is guaranteed to
        be safely startable, resumable, or pausable and hence workable.
        '''

        return self.is_queued or self._is_working


    @property
    def _is_working(self) -> bool:
        '''
        ``True`` only if some simulator worker is currently working.

        Equivalently, this method returns ``True`` only if this simulator is
        currently modelling or exporting some queued simulation phase.
        '''

        # Return true only if a simulator worker is currently working.
        return self._worker is not None

    # ..................{ PROPERTIES ~ bool : state         }..................
    @property
    def _is_running(self) -> bool:
        '''
        ``True`` only if the simulator is **running** (i.e., some simulator
        worker is currently modelling or exporting some queued simulation phase
        and hence is neither paused nor finished).
        '''

        # If no worker was working, raise an exception.
        self._die_unless_working()

        # Return true only if this worker is currently running.
        return self._worker_phase.state in SIMMER_STATES_RUNNING


    @property
    def _is_paused(self) -> bool:
        '''
        ``True`` only if the simulator is **paused** (i.e., some simulator
        worker is currently paused while previously modelling or exporting some
        queued simulation phase and hence is neither running nor finished).
        '''

        # If no worker was working, raise an exception.
        self._die_unless_working()

        # Return true only if this worker is currently paused.
        return self._worker_phase.state is SimmerState.PAUSED

    # ..................{ EXCEPTIONS                        }..................
    def _die_unless_workable(self) -> None:
        '''
        Raise an exception unless the simulator is **workable** (i.e.,
        currently capable of performing work).

        Raises
        ----------
        BetseeSimmerException
            If the simulator is unworkable.

        See Also
        ----------
        :meth:`_is_workable`
            Further details.
        '''

        if not self._is_workable:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer',
                'Simulator not workable (i.e., '
                'not currently working and no phases queued).'))

    # ..................{ EXCEPTIONS ~ state                }..................
    def _die_unless_running(self) -> None:
        '''
        Raise an exception unless the simulator is **running** (i.e., some
        simulator worker is currently modelling or exporting some queued
        simulation phase and hence is neither paused nor finished).

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* running, in which case the simulator is
            either paused or finished.

        See Also
        ----------
        :meth:`_is_running`
            Further details.
        '''

        if not self._is_running:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer',
                'Simulator not running (i.e., '
                'either paused, finished, or not started).'))


    def _die_unless_paused(self) -> None:
        '''
        Raise an exception unless the simulator is **paused** (i.e., some
        simulator worker is currently paused while previously modelling or
        exporting some queued simulation phase and hence is neither running nor
        finished).

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* paused, in which case the simulator is
            either running or finished.

        See Also
        ----------
        :meth:`_is_paused`
            Further details.
        '''

        if not self._is_paused:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer',
                'Simulator not paused (i.e., '
                'either running, finished, or not started).'))

    # ..................{ EXCEPTIONS ~ working              }..................
    def _die_if_working(self) -> None:
        '''
        Raise an exception if some simulator worker is currently working.

        Raises
        ----------
        BetseeSimmerException
            If some simulator worker is currently working.

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

        Raises
        ----------
        BetseeSimmerException
            If no simulator worker is currently working.

        See Also
        ----------
        :meth:`_is_working`
            Further details.
        '''

        if not self._is_working:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer', 'No simulation currently running.'))

    # ..................{ SLOTS ~ action : work             }..................
    # Slots connected to signals emitted by "QAction" objects specific to the
    # currently running simulator worker if any.

    #FIXME: Rewrite documentation to note the considerably changed behaviour.
    @Slot(bool)
    def _toggle_work(self, is_playing: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically pushing the :class:`QPushButton` widget corresponding
        to the :attr:`_action_toggle_work` variable.

        This slot runs the currently queued phase by either:

        * If this phase is currently paused, resuming this phase.
        * Else, starting this phase.

        Parameters
        ----------
        is_playing : bool
            ``True`` only if the corresponding :class:`QPushButton` widget is
            toggled, implying the user to have requested that the simulator be
            either started or resumed, contextually depending on the current
            state of the simulator; conversely, ``False`` implies a request
            that the simulator be paused.
        '''

        # If the simulator is unworkable, raise an exception.
        self._die_unless_workable()

        # If the user requested the simulator be started or unpaused...
        if is_playing:
            # If the simulator is currently working, some simulator worker was
            # previously working before being paused by a prior call to this
            # slot. In this case, resume this worker.
            if self._is_working:
                self._resume_work()
            # Else, the simulator is *NOT* currently working. In this case,
            # enqueue all currently queued simulation phases as simulator
            # workers and start the first such worker.
            else:
                self._start_work()
        # Else, the user requested the simulator be paused. Do so.
        else:
            self._pause_work()


    #FIXME: Implement us up, please.
    #FIXME: Docstring us up, please.
    def _start_work(self) -> None:

        # Log this attempt.
        logs.log_debug('Starting queued simulator phase(s)...')

        # If no simulator phase is currently queued, raise an exception.
        self._die_unless_queued()

        # Initialize the queue of simulator phases to be run.
        self._enqueue_worker_types()

        # Iteratively run each such phase.
        self._start_workers()

        #FIXME: Does _start_workers() already set this state?
        #FIXME: Set the state of both this simulator *AND* the currently
        #running phase *AFTER* successfully running this phase above.
        # self._worker_phase.state = SimmerState.MODELLING
        # self._worker_phase.state = SimmerState.EXPORTING


    def _pause_work(self) -> None:
        '''
        Pause the currently running simulator.

        This method temporarily pauses the current simulator worker in a
        thread-safe manner safely resumable at any time by calling the
        :meth:`_resume_work` method.

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* currently running.
        '''

        # Log this attempt.
        logs.log_debug('Pausing simulator phase...')

        # If the simulator is *not* currently running, raise an exception.
        self._die_unless_running()

        # Pause the currently running simulator worker.
        self._worker.pause()

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the paused() signal of this worker.

        # Set this simulator and the currently running phase to the paused
        # state *AFTER* successfully pausing this worker.
        self._worker_phase.state = SimmerState.PAUSED


    def _resume_work(self) -> None:
        '''
        Resume the currently paused simulator.

        This method resumes the current simulator worker in a thread-safe
        manner after having been previously paused by a call to the
        :meth:`_pause_work` method.

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* currently paused.
        '''

        # Log this attempt.
        logs.log_debug('Resuming simulator phase...')

        # If the simulator is *not* currently paused, raise an exception.
        self._die_unless_paused()

        # Resume the currently paused simulator worker.
        self._worker.resume()

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the resumed() signal of this worker.

        # Set this simulator and the currently running phase to the
        # worker-specific running state *AFTER* successfully resuming this
        # worker.
        self._worker_phase.state = self._worker.simmer_state

    # ..................{ SLOTS ~ action : stop             }..................
    @Slot()
    def _stop_work(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget associated
        with the :attr:`_action_stop_work` action.
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
            'Simulator phase "%s" state set to "%s"...',
            phase.name, enums.get_member_name_lowercase(phase.state))

        # New state to change this simulator to if any *OR* "None" otherwise.
        state_new = None

        # If the current state of either:
        #
        # * This phase is fixed (i.e., high-priority) and hence superceding the
        #   current state of this simulator...
        # * This simulator is fluid (i.e., low-priority) and hence superceded
        #   by the current state of this phase...
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
                    state_new = SimmerState.UNQUEUED
            # Else, this phase's new state unconditionally takes precedence.
            # Set this simulator's current state to this phase's new state.
            else:
                state_new = phase.state
        # Else, silently preserve this simulator's current state as is.

        # If changing the state of this simulator...
        if state_new is not None:
            # Log this change.
            logs.log_debug(
                'Simulator state set to "%s"...',
                enums.get_member_name_lowercase(state_new))

            # Change the state of this simulator to this new state.
            self.state = state_new

            # Update the state of simulator widgets *AFTER* setting this state.
            self._update_widgets()

    # ..................{ UPDATERS                          }..................
    def _update_widgets(self) -> None:

        # Enable (in arbitrary order):
        #
        # * All widgets controlling the currently queued phase only if one or
        #   more phases are currently queued.
        # * All widgets halting the current worker only if some worker is
        #   currently working.
        #
        # To reduce the likelihood of accidental interaction with widgets
        # intended to be disabled, do so *BEFORE* subsequent slot logic.
        self._player_toolbar.setEnabled(self.is_queued)

        # Enable simulator working only if the simulator is workable.
        self._action_toggle_work.setEnabled(self._is_workable)

        # Enable simulator stopping only if the simulator is currently working.
        self._action_stop_work.setEnabled(self._is_working)

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

        # If some simulator worker is currently working, raise an exception.
        self._die_if_working()

        # Create this simulator worker queue.
        self._workers_cls = guisimrunworkqueue.enqueue_worker_types(
            phases=self._PHASES)


    def _dequeue_workers(self) -> None:
        '''
        Revert the :attr:`_workers_cls` to ``None``, effectively dequeueing
        (i.e., popping) all previously queued simulator workers.
        '''

        # If no simulator worker is currently working, raise an exception.
        self._die_unless_working()

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
        self._loop_work()


    def _loop_work(self) -> None:
        '''
        Iteratively run the next enqueued simulator worker if any *or* cleanup
        after this iteration otherwise (i.e., if no workers remain to be run).

        This method perform the equivalent of the body of the abstract loop
        iteratively starting and running all enqueued simulator workers.
        Specifically, this method iteratively starts the next simulator worker
        (i.e., head item of the :attr:`_workers_cls`) enqueued by a prior call
        to the :meth:`_enqueue_worker_types` method if this queue is non-empty
        *or* garbage-collects this queue otherwise (i.e., if already empty).

        Design
        ----------
        Ideally, the body of this method would be the body of a simple loop
        over all enqueued simulator workers. Since the
        :meth:`_handle_worker_completion` slot calling this method is only
        iteratively signalled by Qt on the completion of each worker, however,
        "rolling" this method into a loop is effectively infeasible.

        Technically, refactoring this method into a continuation-based
        generator would probably suffice to "roll" this method into a loop.
        Doing so, however, would require the use of an asynchronous
        Python-based event loop *and* a heavyweight architectural redesign. In
        short, the current approach stands as the most reasonable.
        '''

        # If no workers remain to be run...
        if not self._workers_cls:
            # Log this completion.
            logs.log_debug(
                'Stopping simulator work from main thread "%d"...',
                guithread.get_current_thread_id())

            # Gracefully halt this iteration.
            self._dequeue_workers()
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
        self._worker = worker_type(
            conf_filename=self._sim_conf.p.conf_filename)

        # Finalize this worker's initialization.
        self._worker.init(progress_bar=self._player_progress)

        # Simulator phase acted upon by this worker.
        self._worker_phase = self._PHASE_KIND_TO_PHASE[worker_type.phase_kind]

        # Connect signals emitted by this worker to slots on this simulator.
        self._worker.signals.failed.connect(self._handle_worker_exception)
        self._worker.signals.finished.connect(self._handle_worker_completion)

        # Start this worker.
        guipoolthread.start_worker(self._worker)

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the started() signal of this worker. After all, this
        #should only be performed if this worker is indeed successfully started
        #within this thread -- which we have no way of guaranteeing here.

        # Set the state of both this simulator *AND* the currently
        # running phase *AFTER* successfully starting this worker.
        self._worker_phase.state = worker_type.simmer_state

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

    #FIXME: Revise the "Caveats" section of the docstring below, which (sadly,
    #given how decently it was written), no longer applies at all. Perhaps at
    #least some of this section can be shifted into the "Lifecycle" section of
    #the class docstring instead?
    #FIXME: Probably insufficient as is, sadly. Consider improving as follows:
    #
    #* Toggle the play button such that the play icon is now visible. The
    #  optimal means of implementing this and the following item might be to
    #  set the state of the simulator to stopped by calling the
    #  _set_phase_state(). Since that internally calls the
    #  _update_widgets() method, that might suffice. (It's been some time.)
    #  * Actually, doesn't setting the "_worker_phase.state" property to
    #    "HALTED" already satisfy this here?
    #* Disable the stop button. Actually, shouldn't this already be implicitly
    #  performed by a call to the _update_widgets() method?
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
        :meth:`_loop_work` method, which internally
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

        Technically, Python-based workarounds may exist. Workers are also
        instances of Python classes, whose optional **finalizer** (i.e.,
        special ``__del__()`` method) if any is called on object deletion.
        Likewise, the :func:`weakref.ref` function proxying the weak
        :attr:`_worker` reference accepts an optional ``callback`` parameter
        performing similar finalization. Unfortunately, both cases impose
        similar constraints on exception handling:

            Exceptions raised by the callback will be noted on the standard
            error output, but cannot be propagated; they are handled in exactly
            the same way as exceptions raised from an object’s ``__del__()``
            method.

        Exception propagation and logging is central to sane, deterministic
        application behaviour. Any small benefit gained from handling worker
        deletion via such a callback would certainly be dwarfed by the large
        detriment of being unable to properly handle exceptions.

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

        # Schedule this worker's signals for immediately deletion and hence
        # disconnection from all slots they're currently connected to.
        # Technically, doing so is unnecessary; the subsequent nullification of
        # the "_worker" owning these signals should implicitly signal the same
        # deletion; nonetheless, since doing so has no harmful side effects and
        # can only assist code sanity, we do so regardless.
        self._worker.signals.deleteLater()

        # Set this simulator and the previously working phase to halted
        # *BEFORE* nullifying all references to this worker.
        self._worker_phase.state = SimmerState.HALTED

        # Nullify all references to this worker for safety. Note that this
        # worker is a "QRunnable" rather than "QObject" and hence provides no
        # deleteLater() method. (Nullifying this worker is the best we can do.)
        self._worker_phase = None
        self._worker = None

        # Dequeue this worker (i.e., remove this worker's subclass from
        # the queue of worker subclasses to be instantiated and run).
        self._workers_cls.pop()

        # Start the next worker in the current queue of workers to be run
        # if any or reduce to a noop otherwise.
        self._loop_work()
