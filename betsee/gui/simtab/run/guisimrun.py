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
from betsee.gui.simtab.run.guisimrunstate import (
    SimulatorState,
    SIMULATOR_STATE_TO_STATUS_TERSE,
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
    _state_seed : SimulatorState
        Current state of the seed phase for the current simulation.
    _state_init : SimulatorState
        Current state of the initialization phase for the current simulation.
    _state_sim : SimulatorState
        Current state of the simulation phase for the current simulation.

    Attributes (Private: Widgets)
    ----------
    _action_sim_run_toggle : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle` action.
    _action_sim_run_halt : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_halt` action.
    _sim_run_queue_seed_model : QCheckbox
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_seed_model` widget.
    _sim_run_queue_seed_model_lock : QToolButton
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_seed_model_lock`
        widget.
    _sim_run_queue_seed_status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_seed_status` widget.
    _sim_run_queue_init_model : QCheckbox
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_init_model` widget.
    _sim_run_queue_init_model_lock : QToolButton
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_init_model_lock`
        widget.
    _sim_run_queue_init_export : QCheckbox
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_init_export` widget.
    _sim_run_queue_init_status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_init_status` widget.
    _sim_run_queue_sim_model : QCheckbox
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_sim_model` widget.
    _sim_run_queue_sim_model_lock : QToolButton
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_sim_model_lock`
        widget.
    _sim_run_queue_sim_export : QCheckbox
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_sim_export` widget.
    _sim_run_queue_sim_status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_queue_sim_status` widget.
    _sim_run_state_progress : QProgressBar
        Alias of the :attr:`QBetseeMainWindow.sim_run_state_progress` widget.
    _sim_run_state_status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_state_status` widget.
    _sim_run_state_substatus : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_state_substatus` widget.
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
        self._sim_run_queue_seed_model = None
        self._sim_run_queue_seed_model_lock = None
        self._sim_run_queue_seed_status = None
        self._sim_run_queue_init_model = None
        self._sim_run_queue_init_model_lock = None
        self._sim_run_queue_init_export = None
        self._sim_run_queue_init_status = None
        self._sim_run_queue_sim_model = None
        self._sim_run_queue_sim_model_lock = None
        self._sim_run_queue_sim_export = None
        self._sim_run_queue_sim_status = None
        self._sim_run_state_progress = None
        self._sim_run_state_status = None
        self._sim_run_state_substatus = None
        self._state_queued = None
        self._state_seed = None
        self._state_init = None
        self._state_sim = None


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Finalize this simulator's initialization, owned by the passed main
        window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulation subcommander.

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
        logs.log_debug('Sanitizing simulation subcommand state...')

        # Initialize all widgets concerning simulation subcommand state the
        # *BEFORE* connecting all relevant signals and slots typically expecting
        # these widgets to be initialized.
        self._init_widgets(main_window)
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (not necessarily owned by this object) whose internal
        state pertains to the high-level state of simulation subcommands.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Classify all instance variables of this main window subsequently
        # required by this object. Since this main window owns this object,
        # since weak references are unsafe in a multi-threaded GUI context, and
        # since circular references are bad, this object intentionally does
        # *NOT* retain a reference to this main window.
        self._action_sim_run_toggle = main_window.action_sim_run_toggle
        self._action_sim_run_halt   = main_window.action_sim_run_halt
        self._sim_run_queue_seed_model = main_window.sim_run_queue_seed_model
        self._sim_run_queue_seed_model_lock = (
            main_window.sim_run_queue_seed_model_lock)
        self._sim_run_queue_seed_status = main_window.sim_run_queue_seed_status
        self._sim_run_queue_init_model = main_window.sim_run_queue_init_model
        self._sim_run_queue_init_model_lock = (
            main_window.sim_run_queue_init_model_lock)
        self._sim_run_queue_init_export = main_window.sim_run_queue_init_export
        self._sim_run_queue_init_status = main_window.sim_run_queue_init_status
        self._sim_run_queue_sim_model = main_window.sim_run_queue_sim_model
        self._sim_run_queue_sim_model_lock = (
            main_window.sim_run_queue_sim_model_lock)
        self._sim_run_queue_sim_export = main_window.sim_run_queue_sim_export
        self._sim_run_queue_sim_status = main_window.sim_run_queue_sim_status
        self._sim_run_state_progress   = main_window.sim_run_state_progress
        self._sim_run_state_status     = main_window.sim_run_state_status
        self._sim_run_state_substatus  = main_window.sim_run_state_substatus

        #FIXME: After at least partially implementing queueing, uncomment this:
        # self._state = SimulatorState.UNQUEUED

        # By default, queue all subcommands run by the "try" subcommand *AFTER*
        # classifying instance variables.
        #
        # Default the simulator to the queued state.
        self._state_queued = SimulatorState.QUEUED

        #FIXME: These states should be dynamically set by slots connected to
        #the QCheckBox.toggled() signal emitted by each of these widgets. To do
        #so, we'll need to define one such slot for each such widget: e.g.,
        #
        #    # Define a seed-specific modelling checkbox (un)checked slot.
        #    @Slot(bool)
        #    def toggle_seed_model(self, is_seed_model: bool) -> None:
        #        if self._state_seed in SIMULATOR_STATES_FIXED:
        #            return
        #
        #        if is_seed_model:
        #            if self._state_seed is SimulatorState.UNQUEUED:
        #                self._state_seed = SimulatorState.QUEUED
        #        else:
        #
        #
        #    # Connect this slot to the corresponding signal here.
        #    self._state_seed.toggled.connect(self.toggle_seed_model)
        #
        #Trivial
        self._state_seed = SimulatorState.QUEUED
        self._state_init = None
        self._state_sim = None

        # Queue all simulation phases to be modelled.
        self._sim_run_queue_seed_model.setChecked(True)
        self._sim_run_queue_init_model.setChecked(True)
        self._sim_run_queue_sim_model.setChecked(True)

        # Queue all exportable phases to be exported.
        self._sim_run_queue_init_export.setChecked(True)
        self._sim_run_queue_sim_export.setChecked(True)

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()


    def _update_widgets(self) -> None:
        '''
        Update the low-level state of all widgets controlled by this simulator
        to reflect the current high-level state of this simulator.
        '''

        #FIXME: Generalize to all other phases, presumably by defining a new
        #_update_widget_phase() method passed the following parameters:
        #
        #* Phase state.
        #* Modelling checkbox.
        #* Exporting checkbox.
        #* Phase status (terse).
        #* Phase status (verbose).
        #
        #Or maybe this is already getting overkill. We really need a better way.
        #Would encapsulating the above parameters into a new class in a new
        #submodule -- say, "QBetseeSimulatorPhase(QBetseeControllerABC)" in
        #"guisimrunphase" -- providing these parameters as instance variables
        #and a corresponding public update_widgets() method not succinctly
        #address this issue?
        #
        #We think it would. We're clearly going to do this anyway, so... Let's
        #just do this now and save us the substantial refactoring effort later.
        #Here's the relevant QBetseeSimulatorPhase.update_widgets() logic:
        #
        #    status_terse   = SIMULATOR_STATE_TO_STATUS_TERSE  .get(self._state, None)
        #    status_verbose = SIMULATOR_STATE_TO_STATUS_VERBOSE.get(self._state, None)
        #
        #    if status_terse is None:
        #        raise SomeKindOfException()
        #    if status_verbose is None:
        #        raise SomeKindOfException()
        #
        #    self._label_status_terse  .setText(status_terse)
        #
        #    #FIXME: This one isn't quite so simple. We'll need to interpolate
        #    #various values into this template contextually depending on the
        #    #current state. For now, a simple if conditional should suffice.
        #    self._label_status_verbose.setText(status_verbose)

        #FIXME: Conditionally enable this group of widgets as described here.

        # Enable all widgets controlling the state of the currently queued
        # subcommand only if one or more subcommands are currently queued.
        # main_window.sim_cmd_run_state.setEnabled(False)


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

    # ..................{ PROPERTIES ~ bool                  }..................
    # @property
    # def is_open(self) -> bool:
    #     '''
    #     ``True`` only if a simulation configuration file is currently open.
    #     '''
    #
    #     return self.p.is_loaded

    # ..................{ PROPERTIES ~ str                   }..................
    # @property
    # def dirname(self) -> StrOrNoneTypes:
    #     '''
    #     Absolute path of the directory containing the currently open
    #     simulation configuration file if any *or* ``None`` otherwise.
    #     '''
    #
    #     return self.p.conf_dirname

    # ..................{ EXCEPTIONS                         }..................
    # def die_unless_open(self) -> bool:
    #     '''
    #     Raise an exception unless a simulation configuration file is currently
    #     open.
    #     '''
    #
    #     if not self.is_open:
    #         raise BetseeSimConfException(
    #             'No simulation configuration currently open.')

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

    # ..................{ SLOTS ~ state                      }..................
    # @Slot(str)
    # def set_filename(self, filename: str) -> None:
    #     '''
    #     Slot signalled on both the opening of a new simulation configuration
    #     and closing of an open simulation configuration.
    #
    #     Parameters
    #     ----------
    #     filename : StrOrNoneTypes
    #         Absolute path of the currently open YAML-formatted simulation
    #         configuration file if any *or* the empty string otherwise (i.e., if
    #         no such file is open).
    #     '''
    #
    #     # Notify all interested slots that no unsaved changes remain, regardless
    #     # of whether a simulation configuration has just been opened or closed.
    #     self.set_dirty_signal.emit(False)

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
    #
    #     # If the user canceled this dialog, silently noop.
    #     if conf_filename is None:
    #         return
    #     # Else, the user did *NOT* cancel this dialog.
    #
    #     # Close the currently open simulation configuration if any.
    #     self._close_sim()
    #
    #     # Deserialize this low-level file into a high-level configuration.
    #     self.load(conf_filename)
    #
    #     # Update the status bar *AFTER* successfully completing this action.
    #     self._status_bar.showMessage(QCoreApplication.translate(
    #         'QBetseeSimConf', 'Simulation opened.'))
