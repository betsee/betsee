#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation-specific subcommands)
functionality.
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
from PySide2.QtCore import QCoreApplication, Signal, Slot
from betse.science.export.expenum import SimExportType
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type.types import type_check  #, StrOrNoneTypes
# from betsee.guiexception import BetseeSimConfException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunphase import QBetseeSimulatorPhase
from betsee.gui.simtab.run.guisimrunstate import (
    SimulatorState,
    SIMULATOR_STATE_TO_STATUS_VERBOSE,
    MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS,
    EXPORTING_TYPE_TO_STATUS_DETAILS,
)
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC
from collections import deque

# ....................{ CLASSES                            }....................
class QBetseeSimulator(QBetseeControllerABC):
    '''
    High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
    *and* controlling the execution of simulation-specific subcommands).

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
        Queue of all currently running simulation subcommands if any *or*
        ``None`` otherwise (i.e., if no such subcommands are running). While
        this container is technically a double-ended queue (i.e., deque), Python
        provides *no* corresponding single-ended queue. Since the former
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
        needed for iteration over these controllers.
    _phase_seed : QBetseeSimulatorPhase
        Controller for the seed phase of this simulator.
    _phase_init : QBetseeSimulatorPhase
        Controller for the initialization phase of this simulator.
    _phase_sim : QBetseeSimulatorPhase
        Controller for the simulation phase of this simulator.

    Attributes (Private: Widgets)
    ----------
    _action_toggle_simming : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle` action.
    _action_halt_simming : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_halt` action.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._action_toggle_simming = None
        self._action_halt_simming = None
        self._queue_running = None
        self._state = None

        # Controllers for each phase encapsulated by this simulator.
        self._phase_seed = QBetseeSimulatorPhase(self)
        self._phase_init = QBetseeSimulatorPhase(self)
        self._phase_sim  = QBetseeSimulatorPhase(self)

        # Sequence of these controllers.
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
        self._action_toggle_simming = main_window.action_sim_run_toggle
        self._action_halt_simming   = main_window.action_sim_run_halt

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
        self._action_toggle_simming.toggled.connect(self._toggle_simming)
        self._action_halt_simming.triggered.connect(self._halt_simming)

        # Connect this object's signals to all corresponding slots.
        # self.set_filename_signal.connect(self.set_filename)

        # Set the state of all widgets dependent upon this simulation
        # subcommand state *AFTER* connecting all relavant signals and slots.
        # Initially, no simulation subcommands have yet to be queued or run.
        #
        # Note that, as this slot only accepts strings, the empty string rather
        # than "None" is intentionally passed for safety.
        # self.set_filename_signal.emit('')

    # ..................{ SIGNALS                            }..................
    # set_filename_signal = Signal(str)
    # '''
    # Signal passed either the absolute path of the currently open YAML-formatted
    # simulation configuration file if any *or* the empty string otherwise.
    #
    # This signal is typically emitted on the user:
    #
    # * Opening a new simulation configuration.
    # * Closing a currently open simulation configuration.
    # '''

    # ..................{ SLOTS ~ action                     }..................
    @Slot(bool)
    def _toggle_simming(self, is_simming: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling the checkable :class:`QPushButton` widget
        corresponding to the :attr:`_action_toggle_simming` variable.

        Specifically, if:

        * This button is checked, this slot runs the currently queued subcommand
          by either:
          * If this subcommand was paused, resuming this subcommand.
          * Else, starting this subcommand.
        * This button is unchecked, this slot pauses this subcommand.

        Parameters
        ----------
        is_simming : bool
            ``True`` only if this :class:`QPushButton` is currently checked, in
            which case this slot runs this subcommand.
        '''

        # If now running the currently queued subcommand...
        if is_simming:
            #FIXME: Implement us up, please. To do so, note that we want to:
            #
            #* Define a new QBetseeSimulatorPhase.is_queued() method returning
            #  true only if either of the two checkboxes for that phase are
            #  currently checked. (Trivial.)
            #* Define a new _queue_running() method in this class. This
            #  method should (in order):
            #  * Raise an exception if "self._queue_running" is *NOT* "None".
            #  * Initialize "self._queue_running = deque()".
            #  * Iterate over the phases of "self._phases" and, for each such
            #    phase whose is_queued() method returns true, should append that
            #    phase object to "self._queue_running".
            #  * After iteration, validate that "self._queue_running" is
            #    non-empty. This queue should *NEVER* be empty. Why? Because we
            #    should do the following elsewhere:
            #    * Define a new toggle_is_queued() slot of this class, which
            #      each QBetseeSimulatorPhase.init() call should connect to the
            #      toggled() signals emitted by both of the modelling and export
            #      checkboxes specific to that phase. Note this implies that the
            #      QBetseeSimulatorPhase.init() method will need to be passed a
            #      reference to this parent, which that method must not retain.
            #    * In this toggle_is_queued() slot, if and only if
            #      "self._queue_running" is "None" (i.e., no subcommands are
            #      running), conditionally enable and disable the entire "Phase
            #      Player" "QGroupBox" depending on whether the passed boolean
            #      is true or not. (Trivial.)
            #* Perhaps define a new is_queue_running() property as follows, as
            #  we appear to require this logic in numerous code blocks:
            #
            #     @property
            #     def is_queue_running(self) -> bool:
            #         return self._queue_running is None
            #
            #* Call the _queue_running() method here.

            # If no simulation subcommands are currently running...
            if self._queue_running is None:
            # if self._state in SIMULATOR_STATES_RUNNING:
                pass
            #FIXME: Implement us up, please.
            # Else, a simulation subcommands is currently running.
            else:
                pass
        #FIXME: Implement us up, please.
        # Else, pause this subcommand.
        else:
            pass

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()


    @Slot()
    def _halt_simming(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget
        corresponding to the :attr:`_action_halt_simming` variable.
        '''

        #FIXME: Actually halt the running subcommand here, please.

        # Note that no simulation subcommands are currently running.
        self._queue_running = None

        # Set the current state to the halted state.
        self._state = SimulatorState.HALTED

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()

    # ..................{ UPDATERS                           }..................
    def _update_widgets(self) -> None:
        '''
        Update the contents of all widgets controlled by this simulator to
        reflect the current state of this simulation.
        '''

        # True only if the user has queued one or more subcommands.
        is_queued = False

        #FIXME: Classify "_sim_cmd_run_state" above.

        # Enable all widgets controlling the state of the currently queued
        # subcommand only if one or more subcommands are currently queued.
        # self._sim_cmd_run_state.setEnabled(is_queued)

        #FIXME: Conditionally enable this group of widgets as described here.

        # Enable all widgets controlling the state of the currently queued
        # subcommand only if one or more subcommands are currently queued.
        # main_window.sim_cmd_run_state.setEnabled(False)

        pass
