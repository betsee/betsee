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
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.types import type_check  #, StrOrNoneTypes
# from betsee.guiexception import BetseePySideWindowException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState,
    SIMMER_STATE_TO_STATUS_TERSE,
    SIMMER_STATES_FLUID,
)

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
    _is_enqueued_modelling : BoolOrNoneTypes
       Tristate boolean signifying whether this phase has been enqueued for
       modelling or not, effectively acting as a substitute for a full-blown
       internal queue of all actions specific to this phase to be performed.
       Specifically, either:
       * ``None`` if this phase is currently **dequeued** (i.e., if the
         :meth:`dequeue_running` method has been called more recently than the
         :meth:`enqueue_running` method).
       * ``True`` if this phase is currently **enqueued** (i.e., if the
         :meth:`enqueue_running` method has been called more recently than the
         :meth:`dequeue_running` method) *and* this simulator phase was enqueued
         for modelling at that time.
       * ``False`` if this phase is currently enqueued *and* this simulator
         phase was enqueued for exporting at that time.
    _is_enqueued_exporting : BoolOrNoneTypes
       Tristate boolean signifying whether this phase has been enqueued for
       modelling or not. See the :attr:`_is_enqueued_modelling` boolean.
    _kind : SimPhaseKind
        Type of simulation phase controlled by this controller.
    _name : str
        Machine-readable alphabetic lowercase name of the type of simulation
        phase controlled by this controller (e.g., ``seed``, ``init``, ``sim``).

    Attributes (Private: Widgets)
    ----------
    _queue_modelling_lock : QCheckBox
        Checkbox toggling whether this phase is queueable for modelling.
    _queue_modelling : QCheckBox
        Checkbox toggling whether this phase is queued for modelling.
    _queue_exporting : QCheckBoxOrNoneTypes
        Checkbox toggling whether this phase is queued for exporting if this
        phase supports exporting *or* ``None`` otherwise. While most phases
        support exporting, some (e.g., the seed phase) do *not*.
    _status : QLabel
        Label synopsizing the current state of this phase.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator phase.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Dequeue this phase, thus setting instance variables to sane defaults.
        self.dequeue_running()

        # Nullify all remaining instance variables for safety.
        self._queue_modelling_lock = None
        self._queue_modelling = None
        self._queue_exporting = None
        self._kind = None
        self._name = None
        self._status = None


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Finalize this simulator phase's initialization, owned by the passed main
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
        simulator phase.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Log this initialization.
        logs.log_debug(
            'Sanitizing simulator phase "%s" state...', self._name)

        # Names of all instance variables of this main window yielding widgets
        # specific to this simulator phase.
        is_unqueueable_model_name = 'sim_run_queue_{}_model_lock'.format(
            self._name)
        is_queued_model_name = 'sim_run_queue_{}_model'.format(
            self._name)
        is_queued_export_name = 'sim_run_queue_{}_export'.format(
            self._name)
        status_name = 'sim_run_queue_{}_status'.format(self._name)

        # Classify mandatory widgets unconditionally defined for *ALL* phases.
        self._queue_modelling_lock = main_window.get_widget(
            widget_name=is_unqueueable_model_name)
        self._queue_modelling = main_window.get_widget(
            widget_name=is_queued_model_name)
        self._status = main_window.get_widget(
            widget_name=status_name)

        # Classify optional widgets conditionally defined for only some phases.
        self._queue_exporting = main_window.get_widget_or_none(
            widget_name=is_queued_export_name)


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulator phase.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Connect signals emitted by the checkbox queueing this phase for
        # modelling to corresponding slots, thus synchronizing the state of this
        # checkbox with both this phase and this phase's parent simulator.
        self._queue_modelling.toggled.connect(self.update_state)

        # If this phase is exportable, connect signals emitted by the checkbox
        # queueing this phase for exporting to corresponding slots as above.
        if self._queue_exporting is not None:
            self._queue_exporting.toggled.connect(self.update_state)

        # Connect signals emitted by widgets owned by this phase to slots
        # defined by this phase.
        self._queue_modelling_lock.toggled.connect(
            self._toggle_queue_modelling_lock)

        # Queue this phase to be modelled but *NOT* exported by default *AFTER*
        # connecting all signals emitted by this checkbox above.
        self._queue_modelling.setChecked(True)

    # ..................{ PROPERTIES ~ bool                  }..................
    @property
    def is_queued(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued for modelling
        and/or exporting.
        '''

        return self._is_queued_modelling or self._is_queued_exporting

    # ..................{ PROPERTIES ~ bool : private        }..................
    # This trivial getter exists only for orthogonality with the corresponding
    # non-trivial _is_queued_exporting() getter.
    @property
    def _is_queued_modelling(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued for modelling.
        '''

        return self._queue_modelling.isChecked()


    @property
    def _is_queued_exporting(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued for exporting.
        '''

        # Return true only if this phase is both...
        return (
            # Exportable.
            self._queue_exporting is not None and
            # Currently queued for exporting.
            self._queue_exporting.isChecked()
        )

    # ..................{ PROPERTIES ~ kind                  }..................
    @property
    def kind(self) -> SimPhaseKind:
        '''
        Type of simulation phase controlled by this controller.
        '''

        return self._kind


    @kind.setter
    def kind(self, kind: SimPhaseKind) -> None:
        '''
        Set the type of simulation phase controlled by this controller to the
        passed type.
        '''

        # Set this type and all variables directly dependent upon this type.
        self._kind = kind
        self._name = enums.get_member_name_lowercase(kind)

    # ..................{ PROPERTIES ~ name                  }..................
    # Read-only property.
    @property
    def name(self) -> str:
        '''
        Machine-readable alphabetic lowercase name of the type of simulation
        phase controlled by this controller (e.g., ``seed``, ``init``, ``sim``).
        '''

        return self._name

    # ..................{ SLOTS ~ bool                       }..................
    @Slot(bool)
    def _toggle_queue_modelling_lock(self, is_unqueueable_model: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling the checkable :class:`QToolButton` widget
        corresponding to the :attr:`_queue_modelling_lock` variable.

        Specifically, if:

        * This button is checked, this slot locks (i.e., disables) the
          :class:`QCheckBox` widget corresponding to the
          :attr:`_queue_modelling` variable.
        * This button is unchecked, this slot unlocks (i.e., enables) that
          :class:`QCheckBox` widget.

        Parameters
        ----------
        is_unqueueable_model : bool
            ``True`` only if this :class:`QToolButton` is currently checked.
        '''

        # One-liners for the greater glory of godly efficiency.
        self._queue_modelling.setEnabled(not is_unqueueable_model)

    # ..................{ QUEUERS                            }..................
    def enqueue_running(self) -> None:

        # Enqueue our superclass.
        super().enqueue_running()

        # Enqueue this phase by setting tristate booleans to either "True" or
        # "False" depending on the current state of corresponding checkboxes.
        self._is_enqueued_modelling = self._is_queued_modelling
        self._is_enqueued_exporting = self._is_queued_exporting


    def dequeue_running(self) -> None:

        # Dequeue our superclass.
        super().dequeue_running()

        # Dequeue this phase by resetting tristate booleans to sane defaults.
        self._is_enqueued_modelling = None
        self._is_enqueued_exporting = None


    #FIXME: Set the state of this simulator.
    #FIXME: Set the state of the currently running phase.
    def run_enqueued(self) -> None:

        #FIXME: Actually implement this condition.

        # If this phase is enqueued for modelling...
        if self._is_enqueued_modelling:
            pass

        # If this phase is enqueued for exporting...
        if self._is_enqueued_exporting:
            pass

    # ..................{ UPDATERS                           }..................
    def _update_state(self) -> None:

        # If the current state of this phase is fluid (i.e., freely replaceable
        # with any other state), set this state to whether or not this phase is
        # currently queued.
        if self.state in SIMMER_STATES_FLUID:
            self.state = (
                SimmerState.QUEUED if self.is_queued else SimmerState.UNQUEUED)
        # Else, the current state of this phase is fixed and hence *NOT*
        # replaceable with any other state. For safety, this state is preserved.


    def _update_widgets(self) -> None:

        # Text synopsizing the action being performed in this state *AFTER*
        # possibly setting this state above.
        status_text = SIMMER_STATE_TO_STATUS_TERSE[self.state]

        # Set the text of the label displaying this synopsis to this text.
        self._status.setText(status_text)
