#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

#FIXME: Refactor to leverage threading via the new "work" subpackage as follows:
#
#* Preserve most existing attributes and properties of this class. That said...
#* Remove the three methods in the "QUEUERS" subsection from *ALL* submodules,
#  possibly excluding the _run_queued() method -- which we might want to
#  preserve *ONLY* in this submodule. Even then, that method should still be
#  removed from all other submodules.
#* Refactor the "_queue_running" variable from a deque of phases to a deque of
#  simulator workers produced by the "work.guisimrunworkqueue" submodule.
#* In the __init__() method:
#  * Define a new "_thread" variable as an instance of "QBetseeWorkableThread".
#  * Define one new "_worker_"-prefixed variable for each of the five possible
#    simulation subcommands (e.g., "_worker_seed").
#  * For each such worker, manually adopt that worker into that thread: e.g.,
#
#      self._thread.adopt_worker(self._worker_seed)
#
#  * Define a new "_PHASE_KIND_TO_PHASE" dictionary mapping from phase types to
#    simulator phases: e.g.,
#
#      # Rename the "self._phases" sequence to "self._PHASES" as well, please.
#      self._PHASE_KIND_TO_PHASE = {
#          SimPhaseKind.SEED: self._phase_seed, ...
#      }
#
#* Refactor the critical _phase_running() property to:
#  * Get the "kind" property of the leading worker in "_queue_running".
#  * Map this property to the corresponding phase via "_PHASE_KIND_TO_PHASE".
#* Refactor the _run_queued() method as follows:
#  * For the first worker in "_queued_running":
#    * Emit a signal connected to the start() slot of that worker. (Probably
#      just a signal of that same worker named "start_signal", for brevity.)
#  * ...that's it. Crazy, eh?
#* Rename the _run_queued() method to _start_worker_queued_next().
#* Rename the "_queue_running" variable to "_worker_queue".
#* Rename the _phase_running() property (and all subsidiary properties) to
#  _phase_working().
#* Rename the _is_running() property to _is_working().
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
from PySide2.QtCore import QCoreApplication, QObject, Slot  # Signal
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.text import strs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
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
    _queue_running : deque
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

    Attributes (Private: Controllers)
    ----------
    _phases : SequenceTypes
        Sequence of all simulator phase controllers (e.g., :attr:`_phase_seed`),
        needed for iteration over these controllers. For sanity, these phases
        are ordered is simulation order such that:
        * The seed phase is listed *before* the initialization phase.
        * The initialization phase is listed *before* the simulation phase.
    _phase_seed : QBetseeSimmerPhase
        Controller for the seed phase of this simulator.
    _phase_init : QBetseeSimmerPhase
        Controller for the initialization phase of this simulator.
    _phase_sim : QBetseeSimmerPhase
        Controller for the simulation phase of this simulator.

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

        # Controllers for each simulator phase.
        self._phase_seed = QBetseeSimmerPhase(self)
        self._phase_init = QBetseeSimmerPhase(self)
        self._phase_sim  = QBetseeSimmerPhase(self)

        # Set the type of such phase. Since the QObject.__init__() method cannot
        # be redefined to accept subclass-specific parameters, these types
        # *MUST* be subsequently set as follows.
        self._phase_seed.kind = SimPhaseKind.SEED
        self._phase_init.kind = SimPhaseKind.INIT
        self._phase_sim .kind = SimPhaseKind.SIM

        # Sequence of all simulator phases. For sanity (e.g., during iteration),
        # these phases are intentionally listed in simulation order.
        self._phases = (self._phase_seed, self._phase_init, self._phase_sim)

        # Nullify all remaining instance variables for safety.
        self._action_toggle_playing = None
        self._action_halt_playing = None
        self._player_toolbar = None
        self._queue_running = None
        self._status = None


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
    def _is_running(self) -> bool:
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
        #    return self._queue_running is not None and len(self._queue_running)
        return bool(self._queue_running)

    # ..................{ PROPERTIES ~ phase                 }..................
    @property
    def _phase_running(self) -> QBetseeSimmerPhase:
        '''
        Queued simulator phase that is currently **running** (i.e., either being
        modelled or exported by this simulator) if any *or* raise an exception
        otherwise.

        Equivalently, this phase is the first item of the underlying queue of
        all simulator phases to be run.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`_is_running` property
        is ``True``).

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
              :attr:`_queue_running` is either ``None`` or empty).
        '''

        # If *NO* simulator phase is currently running, raise an exception.
        self._die_unless_running()

        # Return true only if one or more phases are queued.
        return self._queue_running[0]

    # ..................{ PROPERTIES ~ phase : state         }..................
    # This trivial property getter exists only so that the corresponding
    # non-trivial property setter may be defined.
    @property
    def _phase_running_state(self) -> SimmerState:
        '''
        State of the queued simulator phase that is currently **running** (i.e.,
        either being modelled or exported by this simulator) if any *or* raise
        an exception otherwise.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`_is_running` property
        is ``True``).

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
              :attr:`_queue_running` is either ``None`` or empty).

        See Also
        ----------
        :meth:`_phase_running`
            Further details.
        '''

        return self._phase_running.state


    @_phase_running_state.setter
    @type_check
    def _phase_running_state(self, state: SimmerState) -> None:
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
        guaranteed to be non-empty (i.e., when the :meth:`_is_running` property
        is ``True``).

        Parameters
        ----------
        state: SimmerState
            New state to set this phase to.

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
              :attr:`_queue_running` is either ``None`` or empty).

        See Also
        ----------
        :meth:`_phase_running_state`
            Further details.
        '''

        #FIXME: This may now induce infinite recursion. *sigh*

        # Set the state of the currently running phase to this state.
        self._phase_running.state = state

        # Set the state of this simulator to the same state.
        # self.state = state

    # ..................{ EXCEPTIONS ~ running               }..................
    def _die_if_running(self) -> None:
        '''
        Raise an exception if some queued simulator phase is currently
        **running** (i.e., either being modelled or exported by this simulator).

        See Also
        ----------
        :meth:`_is_running`
            Further details.
        '''

        if self._is_running:
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
        :meth:`_is_running`
            Further details.
        '''

        if not self._is_running:
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
            if self._is_running:
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
            self._phase_running_state = SimmerState.PAUSED


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
        self._phase_running_state = SimmerState.HALTED

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
        Define the :attr:`_queue_running` queue of all simulator phases to be
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
              :attr:`_queue_running` is already defined to be non-``None``).
        '''

        # Enqueue our superclass.
        super().enqueue_running()

        # If some simulator phase is currently running, raise an exception.
        self._die_if_running()

        # Initialize this queue to the empty double-ended queue (i.e., deque).
        self._queue_running = deque()

        # For each possible phase...
        for phase in self._phases:
            # If this phase is currently queued for modelling or exporting...
            if phase.is_queued:
                # Record which actions this phase was queued for.
                phase.enqueue_running()

                # Enqueue this phase.
                self._queue_running.append(phase)


    def dequeue_running(self) -> None:
        '''
        Revert the :attr:`_queue_running` queue to ``None``, effectively
        dequeueing (i.e., popping from this queue) all previously queued
        simulator phases.
        '''

        # Dequeue our superclass.
        super().dequeue_running()

        # Uninitialize this queue.
        self._queue_running = None

        # For each possible phase, forget which actions this phase was queued
        # for (if any). While technically optional, doing so should preserve
        # sanity by assisting in debugging.
        for phase in self._phases:
            phase.dequeue_running()


    def run_enqueued(self) -> None:
        '''
        Iteratively run each simulator phase enqueued (i.e., appended to the
        :attr:`_queue_running` queue of such phases) by a prior call to the
        :meth:`enqueue_running` method.
        '''

        # While one or more enqueued phases have yet to be run...
        while self._is_running:
            # Enqueued simulator phase to be run.
            phase_queued = self._phase_running

            # Run all actions previously enqueued for this phase (e.g.,
            # modelling, exporting).
            phase_queued.run_enqueued()

            # Dequeue this phase *AFTER* successfully running these actions.
            self._queue_running.pop()

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
        self._action_halt_playing.setEnabled(self._is_running)

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
