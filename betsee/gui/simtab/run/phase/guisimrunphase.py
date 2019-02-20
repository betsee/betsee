#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator phase** (i.e., simulation phase to be queued for
modelling and/or exporting by this simulator) functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QObject, Signal, Slot  # QCoreApplication,
from betse.science.enum.enumphase import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.decorator.decmemo import property_cached
from betse.util.type.types import type_check  #, CallableTypes
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.gui.simtab.run.guisimrunenum import SimmerState
from betsee.gui.simtab.run.guisimrunstate import (
    SIMMER_STATE_TO_PHASE_STATUS,
    SIMMER_STATES_FROM_FLUID,
)
from betsee.gui.window.guimainwindow import QBetseeMainWindow

# ....................{ SUPERCLASSES                      }....................
class QBetseeSimmerPhase(QBetseeSimmerStatefulABC):
    '''
    **Simulator phase controller** (i.e., :mod:`PySide2`-based object wrapping
    a simulator phase to be queued for modelling and/or exporting by this
    simulator).

    This controller maintains all state required to interactively manage this
    simulator phase.

    Attributes (Private: Non-widgets)
    ----------
    _kind : SimPhaseKind
        Type of simulation phase controlled by this controller.

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

    # ..................{ SIGNALS                           }..................
    queue_changed = Signal(QObject)
    '''
    Signal emitted by the :meth:`_toggle_queue_subkind` slot immediately after
    changing the state of this simulator phase to be either
    :attr:`SimmerState.QUEUED` or :attr:`SimmerState.UNQUEUED`, passed this
    simulator phase itself.

    This signal enables the parent simulator proactor to respond to user
    requests to enqueue or dequeue any child simulator phase, which are
    sufficiently unique events to warrant special-case handling.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator phase.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        self._kind = None
        self._queue_modelling_lock = None
        self._queue_modelling = None
        self._queue_exporting = None
        self._status = None


    @type_check
    def init(
        self,
        main_window: QBetseeMainWindow,
        kind: SimPhaseKind,
    ) -> None:
        '''
        Finalize the initialization of this simulator phase, owned by the
        passed main window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulator.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        kind : SimPhaseKind:
            Type of simulation phase controlled by this controller.
        '''

        # Initialize our superclass with the passed window.
        super().init(main_window)

        # Classify all remaining passed parameters.
        self._kind = kind

        # Log this initialization *AFTER* classifying these parameters, as
        # required by the "name" property embedded in this log message.
        logs.log_debug(
            'Sanitizing simulator phase "%s" state...', self.name)

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
            Initialized application-specific parent :class:`QMainWindow`
            widget.
        '''

        # Names of all instance variables of this main window yielding widgets
        # specific to this simulator phase.
        is_unqueueable_model_name = 'sim_run_queue_{}_model_lock'.format(
            self.name)
        is_queued_model_name  = 'sim_run_queue_{}_model' .format(self.name)
        is_queued_export_name = 'sim_run_queue_{}_export'.format(self.name)
        status_name           = 'sim_run_queue_{}_status'.format(self.name)

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
            Initialized application-specific parent :class:`QMainWindow`
            widget.
        '''

        # Connect signals emitted by the checkbox queueing this phase for
        # modelling to corresponding slots, thus synchronizing the state of
        # this checkbox with both this phase and this phase's parent simulator.
        self._queue_modelling.toggled.connect(self._toggle_queue_subkind)

        # If this phase is exportable, connect signals emitted by the checkbox
        # queueing this phase for exporting to corresponding slots as above.
        if self._queue_exporting is not None:
            self._queue_exporting.toggled.connect(self._toggle_queue_subkind)

        # Connect signals emitted by widgets owned by this phase to slots
        # defined by this phase.
        self._queue_modelling_lock.toggled.connect(
            self._toggle_queue_modelling_lock)

        # Queue this phase to be modelled but *NOT* exported by default *AFTER*
        # connecting all signals emitted by this checkbox above.
        self._queue_modelling.setChecked(True)

    # ..................{ PROPERTIES ~ bool                 }..................
    # Read-only boolean properties.

    @property
    def is_queued(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued (i.e., for
        modelling and/or exporting).
        '''

        return self.is_queued_modelling or self.is_queued_exporting


    # This trivial getter exists only for orthogonality with the corresponding
    # non-trivial is_queued_exporting() getter.
    @property
    def is_queued_modelling(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued for
        modelling.
        '''

        return self._queue_modelling.isChecked()


    @property
    def is_queued_exporting(self) -> bool:
        '''
        ``True`` only if this simulator phase is currently queued for
        exporting.
        '''

        # Return true only if this phase is both...
        return (
            # Exportable.
            self._queue_exporting is not None and
            # Currently queued for exporting.
            self._queue_exporting.isChecked()
        )

    # ..................{ PROPERTIES ~ non-bool             }..................
    # Read-only non-boolean properties.

    @property
    def kind(self) -> SimPhaseKind:
        '''
        Type of simulation phase controlled by this controller.
        '''

        return self._kind


    @property_cached
    def name(self) -> str:
        '''
        Machine-readable alphabetic lowercase name of the type of simulation
        phase controlled by this controller (e.g., ``seed``, ``init``).
        '''

        return enums.get_member_name_lowercase(self._kind)

    # ..................{ SLOTS                             }..................
    @Slot(bool)
    def _toggle_queue_subkind(self, is_queued: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically toggling the :class:`QCheckBox` widget corresponding
        to either the :attr:`_queue_modelling` *or* :attr:`_queue_exporting`
        variables.

        If this slot changes the state of this simulator phase to either
        :attr:`SimmerState.QUEUED` or :attr:`SimmerState.UNQUEUED`, this slot
        notifies interested parties of this fact by signalling the
        :attr:`queue_changed` with this simulator phase.

        Parameters
        ----------
        is_queued : bool
            ``True`` only if this :class:`QCheckBox` is currently checked.
        '''

        # Log this action.
        logs.log_debug(
            'Enqueueing simulator phase "%s"...' if is_queued else
            'Dequeueing simulator phase "%s"...', self.name)

        # If the current state of this phase is fluid (i.e., freely replaceable
        # with any other state)...
        if self.state in SIMMER_STATES_FROM_FLUID:
            # Reduce this state to whether this phase is queued or not.
            self.state = (
                SimmerState.QUEUED if self.is_queued else SimmerState.UNQUEUED)

            # Update the proactor's state to reflect this phase's state.
            self.queue_changed.emit(self)
        # Else, the current state of this phase is fixed and hence *NOT*
        # replaceable with any other state. For safety, this state is preserved
        # as is.
        #
        # Note that setting the "state" property above implicitly calls the
        # _update_state() method, which thus need (and indeed should) *NOT* be
        # explicitly recalled here. While technically safe, doing so would
        # nonetheless incur a senseless performance penalty.


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

        # One-liners for the greater glory of god-like efficiency.
        self._queue_modelling.setEnabled(not is_unqueueable_model)

    # ..................{ UPDATERS                          }..................
    def _update_state(self) -> None:

        # Text synopsizing the action being performed in this state *AFTER*
        # possibly setting this state above.
        status_text = SIMMER_STATE_TO_PHASE_STATUS[self.state]

        # Set the text of the label displaying this synopsis to this text.
        self._status.setText(status_text)
