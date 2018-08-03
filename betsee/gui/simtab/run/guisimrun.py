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
#progress bars. Nonetheless, this *DOES* appear to be circumventable by
#manually overlaying a "QLabel" widget over the "QProgressBar" widget in
#question. For details, see the following StackOverflow answer (which, now that
#I peer closely at it, appears to be quite incorrect... but, something's better
#than nothing... maybe):
#    https://stackoverflow.com/a/28816650/2809027

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, QObject, Slot  #, Signal
from betse.exceptions import BetseSimUnstableException
# from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.py import pythread
from betse.util.type import enums
from betse.util.type.obj import objects
from betse.util.type.text import strs
from betse.util.type.types import type_check
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
from betsee.gui.simtab.run.work.guisimrunwork import QBetseeSimmerPhaseWorker
from betsee.gui.simtab.run.work.guisimrunworkenum import SimmerPhaseSubkind
from betsee.util.thread import guithread
from betsee.util.thread.pool import guipoolthread
from collections import deque

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

    Caveats
    ----------
    For simplicity, this simulator internally assumes the active Python
    interpreter to prohibit Python-based multithreading via a Global
    Interpreter Lock (GIL). Specifically, all worker-centric attributes (e.g.,
    :attr:`_worker`, :attr:`_workers_queued`) are assumed to be implicitly
    synchronized despite access to these attributes *not* being explicitly
    locked behind a Qt-based mutual exclusion primitive.

    GIL-less Python interpreters violate this simplistic assumption. For
    example, the :meth:`_stop_worker` and
    :meth:`_handle_worker_completion` slots suffer a variety of obvious (albeit
    unlikely) race conditions under these interpreters centered around their
    attempts to competitively delete the same underlying worker in a
    desynchronized and hence non-deterministic manner... Woops.

    Yes, this is assuredly a bad idea. Yes, this is us nonchalantly shrugging.

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
    _workers_queued : {QueueType, NoneType}
        **Simulator worker queue** (i.e., double-ended queue of all simulator
        workers to be subsequently run in a multithreaded manner by this
        simulator, where each worker runs a simulation subcommand whose
        corresponding checkbox was checked at the time this queue was
        instantiated) if this simulator has started one or more such workers
        *or* ``None`` otherwise (i.e., if no such workers have been started).
        Note that this queue is double- rather than single-ended only as the
        Python stdlib fails to provide the latter. Since the former generalizes
        the latter, however, leveraging the former in a single-ended manner
        replicates the behaviour of the latter. Ergo, a double-ended queue
        remains the most space- and time-efficient data structure for doing so.

    Attributes (Private: Widgets)
    ----------
    _action_toggle_work : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle_work`
        action.
    _action_stop_worker : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_stop_worker` action.
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

        #FIXME: Yeah... Fix this, please. PyPy will probably make the GIL
        #optionally go away at some point. (At least, it certainly should.)

        # Raise an exception unless the active Python interpreter has a GIL, as
        # foolishly required by methods defined by this class.
        pythread.die_unless_gil()

        # Nullify all remaining instance variables for safety.
        self._action_toggle_work = None
        self._action_stop_worker = None
        self._player_progress = None
        self._player_toolbar = None
        self._workers_queued = None
        self._status = None

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
        self._action_toggle_work = main_window.action_sim_run_toggle_work
        self._action_stop_worker = main_window.action_sim_run_stop_work
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

        #FIXME: Excise the following code block after defining and implementing
        #hooks to update this status in a sane manner.

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
        self._action_stop_worker.triggered.connect(self._stop_worker)

        # For each possible phase...
        for phase in self._PHASES:
            # Connect this phase's signals to this object's equivalent slots.
            phase.set_state_signal.connect(self._set_phase_state)

            # Inform this simulator of the initial state of this phase.
            self._set_phase_state(phase)

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
        ``True`` only if the simulator is **working** (i.e., some simulator
        worker is either running or paused from running some queued simulation
        phase and hence is *not* finished).
        '''

        # Return true only if a non-empty queue of all phases to be run
        # currently exists. The lifecycle of this queue is managed in a just in
        # time (JIT) manner corresponding exactly to whether or not the
        # simulator and hence a simulator worker is currently working.
        # Specifically:
        #
        # * This queue defaults to "None".
        # * The _toggle_work() slot instantiates this queue on first
        #   running a new queue of simulator phases.
        # * The _stop_worker() slot reverts this queue back to "None".
        #
        # For efficiency, return this queue reduced to a boolean -- equivalent
        # to this less efficient (but more readable) pair of tests:
        #
        #    return self._workers_cls is not None and len(self._workers_cls)
        return bool(self._workers_queued)

    # ..................{ PROPERTIES ~ bool : state         }..................
    @property
    def _is_running(self) -> bool:
        '''
        ``True`` only if the simulator is **running** (i.e., some simulator
        worker is currently modelling or exporting some queued simulation phase
        and hence is neither paused nor finished).
        '''

        # Return true only if...
        return (
            # Some worker is currently working.
            self._is_working and
            # This worker is currently running.
            self._worker.phase.state in SIMMER_STATES_RUNNING)


    @property
    def _is_paused(self) -> bool:
        '''
        ``True`` only if the simulator is **paused** (i.e., some simulator
        worker is currently paused while previously modelling or exporting some
        queued simulation phase and hence is neither running nor finished).
        '''

        # Return true only if...
        return (
            # Some worker is currently working.
            self._is_working and
            # This worker is currently paused.
            self._worker.phase.state is SimmerState.PAUSED)

    # ..................{ PROPERTIES ~ worker               }..................
    @property
    def _worker(self) -> QBetseeSimmerPhaseWorker:
        '''
        **Currently working worker** (i.e., :class:`QRunnable` instance
        currently modelling or exporting a previously queued simulation phase
        in another thread) if any *or* raise an exception otherwise (i.e., if
        no workers are currently working).

        Raises
        ----------
        BetseeSimmerException
            If no worker is currently working.
        '''

        # If no worker is working, raise an exception.
        self._die_unless_working()

        # Return the head worker of the worker queue.
        return self._workers_queued[0]

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
                'QBetseeSimmer', 'Simulation currently working.'))


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
                'QBetseeSimmer', 'No simulation currently working.'))

    # ..................{ SLOTS ~ action : phase            }..................
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


    def _update_widgets(self) -> None:
        '''
        Update the contents of widgets owned or controlled by this simulator to
        reflect the current state of this simulator.
        '''

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
        self._action_stop_worker.setEnabled(self._is_working)

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
            SIM_PHASE_KIND_TO_NAME[self._worker.phase.kind]
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
                self._resume_worker()
            # Else, the simulator is *NOT* currently working. In this case,
            # enqueue all currently queued simulation phases as simulator
            # workers and start the first such worker.
            else:
                self._start_workers()
        # Else, the user requested the simulator be paused. Do so.
        else:
            self._pause_worker()


    def _start_workers(self) -> None:
        '''
        Enqueue one simulator worker for each simulation subcommand whose
        corresponding checkbox in a simulator phase is currently checked *and*
        iteratively start each such worker in a thread-safe manner.

        Raises
        ----------
        BetseeSimmerException
            If either:

            * No simulator phase is currently queued (i.e., no such checkboxes
              are currently checked).
            * One or more workers are already working.
        '''

        # Log this action.
        logs.log_debug(
            'Starting simulator work by user request from main thread "%d"...',
            guithread.get_current_thread_id())

        # If no simulator phase is currently queued, raise an exception.
        self._die_unless_queued()

        # If one or more workers are already working, raise an exception.
        guipoolthread.die_if_working()

        # Initialize the queue of simulator phases to be run.
        self._enqueue_workers()

        # Initiate iteration by starting the first enqueued worker and
        # connecting the stop signal emitted by that worker to a slot
        # iteratively repeating this process.
        self._loop_worker()


    def _pause_worker(self) -> None:
        '''
        Pause the currently running simulator.

        This method temporarily pauses the current simulator worker in a
        thread-safe manner safely resumable at any time by calling the
        :meth:`_resume_worker` method.

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* currently running.
        '''

        # Log this action.
        logs.log_debug(
            'Pausing simulator work by user request from main thread "%d"...',
            guithread.get_current_thread_id())

        # If the simulator is *not* currently running, raise an exception.
        self._die_unless_running()

        # Pause the currently running simulator worker.
        self._worker.pause()

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the paused() signal of this worker.

        # Set this simulator and the currently running phase to the paused
        # state *AFTER* successfully pausing this worker.
        self._worker.phase.state = SimmerState.PAUSED


    def _resume_worker(self) -> None:
        '''
        Resume the currently paused simulator.

        This method resumes the current simulator worker in a thread-safe
        manner after having been previously paused by a call to the
        :meth:`_pause_worker` method.

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* currently paused.
        '''

        # Log this action.
        logs.log_debug(
            'Resuming simulator work by user request from main thread "%d"...',
            guithread.get_current_thread_id())

        # If the simulator is *not* currently paused, raise an exception.
        self._die_unless_paused()

        # Resume the currently paused simulator worker.
        self._worker.resume()

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the resumed() signal of this worker.

        # Set this simulator and the currently running phase to the
        # worker-specific running state *AFTER* successfully resuming this
        # worker.
        self._worker.phase.state = self._worker.simmer_state

    # ..................{ SLOTS ~ action : stop             }..................
    #FIXME: Improve this slot to stop *ALL* workers (e.g., by calling
    #_dequeue_workers()).
    @Slot()
    def _stop_worker(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget associated
        with the :attr:`_action_stop_worker` action.
        '''

        # Log this slot.
        logs.log_debug(
            'Stopping simulator work by user request from main thread "%d"...',
            guithread.get_current_thread_id())

        # If no worker is currently working, raise an exception.
        self._die_unless_working()

        # Currently working simulator worker. For safety, this property is
        # localized *BEFORE* this worker's stop() pseudo-slot (which
        # internally dequeues this worker and hence implicitly modifies the
        # worker returned by the "_worker" property) is called.
        worker = self._worker

        # Stop this worker. Note that the _dequeue_workers() method need (and
        # indeed should) *NOT* be explicitly called here, as calling the stop()
        # method here implicitly signals the _handle_worker_completion() slot,
        # which internally calls the _dequeue_workers() method.
        worker.stop()

        #FIXME: For safety, relegate this to a new slot of the corresponding
        #phase connected to the stopped() signal of this worker.

        # Set this simulator and the currently running phase to the stopped
        # state *AFTER* successfully stopping this worker.
        worker.phase.state = SimmerState.STOPPED

    # ..................{ QUEUERS                           }..................
    def _enqueue_workers(self) -> None:
        '''
        Create the **simulator worker queue** (i.e., :attr:`_workers_queued`
        variable) as specified by the pair of checkboxes associated with each
        simulator phase.

        This method enqueues (i.e., pushes onto this queue) workers in
        simulation phase order, defined as the ordering of the members of the
        :class:`betse.science.phase.phaseenum.SimPhaseKind` enumeration.
        Callers may safely run the simulation phases performed by these workers
        merely by sequentially assigning each worker enqueued in this queue to
        a thread via the
        :func:`betsee.util.thread.pool.guipoolthread.start_worker` function.

        For example:

        #. The :class:`QBetseeSimmerSubcommandWorkerModelSeed` worker (if any)
           is guaranteed to be queued *before*...
        #. The :class:`QBetseeSimmerSubcommandWorkerModelInit` worker (if any)
           is guaranteed to be queued *before*...
        #. The :class:`QBetseeSimmerSubcommandWorkerModelSim` worker (if any).

        Raises
        ----------
        BetseeSimmerException
            If either:

            * No simulator phase is currently queued.
            * Some simulator phase is currently running (i.e.,
              :attr:`_workers_queued` is already defined to be non-``None``).
        '''

        # If this controller is *NOT* currently queued, raise an exception.
        self._die_unless_queued()

        # If some simulator worker is currently working, raise an exception.
        self._die_if_working()

        # Simulator worker queue to be classified *AFTER* creating and
        # enqueuing all workers.
        workers_queued = deque()

        # For each simulator phase...
        for phase in self._PHASES:
            # If this phase is currently queued for modelling...
            if phase.is_queued_modelling:
                # Simulator worker modelling this phase.
                worker = QBetseeSimmerPhaseWorker(
                    phase=phase, phase_subkind=SimmerPhaseSubkind.MODELLING)

                # Enqueue a new instance of this subclass.
                workers_queued.append(worker)

            # If this phase is currently queued for exporting...
            if phase.is_queued_exporting:
                # Simulator worker subclass exporting this phase.
                worker = QBetseeSimmerPhaseWorker(
                    phase=phase, phase_subkind=SimmerPhaseSubkind.EXPORTING)

                # Enqueue a new instance of this subclass.
                workers_queued.append(worker)

        # Classify this queue *AFTER* successfully creating and enqueuing all
        # workers, thus reducing the likelihood of desynchronization.
        self._workers_queued = workers_queued


    def _dequeue_workers(self) -> None:
        '''
        Revert the :attr:`_workers_queued` to ``None``, effectively dequeueing
        (i.e., popping) all previously queued simulator workers.
        '''

        # If no simulator worker is currently working, raise an exception.
        self._die_unless_working()

        # Clear this queue, implicitly scheduling all previously queued workers
        # for garbage collection *AND* disconnecting all external slots
        # previously connected to signals defined by these workers.
        self._workers_queued = None

    # ..................{ WORKERS ~ loop                    }..................
    def _loop_worker(self) -> None:
        '''
        Iteratively run the next enqueued simulator worker if any *or* cleanup
        after this iteration otherwise (i.e., if no workers remain to be run).

        This method perform the equivalent of the body of the abstract loop
        iteratively starting and running all enqueued simulator workers.
        Specifically, this method iteratively starts the next simulator worker
        (i.e., head item of the :attr:`_workers_queued`) enqueued by a prior call
        to the :meth:`_enqueue_workers` method if this queue is non-empty
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
        if not self._is_working:
            # Log this completion.
            logs.log_debug(
                'Finalizing simulator work from main thread "%d"...',
                guithread.get_current_thread_id())

            # Gracefully halt this iteration.
            self._dequeue_workers()
        # Else, one or more workers remain to be run.

        # Next worker to be run.
        worker = self._workers_queued[0]

        # Log this work attempt.
        logs.log_debug(
            'Spawning simulator worker "%s" from main thread "%d"...',
            objects.get_class_name(worker), guithread.get_current_thread_id())

        # Finalize this worker's initialization.
        worker.init(
            conf_filename=self._sim_conf.p.conf_filename,
            progress_bar=self._player_progress,
        )

        # Connect signals emitted by this worker to simulator slots *AFTER*
        # initializing this worker, which these slots usually assume.
        worker.signals.failed.connect(self._handle_worker_exception)
        worker.signals.finished.connect(self._handle_worker_completion)

        # Start this worker *AFTER* establishing all signal-slot connections.
        guipoolthread.start_worker(worker)

        #FIXME: For safety, relegate this to a new slot of this object
        #connected to the started() signal of this worker. After all, this
        #should only be performed if this worker is indeed successfully started
        #within this thread -- which we have no way of guaranteeing here.

        # Set the state of both this simulator *AND* the currently
        # running phase *AFTER* successfully starting this worker.
        worker.phase.state = worker.simmer_state

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
    #  * Actually, doesn't setting the "self._worker.phase.state" property to
    #    "HALTED" already satisfy this here?
    #* Disable the stop button. Actually, shouldn't this already be implicitly
    #  performed by a call to the _update_widgets() method?
    #* Probably ensure that the worker queue is empty.
    @Slot(bool)
    def _handle_worker_completion(self, is_success: bool) -> None:
        '''
        Handle the completion of the most recently working simulator worker.

        Specifically, this method:

        * Sets the state of the corresponding simulator phase to finished.
        * Pops this worker from the :attr:`_workers_queued`.
        * If this queue is non-empty, starts the next enqueued worker.
        '''

        # If no worker is currently working, raise an exception.
        self._die_unless_working()

        # Currently working simulator worker. For safety, this property is
        # localized *BEFORE* this method dequeues this worker and hence
        # implicitly modifies the worker returned by the "_worker" property.
        worker = self._worker

        # Schedule this worker for immediate deletion. On doing so, all signals
        # owned by this worker will be disconnected from connected slots.
        #
        # Technically, doing so is unnecessary. The subsequent nullification of
        # the worker owning these signals already signals this deletion. As
        # doing so has no harmful side effects, however, do so regardless.
        worker.delete_later()

        # If this worker was *NOT* stopped by the user and hence finished
        # successfully, set the state of both this simulator *AND* the
        # previously running phase to finished *BEFORE* nullifying this phase.
        # This conditional ensures that the user-driven stopped state takes
        # precedence over the worker-driven finished state.
        if worker.phase.state is not SimmerState.STOPPED:
            worker.phase.state = SimmerState.FINISHED

        # Dequeue this worker (i.e., remove this worker's subclass from
        # the queue of worker subclasses to be instantiated and run).
        self._workers_queued.popleft()

        # Start the next worker in the current queue of workers to be run
        # if any or reduce to a noop otherwise.
        self._loop_worker()
