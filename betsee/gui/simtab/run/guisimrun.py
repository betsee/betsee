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
from PySide2.QtCore import QCoreApplication, QObject, Slot, Signal
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.text import strs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
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
from betsee.util.thread.pool import guipoolthread
# from betsee.gui.simtab.run.work.guisimrunworkcls import (
#     QBetseeSimmerWorkerSeed,
# )
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
    _action_toggle_playing : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle` action.
    _action_halt_playing : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_halt` action.
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
        self._action_toggle_playing = None
        self._action_halt_playing = None
        self._player_toolbar = None
        self._worker_queue = None
        self._status = None

        # Initialize all phases of this simulator.
        self._init_phases()

        # Initialize this simulator's thread and all workers of this thread.
        self._init_thread()


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


    #FIXME: Excise this method entirely, which is no longer needed.
    def _init_thread(self) -> None:
        '''
        Initialize this simulator's thread and all workers of this thread.
        '''

        #FIXME: Excise us up.
        #FIXME: Excise all documentation for these variables above.
        # # Simulator thread workers.
        # self._worker_seed = QBetseeSimmerWorkerSeed(self)
        #
        # # Immutable set of all simulator thread workers.
        # self._workers = frozenset({self._worker_seed,})

        #FIXME: This thread object probably needs to be parented. Consider
        #reverting the commented-out line, please.

        # Simulator thread controller.
        # self._thread = QBetseeWorkerThread(self)
        # self._thread = QBetseeWorkerThread()

        # Set the name of the OS-level process associated with this thread to
        # the same name of the OS-level process associated with the main thread
        # appended by a unique arbitrary suffix *BEFORE* starting this thread.
        # After this thread is started, setting this name reduces to a noop.
        # self._thread.process_name = SCRIPT_BASENAME + '_simmer'

        #FIXME: We *REALLY* need to do something resembling the following here:
        #
        #   gui_app.aboutToQuit.connect(self._thread.halt)
        #
        #Untested, of course. Why do this? Because Qt does *NOT* implicitly
        #attempt to gracefully halt running threads on application shutdown,
        #resulting in the following ugly error message on quitting BETSEE:
        #
        #    QThread: Destroyed while thread is still running
        #
        #Of course, the above signal connection would only be appropriate if
        #self._thread.halt():
        #
        #* Were a slot -- which it currently isn't. (Trivial, of course.)
        #* Iteratively signalled the stop() slots of all adopted workers. This
        #  in turns implies that the QBetseeWorkerThread class needs to:
        #  * Define a new "_workers_stop_signal" list of the "stop_signal"
        #    attributes of all adopted workers. Naturally, the
        #    the QBetseeWorkerThread.adopt_worker() method needs to append these
        #    attributes of the passed workers to this list.
        #  * Define a new unadopt_worker() method undoing everything done by
        #    the adopt_worker() method, including removing items from the
        #    "_workers_stop_signal" list corresponding to the passed workers.

        #FIXME: Excise us up.
        # Adopt these workers into this thread.
        # self._thread.adopt_worker(*self._workers)

        # Start this thread and hence this thread's event loop. This does *NOT*
        # start any workers adopted into this thread; this only permits slots
        # for these workers to begin receiving signals.
        # self._thread.start()

        # from PySide2.QtCore import QThreadPool
        # self.threadpool = QThreadPool()
        pass


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
        self._action_toggle_playing = main_window.action_sim_run_toggle
        self._action_halt_playing   = main_window.action_sim_run_halt
        self._player_toolbar = main_window.sim_run_player_toolbar_frame
        self._status = main_window.sim_run_player_status

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
        self._action_toggle_playing.toggled.connect(self._toggle_playing)
        self._action_halt_playing.triggered.connect(self._halt_playing)

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
        # * The _toggle_playing() slot instantiates this queue on first running
        #   a new queue of simulator phases.
        # * The _halt_playing() slot reverts this queue back to "None".
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
        self._die_unless_running()

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

    # ..................{ EXCEPTIONS ~ running               }..................
    def _die_if_running(self) -> None:
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


    def _die_unless_running(self) -> None:
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

    # ..................{ SLOTS ~ private : action           }..................
    # Slots connected to signals emitted by "QAction" objects.

    @Slot(bool)
    def _toggle_playing(self, is_playing: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling the checkable :class:`QPushButton` widget
        corresponding to the :attr:`_action_toggle_playing` variable.

        Specifically, if:

        * This button is checked, this slot runs the currently queued phase
          by either:
          * If this phase was paused, resuming this phase.
          * Else, starting this phase.
        * This button is unchecked, this slot pauses this phase.

        Parameters
        ----------
        is_playing : bool
            ``True`` only if this :class:`QPushButton` is currently checked, in
            which case this slot plays (i.e., either starts or resumes) this
            phase.
        '''

        # If now running the currently queued phase...
        if is_playing:
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
        # Else, pause this subcommand.
        else:
            #FIXME: Actually pause the currently running phase here.

            # Set this simulator and the previously running phase to the paused
            # state *AFTER* successfully pausing this phase.
            self._phase_working_state = SimmerState.PAUSED

        logs.log_debug('Returning from _toggle_playing...')


    @Slot()
    def _halt_playing(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget
        corresponding to the :attr:`_action_halt_playing` variable.
        '''

        # If *NO* simulator phase is currently running, raise an exception.
        self._die_unless_running()

        #FIXME: Actually halt the running subcommand here, please.

        # Uninitialize the queue of simulator phases to be run *AFTER*
        # successfully halting this phase.
        self.dequeue_running()

        # Set this simulator and the previously running phase to the halted
        # state *AFTER* successfully halting this phase.
        self._phase_working_state = SimmerState.HALTED

    # ..................{ SLOTS ~ private : action           }..................
    # Slots connected to signals emitted by "QAction" objects.

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
        self._die_if_running()

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


    #FIXME: Sadly, this remains entrenched in horror. The issue appears to be
    #that "QThread" is too low-level to actually bother with "trivial" issues
    #like sharing the time slice with other running Qt-based threads -- like,
    #say, the main thread. This is completely non-sensical, as well as
    #completely contrary to the concept of multithreading as implemented in
    #effectively *OTHER* other multithreading framework. Consequently, it would
    #appear that we either need to:
    #
    #* Completely abandon the current "QThread"-based approach in favour of
    #  either:
    #  * A "QRunner" + "QThreadPool"-based approach.
    #  * A "QConcurrent"-based approach. This is infeasible in our case, sadly.
    #* Laboriously refactor the
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

        #FIXME: *OMFG.* This was it. The GIL ensured that only the _work()
        #method of this worker had access to the time slice, thus preventing
        #this method and hence the parent _toggle_playing() slot from returning
        #and hence returning control to the main event loop. Absolute insanity,
        #which I only realized after reading the following astute logic:
        #
        #    "Similarly, if your application makes use of a large number of
        #     threads and Python result handlers, you may come up against the
        #     limitations of the GIL. As mentioned previously, when using
        #     threads execution of Python is limited to a single thread at one
        #     time. The Python code [i.e., slots in the main thread] that
        #     handles signals from your threads can be blocked by your workers
        #     and vice versa. Since blocking your slot functions blocks the
        #     event loop, this can directly impact GUI responsiveness.
        #     In these cases it is often better to investigate using a
        #     pure-Python thread pool (e.g. concurrent futures) implementation
        #     to keep your processing and thread event handling further isolated
        #     from your GUI."
        #
        #See also: https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool/
        #
        #The final paragraph fails to make sense to me, however. What would
        #using a pure-Python thread pool seek to achieve? How would doing so in
        #any way circumvent the GIL? Unless you're actually using a pure-Python
        #*PROCESS* pool, the GIL absolutely still remains in effect.
        #FIXME: Actually, wait. Something's critically wrong. While the GIL is
        #absolutely in effect, that still fails to explain why the GUI is
        #literally unresponsive. Clearly, the worker is still being run in the
        #main event thread -- even though Qt claims otherwise. some combination
        #of PySide2, Qt, and/or Python are *NOT* correctly multithreading. This
        #is trivially observed by running the sample PyQt5-based "threado"
        #application, which actually is responsive despite multithreading. Our
        #dim suspicion is that we're doing something *HORRIBLE* in pure-Python
        #that's causing the GUI to constaintly sieze the GIL. Tooltip filtering
        #and log handling seem like reasonable culprits. This is going to take
        #forever to sort out, sadly. Unfortunately, because we implemented this
        #functionality last rather than first, we have *SO* much baggage that
        #needs to be disabled one-by-one to get to the bottom of this.
        #
        #As a start, we need to isolate whether or not:
        #
        #* "PySide2" is the issue. To do so, refactor the sample "threado"
        #  application to leverage PySide2 instead. (Trivial).
        #* "QThread" is the issue. To do so, refactor the sample "threado"
        #  application to leverage "QThread" instead. (Hopefully trivial, but
        #  probably not).
        #* BETSE is the issue. To do so, refactor the sample "threado"
        #  application to just run a hard-coded BETSE seed phase with a
        #  hard-coded simulation configuration file. (Hopefully trivial, but
        #  probably not).
        #
        #Our working assumption is that *NONE* of the above are the issue, but
        #that BETSEE itself is somehow the issue. If that's the case, the only
        #sane solution will be to:
        #
        #* Recursively copy "~/py/betsee" to... say, "~/tmp/betsee".
        #* Iteratively remove functionality from "~/tmp/betsee" until the GUI
        #  becomes responsive while seeding. This will be *EXTREMELY* tedious
        #  and annoying, but we see no alternatives. Again, start with tooltip
        #  filtering and log handling.

        #FIXME: Demonstrably awful. Pass "QObject" instances instead.
        # self._start_signal.connect(worker_seed.start)
        # self._start_signal.emit(self._sim_conf.filename)
        # worker_seed.start_signal.emit(self._sim_conf.filename)

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

        from betsee.util.thread import guithread
        logs.log_debug(
            'Object "%s" in main GUI thread "%d"...',
            self.obj_name, guithread.get_current_thread_id())

        # from PySide2.QtCore import QThread
        # thread = QThread()
        # thread.setObjectName('simmer_thread')
        # thread.finished.connect(thread.deleteLater)

        # Start this thread and hence this thread's event loop. This does *NOT*
        # start any workers adopted into this thread; this only permits slots
        # for these workers to begin receiving signals.
        # thread.start()

        # self._start_signal.connect(worker_seed.start)
        # self._start_signal.emit(self._sim_conf.filename)

        # Test the seed worker.
        # worker_seed = QBetseeSimmerWorkerSeed()
        #
        # # Adopt these workers into this thread.
        # self._thread.adopt_worker(worker_seed)
        # # worker_seed.moveToThread(self._thread)
        # # worker_seed.moveToThread(thread)

        from betsee.gui.simtab.run.work.guisimrunworkpool import Worker

        #FIXME: The current "Worker" API accepting an arbitrary callable seems
        #dangerous, particularly if that callable is a bound method living in a
        #different thread. We probably instead want to leverage the old
        #_work()-based approach by requiring workers to subclass this superclass
        #and define an abstract _work() method that the superclass run() method
        #then internally calls. Anyway!

        # Any other args, kwargs are passed to the run function.
        #
        # Note: is deep copying arguments necessary? No idea. It probably is to
        # avoid race conditions induced by desynchronization issues.
        worker = Worker(_run_all_subcommands, str(self._sim_conf.filename))

        #FIXME: Uncommenting the following line induces hard segmentation faults
        #on worker completion with *NO* explicit error message. We have little
        #to no interest in debugging this at the moment; ergo, this remains
        #commented out until further notice. *mournful_sigh*
        # worker.signals.result.connect(self.print_output)

        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        #FIXME: *CRITICAL*: we're currently ignoring exceptions raised by this
        #worker. To handle these exceptions, we'll need to:
        #
        #* Define a new _catch_exception(tuple) slot of this class, presumably
        #  by either:
        #  * Re-raising the exception described by the passed tuple. (Unclear if
        #    this is feasible. If it is, this might be the ideal solution.)
        #  * Directly call a method displaying the exception described by the
        #    passed tuple. (Less ideal, but probably *MUCH* simpler to
        #    implement as a first-draft approach.)
        #* Connect this slot to the "worker.signals.error" signal above.

        #FIXME: Do this rather than what we currently do:
        # guipoolthread.run_worker(worker)
        guipoolthread.get_thread_pool().start(worker)


    @Slot(int)
    def progress_fn(self, n):
        print("%d%% done" % n)

    @Slot()
    def thread_complete(self):
        print("THREAD COMPLETE!")

    @Slot(object)
    def print_output(self, s):
        print(s)

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
        self._action_halt_playing.setEnabled(self._is_working)

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

# ....................{ RUNNERS                            }....................
def _run_all_subcommands(conf_filename):

    # Isolate importation statements to this worker.
    from betse.science.parameters import Parameters
    from betse.science.simrunner import SimRunner

    #FIXME: Non-ideal for the following obvious reasons:
    #
    #* The "main_window.sim_conf" object already has a Parameters() object
    #  in-memory. The changes performed here will *NOT* be propagated back
    #  into that object. That is bad.
    #* We shouldn't need to manually modify this file, anyway. Or should we?
    #  Should the GUI just assume absolute control over this file? That
    #  doesn't quite seem right, but it certainly would be simpler to do so.
    #  Well, at least for now.
    #FIXME: Ah-ha! The simplest means of circumventing the need to write
    #these changes back out to disk would be to refactor the
    #SimRunner.__init__() method to optionally accept a "Parameters" object
    #classified into a "_p" instance variable. Doing so, however, would mean
    #refactoring most methods of this class to reuse "_p" rather than
    #instantiate a new "Parameters" object each call. Of course, we arguably
    #should be doing that *ANYWAY* by unconditionally creating "_p" in
    #SimRunner.__init__() regardless of whether a "Parameters" object is
    #passed or not. We'll need to examine this further, of course.

    # Simulation configuration deserialized from this file.
    p = Parameters().load(conf_filename)

    # Disable all simulation configuration options either requiring
    # interactive user input *OR* displaying graphical output intended for
    # interactive user consumption (e.g., plots, animations).
    p.anim.is_after_sim_show = False
    p.anim.is_while_sim_show = False
    p.plot.is_after_sim_show = False

    # Enable all simulation configuration options exporting to disk.
    p.anim.is_after_sim_save = True
    p.anim.is_while_sim_save = True
    p.plot.is_after_sim_save = True

    # Reserialize these changes back to this file.
    p.save_inplace()

    # return

    #FIXME: Uncomment the plot_seed() call after pipelining that subcommand.

    # Run all simulation subcommands.
    sim_runner = SimRunner(conf_filename=conf_filename)
    sim_runner.seed()
    sim_runner.init()
    sim_runner.sim()
    # sim_runner.plot_seed()
    sim_runner.plot_init()
    sim_runner.plot_sim()
