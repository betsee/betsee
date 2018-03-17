#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot  # QCoreApplication, Signal
from abc import abstractmethod
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunstate import (
    SimulatorState, SIMULATOR_STATES_FLUID)
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimmerStatefulABC(QBetseeControllerABC):
    '''
    Abstract base class of all **stateful simulator controller** (i.e.,
    :mod:`PySide2`-based object controlling the internal and possibly external
    state of some aspect of the simulator) subclasses.

    Attributes (Private: Non-widgets)
    ----------
    state : SimulatorState
        Current state of this simulator controller, exactly analogous to the
        current state of a finite state automata.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this stateful simulator controller.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Default this controller's state to the unqueued state.
        self.state = SimulatorState.UNQUEUED


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Finalize this stateful simulator controller's initialization, owned by
        the passed main window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulator.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child widgets
        (e.g., actions) of this window may be retained, however.

        Caveats
        ----------
        For safety, subclasses should either:

        * Avoid redefining this method. Instead, subclasses should redefine the
          :meth:`_init_widgets` and/or :meth:`_init_connections` methods.
        * Redefine this method to call this superclass method but *not* the
          :meth:`_init_widgets` and/or :meth:`_init_connections` methods, which
          this superclass method already calls on behalf of subclasses.

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
        stateful simulator controller.

        Subclasses should reimplement this method in a manner calling this
        superclass implementation and then handling subclass-specific widgets.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        pass


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state concerns
        this stateful simulator controller.

        Subclasses should reimplement this method in a manner calling this
        superclass implementation and then handling subclass-specific
        connections.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Update this controller's state to reflect changes performed by the
        # prior _init_widgets() call. Ideally, this logic would be performed in
        # that rather than this call. Due to timing issues, however, doing so
        # would require subclasses to either not call the superclass
        # _init_widgets() method *OR* to call that method last; both cases
        # impose non-intuitive design constraints on subclasses, which is bad.
        # While non-ideal, performing this logic here circumvents such issues.
        self.update_state()

    # ..................{ PROPERTIES ~ bool                  }..................
    @abstractproperty
    def is_queued(self) -> bool:
        '''
        ``True`` only if this stateful simulator controller is currently queued
        for modelling and/or exporting one or more simulator phases.
        '''

        pass

    # ..................{ SLOTS ~ public                     }..................
    @Slot()
    def update_state(self) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically interacting with any widget relevant to the current
        state of this stateful simulator controller, including phase-specific
        checkboxes queueing that simulator phase for modelling and/or exporting.
        '''

        # If the current state of this controller is fluid (i.e., replaceable
        # with any other state)...
        if self.state in SIMULATOR_STATES_FLUID:
            # If this controller is queued, set this state accordingly.
            if self.is_queued:
                self.state = SimulatorState.QUEUED
            # Else, this controller is unqueued. Set this state accordingly.
            else:
                self.state = SimulatorState.UNQUEUED
        # Else, the current state of this controller is fixed and hence *NOT*
        # replaceable with any other state. For safety, this state is preserved.

        # Update the state of controller widgets to reflect these changes.
        self._update_widgets()

    # ..................{ UPDATERS                           }..................
    @abstractmethod
    def _update_widgets(self) -> None:
        '''
        Update the contents of all widgets controlled by this stateful simulator
        controller to reflect this state.
        '''

        pass
