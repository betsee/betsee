#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

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
from PySide2.QtCore import QCoreApplication, Slot  # Signal
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type.text import strs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimulatorException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunphase import QBetseeSimulatorPhase
from betsee.gui.simtab.run.guisimrunstate import (
    SimulatorState,
    SIMULATOR_STATE_TO_STATUS_VERBOSE,
    # MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS,
    # EXPORTING_TYPE_TO_STATUS_DETAILS,
)
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC
from collections import deque

# ....................{ CLASSES                            }....................
class QBetseeSimulator(QBetseeControllerABC):
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

    Attributes (Public)
    ----------

    Attributes (Private: Non-widgets)
    ----------
    _queue_running : deque
        Queue of each **simulator phase** (i.e., :class:`QBetseeSimulatorPhase`
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
    _state : SimulatorState
        Condition of the currently queued simulation subcommand if any,
        analogous to a state in a finite state automata.

    Attributes (Private: Controllers)
    ----------
    _phases : SequenceTypes
        Sequence of all simulator phase controllers (e.g., :attr:`_phase_seed`),
        needed for iteration over these controllers. For sanity, these phases
        are ordered is simulation order such that:
        * The seed phase is listed *before* the initialization phase.
        * The initialization phase is listed *before* the simulation phase.
    _phase_seed : QBetseeSimulatorPhase
        Controller for the seed phase of this simulator.
    _phase_init : QBetseeSimulatorPhase
        Controller for the initialization phase of this simulator.
    _phase_sim : QBetseeSimulatorPhase
        Controller for the simulation phase of this simulator.

    Attributes (Private: Widgets)
    ----------
    _action_toggle_playing : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle` action.
    _action_halt_playing : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_halt` action.
    _status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_state_status` label,
        synopsizing the current state of this simulator.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Default this phase to the unqueued state.
        self._state = SimulatorState.UNQUEUED

        # Controllers for each phase encapsulated by this simulator.
        self._phase_seed = QBetseeSimulatorPhase(self)
        self._phase_init = QBetseeSimulatorPhase(self)
        self._phase_sim  = QBetseeSimulatorPhase(self)

        # Sequence of all simulator phases. For sanity (e.g., during iteration),
        # these phases are intentionally listed in simulation order.
        self._phases = (self._phase_seed, self._phase_init, self._phase_sim)

        # Nullify all remaining instance variables for safety.
        self._action_toggle_playing = None
        self._action_halt_playing = None
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

        # Log this initialization.
        logs.log_debug('Sanitizing simulator state...')

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

        # Classify variables of this main window required by this simulator.
        self._action_toggle_playing = main_window.action_sim_run_toggle
        self._action_halt_playing   = main_window.action_sim_run_halt
        self._status = main_window.sim_run_state_status

        # Initialize all simulator phase controllers (in arbitrary order).
        self._phase_seed.init(
            main_window=main_window, phase_kind=SimPhaseKind.SEED)
        self._phase_init.init(
            main_window=main_window, phase_kind=SimPhaseKind.INIT)
        self._phase_sim.init(
            main_window=main_window, phase_kind=SimPhaseKind.SIM)

        #FIXME: Excise the following code block after hooking this high-level
        #simulator GUI into the low-level "simrunner" submodule.

        # Avoid displaying detailed status for the currently queued subcommand,
        # as the low-level BETSE codebase lacks sufficient hooks to update this
        # status in a sane manner.
        main_window.sim_run_state_substatus_group.hide()

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of simulation subcommands.
        '''

        # Connect each such action to this object's corresponding slot.
        self._action_toggle_playing.toggled.connect(self._toggle_playing)
        self._action_halt_playing.triggered.connect(self._halt_playing)

        # Connect this object's signals to all corresponding slots.
        # self.set_filename_signal.connect(self.set_filename)

        # Set the state of all widgets dependent upon this simulation
        # subcommand state *AFTER* connecting all relavant signals and slots.
        # Initially, no simulation subcommands have yet to be queued or run.
        #
        # Note that, as this slot only accepts strings, the empty string rather
        # than "None" is intentionally passed for safety.
        # self.set_filename_signal.emit('')

    # ..................{ PROPERTIES ~ bool                  }..................
    @property
    def _is_queued(self) -> bool:
        '''
        ``True`` only if one or more simulator phases are currently queued for
        modelling and/or exporting.
        '''

        # Return true only if one or more phases are queued.
        return any(phase.is_queued() for phase in self._phases)


    @property
    def _is_running(self) -> bool:
        '''
        ``True`` only if some queued simulator phase is currently **running**
        (i.e., either being modelled or exported by this simulator).
        '''

        # Return true only if a queue of all phases to be run currently exists.
        # The lifecycle of this queue is managed in a just in time (JIT) manner
        # corresponding exactly to whether or not the simulator is running.
        # Specifically:
        #
        # * This queue defaults to "None".
        # * The _toggle_playing() slot instantiates this queue on first running
        #   a new queue of simulator phases.
        # * The _halt_playing() slot reverts this queue back to "None".
        return self._queue_running is None
        # return self._state in SIMULATOR_STATES_RUNNING

    # ..................{ PROPERTIES ~ phase                 }..................
    @property
    def _phase_running(self) -> QBetseeSimulatorPhase:
        '''
        Queued simulator phase that is currently **running** (i.e., either being
        modelled or exported by this simulator).

        Equivalently, this phase is the first item of the underlying queue of
        all simulator phases to be run.

        Raises
        ----------
        BetseeSimulatorException
            If either:
            * No simulator phase is currently running (i.e.,
              :attr:`_queue_running` is ``None``).
            * No simulator phase is currently queued to be run (i.e.,
              :attr:`_queue_running` is empty).
        '''

        #FIXME: Raise an exception unless this queue is both non-None and
        #non-empty.

        # Return true only if one or more phases are queued.
        return self._queue_running[0]

    # ..................{ EXCEPTIONS                         }..................
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
            raise BetseeSimulatorException(QCoreApplication.translate(
                'QBetseeSimulator', 'Simulator currently running.'))


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
            raise BetseeSimulatorException(QCoreApplication.translate(
                'QBetseeSimulator', 'Simulator currently running.'))

    # ..................{ SLOTS                              }..................
    #FIXME: Implement us up, noting the efficiency technicality below.
    @Slot(bool)
    def toggle_is_queued(self, is_queued: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling any :class:`QCheckBox` widget queueing any
        simulator phase for modelling and/or exporting.

        This slot guarantees sanity by preventing end users from interacting
        with inapplicable simulator widgets. Specifically, if:

        * Any such checkbox is checked, this slot enables all widgets
          controlling this simulator.
        * No such checkbox is checked, this slot disables all of these widgets.

        Parameters
        ----------
        is_queued : bool
            ``True`` only if an arbitrary such checkbox has been checked.
            Technically, the existence of the :meth:`_is_queued` property
            implies that this slot could technically accept *no* boolean
            parameter. Nonetheless, doing so permits us to improve the
            efficiency of this slot by avoiding inefficient access of that
            property in common edge cases.
        '''

        pass

    # ..................{ SLOTS ~ action                     }..................
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
            # If some simulator phase is currently running...
            if self._is_running:
                pass
            # Else, no simulator phase is currently running. In this case...
            else:
                # Initialize the queue of simulator phases to be run.
                self._enqueue_running()

                #FIXME: Actually run these phases.
                #FIXME: Set the state of this simulator.
                #FIXME: Set the state of the currently running phase.

            #FIXME: Set the state of both this simulator *AND* the currently
            #running phase *AFTER* successfully running this phase above.
        # Else, pause this subcommand.
        else:
            #FIXME: Actually pause the currently running phase here.

            # Set this simulator's state to the paused state *AFTER*
            # successfully pausing the simulator.
            self._state = SimulatorState.PAUSED

            #FIXME: Set the state of the previously running phase as well.

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()


    #FIXME: Ensure that slot is only signalled in sane contexts by conditionally
    #disabling the corresponding halt action when no phases are running. Maybe
    #we do this already in _update_widgets()? Verify us up, please.
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

        # Uninitialize the queue of simulator phases to be run.
        self._dequeue_running()

        #FIXME: Also set the current state of the currently running phase to the
        #halted state. We'll probably need to get our queue up and running.

        # Set this simulator's state to the halted state *AFTER* successfully
        # halting the simulator.
        self._state = SimulatorState.HALTED

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()

    # ..................{ UPDATERS                           }..................
    def _update_widgets(self) -> None:
        '''
        Update the contents of all widgets controlled by this simulator to
        reflect the current state of this simulation.
        '''

        # Update the text displayed by the "_status" label.
        self._update_status()

        #FIXME: Classify "_sim_cmd_run_state" above.
        #FIXME: Conditionally enable this group of widgets as described here.

        # Enable all widgets controlling the state of the currently queued
        # subcommand only if one or more subcommands are currently queued.
        # self._sim_cmd_run_state.setEnabled(is_queued)


    def _update_status(self) -> None:
        '''
        Update the text displayed by the :attr:`_status` label, verbosely
        synopsizing the current state of this simulator.
        '''

        # Unformatted template synopsizing the current state of this simulator.
        status_text_template = SIMULATOR_STATE_TO_STATUS_VERBOSE[self._state]

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

    # ..................{ QUEUERS                            }..................
    #* After iteration, validate that "self._queue_running" is
    #  non-empty. This queue should *NEVER* be empty. Why? Because we
    #  should do the following elsewhere:
    #  * Define a new toggle_is_queued() slot of this class, which
    #    each QBetseeSimulatorPhase.init() call should connect to the
    #    toggled() signals emitted by both of the modelling and export
    #    checkboxes specific to that phase. Note this implies that the
    #    QBetseeSimulatorPhase.init() method will need to be passed a
    #    reference to this parent, which that method must not retain.
    #  * In this toggle_is_queued() slot, if and only if
    #    "self._queue_running" is "None" (i.e., no subcommands are
    #    running), conditionally enable and disable the entire "Phase
    #    Player" "QGroupBox" depending on whether the passed boolean
    #    is true or not. (Trivial.)

    def _enqueue_running(self) -> None:
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
        BetseeSimulatorException
            If either:
            * No simulator phase is currently queued.
            * Some simulator phase is currently running (i.e.,
              :attr:`_queue_running` is already defined to be non-``None``).
        '''

        # If some simulator phase is currently running, raise an exception.
        self._die_if_running()

        #FIXME: Programmatically ensure this to be the case with appropriate
        #signals and slots.

        # If no simulator phase is currently queued, raise an exception.
        if not self._is_queued:
            raise BetseeSimulatorException(QCoreApplication.translate(
                'QBetseeSimulator', 'Simulator currently running.'))

        # Initialize this queue to the empty double-ended queue (i.e., deque).
        self._queue_running = deque()

        # For each simulator phase, queue each phase requested by the end user.
        for phase in self._phases:
            if phase.is_queued():
                self._queue_running.append(phase)


    def _dequeue_running(self) -> None:
        '''
        Revert the :attr:`_queue_running` queue to ``None``, effectively
        dequeueing (i.e., popping from this queue) all previously queued
        simulator phases.
        '''

        # Uninitialize this queue.
        self._queue_running = None
