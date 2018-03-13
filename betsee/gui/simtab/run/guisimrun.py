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
    _state_queued : SimulatorState
        Condition of the currently queued simulation subcommand if any,
        analogous to a state in a finite state automata.

    Attributes (Private: Controllers)
    ----------
    _phase_seed : QBetseeSimulatorPhase
        Controller for the seed phase of this simulator.
    _phase_init : QBetseeSimulatorPhase
        Controller for the initialization phase of this simulator.
    _phase_sim : QBetseeSimulatorPhase
        Controller for the simulation phase of this simulator.

    Attributes (Private: Widgets)
    ----------
    _action_sim_run_toggle : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle` action.
    _action_sim_run_halt : QAction
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
        self._action_sim_run_toggle = None
        self._action_sim_run_halt = None
        self._state_queued = None

        # Controllers for each phase encapsulated by this simulator.
        self._phase_seed = QBetseeSimulatorPhase(self)
        self._phase_init = QBetseeSimulatorPhase(self)
        self._phase_sim  = QBetseeSimulatorPhase(self)


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
        self._action_sim_run_toggle = main_window.action_sim_run_toggle
        self._action_sim_run_halt   = main_window.action_sim_run_halt

        # Initialize all simulator phase controllers (in arbitrary order).
        self._phase_seed.init(
            main_window=main_window, phase_kind=SimPhaseKind.SEED)
        self._phase_init.init(
            main_window=main_window, phase_kind=SimPhaseKind.INIT)
        self._phase_sim.init(
            main_window=main_window, phase_kind=SimPhaseKind.SIM)

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()


    def _update_widgets(self) -> None:
        '''
        Update the low-level state of all widgets controlled by this simulator
        to reflect the current high-level state of this simulator.
        '''

        #FIXME: Conditionally enable this group of widgets as described here.

        # Enable all widgets controlling the state of the currently queued
        # subcommand only if one or more subcommands are currently queued.
        # main_window.sim_cmd_run_state.setEnabled(False)

        pass


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of simulation subcommands.
        '''

        # Connect each such action to this object's corresponding slot.
        # self._action_make_sim.triggered.connect(self._make_sim)

        # Connect this object's signals to all corresponding slots.
        # self.set_filename_signal.connect(self.set_filename)

        # Set the state of all widgets dependent upon this simulation
        # subcommand state *AFTER* connecting all relavant signals and slots.
        # Initially, no simulation subcommands have yet to be queued or run.
        #
        # Note that, as this slot only accepts strings, the empty string rather
        # than "None" is intentionally passed for safety.
        # self.set_filename_signal.emit('')

        pass

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
    # @Slot()
    # def _open_sim(self) -> None:
    #     '''
    #     Slot invoked on the user requesting that the currently open simulation
    #     configuration if any be closed and an existing external simulation
    #     configuration be opened.
    #     '''
    #
    #     # Absolute path of an existing YAML-formatted simulation configuration
    #     # file selected by the user.
    #     conf_filename = self._show_dialog_sim_conf_open()
