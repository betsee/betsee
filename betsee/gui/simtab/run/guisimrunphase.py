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
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.types import type_check  #, StrOrNoneTypes
# from betsee.guiexception import BetseePySideWindowException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunstate import (
    SimulatorState,
    SIMULATOR_STATE_TO_STATUS_TERSE,
    SIMULATOR_STATES_FLUID,
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
    state : SimulatorState
        Current state of this phase for the current simulation.

    Attributes (Private: Non-widgets)
    ----------
    _phase_kind : SimPhaseKind
        Type of simulation phase controlled by this controller.
    _phase_name : str
        Machine-readable alphabetic lowercase name of the type of simulation
        phase controlled by this controller (e.g., ``seed``, ``init``, ``sim``).

    Attributes (Private: Widgets)
    ----------
    _is_unqueueable_model : QCheckBox
        Checkbox toggling whether this phase is queueable for modelling.
    _is_queued_model : QCheckBox
        Checkbox toggling whether this phase is queued for modelling.
    _is_queued_export : QCheckBoxOrNoneTypes
        Checkbox toggling whether this phase is queued for exporting if this
        phase supports exporting *or* ``None`` otherwise. While most phases
        support exporting, some (e.g., the seed phase) do *not*.
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
        self.state = SimulatorState.UNQUEUED

        # Nullify all remaining instance variables for safety.
        self._is_unqueueable_model = None
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
        is_unqueueable_model_name = 'sim_run_queue_{}_model_lock'.format(
            self._phase_name)
        is_queued_model_name = 'sim_run_queue_{}_model'.format(
            self._phase_name)
        is_queued_export_name = 'sim_run_queue_{}_export'.format(
            self._phase_name)
        queue_status_name = 'sim_run_queue_{}_status'.format(
            self._phase_name)

        # Classify mandatory widgets unconditionally defined for *ALL* phases.
        self._is_unqueueable_model = main_window.get_widget(
            widget_name=is_unqueueable_model_name)
        self._is_queued_model = main_window.get_widget(
            widget_name=is_queued_model_name)
        self._queue_status = main_window.get_widget(
            widget_name=queue_status_name)

        # Classify optional widgets conditionally defined for only some phases.
        self._is_queued_export = main_window.get_widget_or_none(
            widget_name=is_queued_export_name)

        # Queue this phase to be modelled.
        self._is_queued_model.setChecked(True)

        # If this phase supports exporting,.queue this phase to be exported.
        if self._is_queued_export is not None:
            self._is_queued_export.setChecked(True)

            #FIXME: Excise the following code block after implementing queueing.
            # Prevent this phase from being dequeued for modelling or exporting.
            self._is_queued_export.setEnabled(False)

        #FIXME: Excise the following code block after implementing queueing.
        # Prevent this phase from being dequeued for modelling.
        self._is_unqueueable_model.setEnabled(False)
        self._is_queued_model.setEnabled(False)

        # Update the state of simulator widgets to reflect these changes.
        self._update_widgets()


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulator phase.
        '''

        # Connect signals emitted by widgets associated with this phase to
        # this phase's corresponding slots.
        self._is_unqueueable_model.toggled.connect(
            self._toggle_is_unqueueable_model)

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
    @Slot(bool)
    def _toggle_is_unqueueable_model(self, is_unqueueable_model: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling the checkable :class:`QToolButton` widget
        corresponding to the :attr:`_is_unqueueable_model` variable.

        Specifically, if:

        * This button is checked, this slot locks (i.e., disables) the
          :class:`QCheckBox` widget corresponding to the
          :attr:`_is_queued_model` variable.
        * This button is unchecked, this slot unlocks (i.e., enables) that
          :class:`QCheckBox` widget.

        Parameters
        ----------
        is_unqueueable_model : bool
            ``True`` only if this :class:`QToolButton` is currently checked.
        '''

        # One-liners for the greater glory of godly efficiency.
        self._is_queued_model.setEnabled(not is_unqueueable_model)

    # ..................{ UPDATERS                           }..................
    def _update_widgets(self) -> None:
        '''
        Update the contents of all widgets controlled by this simulator phase to
        reflect the current state of this phase.
        '''

        # If the current state of this phase is fluid (i.e., freely replaceable
        # with any other state)...
        if self.state in SIMULATOR_STATES_FLUID:
            # If either...
            if (
                # The modelling checkbox for this phase is checked...
                self._is_queued_model.isChecked() or
                # This phase has an exporting checkbox that is checked...
                (self._is_queued_export is not None and
                 self._is_queued_export.isChecked())
            # Then set this state to queued for modelling and/or exporting.
            ):
                self.state = SimulatorState.QUEUED
            # Else, this phase is queued for neither modelling nor exporting.
            # Set this state to unqueued.
            else:
                self.state = SimulatorState.UNQUEUED
        # Else, the current state of this phase is fixed and hence *NOT* freely
        # replaceable with any other state. For safety, this state is preserved.

        # Text synopsizing the action being performed in this state *AFTER*
        # possibly setting this state above.
        queue_status_text = SIMULATOR_STATE_TO_STATUS_TERSE[self.state]

        # Set the text of the label displaying this synopsis to this text.
        self._queue_status.setText(queue_status_text)
