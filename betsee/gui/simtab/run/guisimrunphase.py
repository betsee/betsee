#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator phase** (i.e., simulation phase to be queued for modelling
and/or exporting by this simulator) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot  # QCoreApplication, Signal,
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.types import type_check  #, StrOrNoneTypes
# from betsee.guiexception import BetseePySideWindowException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.gui.simtab.run.guisimrunstate import (
    SIMULATOR_STATE_TO_STATUS_TERSE,)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimmerPhase(QBetseeSimmerStatefulABC):
    '''
    Low-level **simulator phase** (i.e., :mod:`PySide2`-based object wrapping a
    simulation phase to be queued for modelling and/or exporting by this
    simulator).

    This simulator phase maintains all state required to interactively manage
    this simulation phase, including:

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
    _status : QLabel
        Label synopsizing the current state of this phase.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator phase.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        self._is_unqueueable_model = None
        self._is_queued_model = None
        self._is_queued_export = None
        self._phase_kind = None
        self._phase_name = None
        self._status = None


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

        # Initialize all superclass widgets.
        super()._init_widgets(main_window)

        # Log this initialization.
        logs.log_debug(
            'Sanitizing simulator phase "%s" state...', self._phase_name)

        # Names of all instance variables of this main window yielding widgets
        # specific to this simulator phase.
        is_unqueueable_model_name = 'sim_run_queue_{}_model_lock'.format(
            self._phase_name)
        is_queued_model_name = 'sim_run_queue_{}_model'.format(
            self._phase_name)
        is_queued_export_name = 'sim_run_queue_{}_export'.format(
            self._phase_name)
        status_name = 'sim_run_queue_{}_status'.format(self._phase_name)

        # Classify mandatory widgets unconditionally defined for *ALL* phases.
        self._is_unqueueable_model = main_window.get_widget(
            widget_name=is_unqueueable_model_name)
        self._is_queued_model = main_window.get_widget(
            widget_name=is_queued_model_name)
        self._status = main_window.get_widget(
            widget_name=status_name)

        # Classify optional widgets conditionally defined for only some phases.
        self._is_queued_export = main_window.get_widget_or_none(
            widget_name=is_queued_export_name)

        # Queue this phase to be modelled but *NOT* exported by default.
        self._is_queued_model.setChecked(True)


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulator phase.
        '''

        # Initialize all superclass connections.
        super()._init_connections(main_window)

        # Parent slot updating the simulator player to reflect simulator state.
        player = main_window.sim_tab.simmer

        # Connect signals emitted by the checkbox queueing this phase for
        # modelling to corresponding slots, thus synchronizing the state of this
        # checkbox with both this phase and this phase's parent simulator.
        self._is_queued_model.toggled.connect(player.update_state)
        self._is_queued_model.toggled.connect(self.update_state)

        # If this phase is exportable, connect signals emitted by the checkbox
        # queueing this phase for exporting to corresponding slots as above.
        if self._is_queued_export is not None:
            self._is_queued_export.toggled.connect(player.update_state)
            self._is_queued_export.toggled.connect(self.update_state)

        # Connect signals emitted by widgets owned by this phase to slots
        # defined by this phase.
        self._is_unqueueable_model.toggled.connect(
            self._toggle_is_unqueueable_model)

    # ..................{ PROPERTIES ~ bool                  }..................
    @property
    def is_queued(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued for modelling
        and/or exporting.
        '''

        # Return true only if this phase is either...
        return (
            # Queued for modelling.
            self._is_queued_model.isChecked() or
            # Exportable *AND* queued for exporting.
            (self._is_queued_export is not None and
             self._is_queued_export.isChecked())
        )

    # ..................{ PROPERTIES ~ kind                  }..................
    @property
    def kind(self) -> SimPhaseKind:
        '''
        Type of simulation phase controlled by this controller.
        '''

        return self._phase_kind


    @kind.setter
    def kind(self, kind: SimPhaseKind) -> None:
        '''
        Set the type of simulation phase controlled by this controller to the
        passed type.
        '''

        # Set this type and all variables directly dependent upon this type.
        self._phase_kind = kind
        self._phase_name = enums.get_member_name_lowercase(kind)

    # ..................{ SLOTS ~ bool                       }..................
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

        # Text synopsizing the action being performed in this state *AFTER*
        # possibly setting this state above.
        status_text = SIMULATOR_STATE_TO_STATUS_TERSE[self.state]

        # Set the text of the label displaying this synopsis to this text.
        self._status.setText(status_text)
