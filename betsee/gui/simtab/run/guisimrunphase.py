#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator phase** (i.e., simulation phase to be queued for modelling
and/or exporting by this simulator) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal, Slot
from betse.science.export.expenum import SimExportType
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseePySideWindowException
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
class QBetseeSimulatorPhase(QBetseeControllerABC):
    '''
    Low-level **simulator phase** (i.e., :mod:`PySide2`-based object wrapping a
    simulation phase to be queued for modelling and/or exporting by this
    simulator).

    This simulator phase maintains all state required to interactively manage
    this simulation phase, including:

    Attributes (Public)
    ----------

    Attributes (Private: Non-widgets)
    ----------
    _phase_kind : SimPhaseKind
        Type of simulation phase controlled by this controller.
    _phase_name : str
        Machine-readable alphabetic lowercase name of the type of simulation
        phase controlled by this controller (e.g., ``seed``, ``init``, ``sim``).
    _state : SimulatorState
        Current state of this phase for the current simulation.

    Attributes (Private: Widgets)
    ----------
    _is_queueable_model : QCheckBox
        Checkbox toggling whether this phase is queueable for modelling.
    _is_queued_model : QCheckBox
        Checkbox toggling whether this phase is queued for modelling.
    _is_queued_export : QCheckBox
        Checkbox toggling whether this phase is queued for exporting.
    _queue_status : QLabel
        Label synopsizing the current queueing of this phase.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator phase.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Default this phase to the unqueued state.
        self._state = SimulatorState.UNQUEUED

        # Nullify all remaining instance variables for safety.
        self._is_queueable_model = None
        self._is_queued_model = None
        self._is_queued_export = None
        self._phase_kind = None
        self._phase_name = None
        self._queue_status = None


    @type_check
    def init(
        self,
        main_window: QBetseeMainWindow,
        phase_kind: SimPhaseKind,
    ) -> None:
        '''
        Finalize this simulator phase's initialization, owned by the passed main
        window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulator phase.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child widgets
        (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        phase_kind : SimPhaseKind
            Type of simulation phase controlled by this controller.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Classify all passed parameters *EXCEPT* the passed main window.
        # Classifying the latter invites circular references.
        self._phase_kind = phase_kind

        # Machine-readable alphabetic lowercase name of the type of simulation
        # phase controlled by this controller (e.g., "seed", "init", "sim").
        self._phase_name = enums.get_member_name_lowercase(phase_kind)

        # Log this finalization.
        logs.log_debug(
            'Sanitizing simulator phase "%s" state...', self._phase_name)

        # Initialize all widgets concerning simulator phase state.
        self._init_widgets(main_window)

        # Connect all relevant signals and slots *AFTER* initializing these
        # widgets, as the former typically requires the latter.
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (*not* always owned by this object) concerning this
        simulator phase.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Names of all instance variables of this main window yielding widgets
        # specific to this simulator phase.
        is_queueable_model_name = 'sim_run_queue_{}_model_lock'.format(
            self._phase_name)
        is_queued_model_name = 'sim_run_queue_{}_model'.format(self._phase_name)
        is_queued_export_name = 'sim_run_queue_{}_export'.format(
            self._phase_name)
        queue_status_name = 'sim_run_queue_{}_status'.format(self._phase_name)

        # Classify these widgets. Since this main window owns this object, since
        # weak references are unsafe in a multi-threaded GUI context, and since
        # circular references are bad, this object intentionally does *NOT*
        # retain a reference to this main window.
        self._is_queueable_model = getattr(
            main_window, is_queueable_model_name, None)
        self._is_queued_model = getattr(
            main_window, is_queued_model_name, None)
        self._is_queued_export = getattr(
            main_window, is_queued_export_name, None)
        self._queue_status = getattr(main_window, queue_status_name, None)

        # If any such widget does *NOT* exist, raise an exception.
        # raise BetseePySideWindowException()

        # If this is the seed phase

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
