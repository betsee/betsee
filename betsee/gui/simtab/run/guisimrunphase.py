#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator phase** (i.e., simulation phase to be queued for modelling
and/or exporting by this simulator) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Signal, Slot  # QCoreApplication,
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
class QBetseeSimmerPhase(QBetseeControllerABC):
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

        # Default this phase to the unqueued state.
        self.state = SimulatorState.UNQUEUED

        # Nullify all remaining instance variables for safety.
        self._is_unqueueable_model = None
        self._is_queued_model = None
        self._is_queued_export = None
        self._phase_kind = None
        self._phase_name = None
        self._status = None


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

        # Update the state of phase widgets to reflect these changes.
        self._update_state()


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulator phase.
        '''

        # Parent slot updating the simulator player to reflect simulator state.
        player = main_window.sim_tab.simmer

        # Connect signals emitted by the checkbox queueing this phase for
        # modelling to corresponding slots, thus synchronizing the state of this
        # checkbox with both this phase and this phase's parent simulator.
        self._is_queued_model.toggled.connect(player.update_state)
        self._is_queued_model.toggled.connect(self._update_state)

        # If this phase is exportable, connect signals emitted by the checkbox
        # queueing this phase for exporting to corresponding slots as above.
        if self._is_queued_export is not None:
            self._is_queued_export.toggled.connect(player.update_state)
            self._is_queued_export.toggled.connect(self._update_state)

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

    # ..................{ SLOTS                              }..................
    def _update_state(self) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically interacting with any widget relevant to the current
        state of this simulator phase, including phase-specific checkboxes
        queueing this phase for modelling and/or exporting.

        This slot internally updates all widgets owned by this phase to reflect
        the current state of this phase. Notably, this slot updates the text
        displayed by the :attr:`_status` label, tersely synopsizing this state.
        '''

        #FIXME: Insufficient. We also need to update the state of the simulator
        #to reflect this state change. Unfortunately, doing so is complicated
        #by the fact that we entangled the parent controller owning this child
        #controller with the simulator player. To implement this sanely, we'll
        #probably need to disentangle the two; specifically:
        #
        #* Define a new "guisimrunplayer" submodule.
        #* Define a new "QBetseeSimmerPlayer" class in that submodule.
        #* Shift all player-specific functionality in the parent "QBetseeSimmer"
        #  controller into that new class.
        #* Instantiate that new class in the parent "QBetseeSimmer" controller.
        #* Pass that instance to the init() method of this class as a new
        #  "player" parameter. Since the player does *NOT* own this phase, the
        #  two objects may freely classify variables referring to each other and
        #  hence call methods of each other without concern for circularity.
        #
        #Technically, none of the above is strictly required. The "guisimrun"
        #submodule is growing increasingly long in the tooth, however. To avoid
        #circularity issues in the future *AND* to compartmentalize logic, it
        #would be advisable to implement the above as soon as time allows.
        #FIXME: Indeed, if we implement the above, we might even go a step
        #further by abstracting out the concept of a "state" into a parent
        #"QBetseeSimmerControllerABC" superclass providing:
        #
        #* A public "state" instance variable.
        #* A public update_state() slot performing *ONLY* the following
        #  state-specific logic.
        #
        #Assuming we do so, such a superclass should be added to a new
        #"guisimrunabc" submodule. Trivial, really; only time-consuming.

        # If the current state of this phase is fluid (i.e., freely replaceable
        # with any other state)...
        if self.state in SIMULATOR_STATES_FLUID:
            # If this phase is queued, set this state accordingly.
            if self.is_queued:
                self.state = SimulatorState.QUEUED
            # Else, this phase is unqueued. Set this state accordingly.
            else:
                self.state = SimulatorState.UNQUEUED
        # Else, the current state of this phase is fixed and hence *NOT* freely
        # replaceable with any other state. For safety, this state is preserved.

        # Update the terse status of this phase.
        self._update_status()

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
    def _update_status(self) -> None:
        '''
        Update the text displayed by the :attr:`_status` label, tersely
        synopsizing the current state of this simulator phase.
        '''

        # Text synopsizing the action being performed in this state *AFTER*
        # possibly setting this state above.
        status_text = SIMULATOR_STATE_TO_STATUS_TERSE[self.state]

        # Set the text of the label displaying this synopsis to this text.
        self._status.setText(status_text)
