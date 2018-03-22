#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

#FIXME: Refactor this to leverage Qt's existing "QStateMachine" framework. Had
#we known about the existence of this framework, we likely wouldn't have
#implemented the cumbersome "QBetseeSimmerStatefulABC" API but instead leveraged
#the existing quite elegant "QStateMachine" API. Sadly, we know which of these
#two roads was taken. Unfortunately, refactoring this subpackage from the former
#to latter will probably be highly non-trivial -- but ultimately essential.
#
#There exist many, many reasons to transition to the "QStateMachine" API,
#including:
#
#* Sanity. We really just wanted a finite state machine (FSM). Now, we can. In
#  theory, an FSM-based implementation should be significantly saner.
#* Properties. The "QStateMachine" API permits the properties of arbitrary
#  "QObject" instances (like, say, whether or not a given "QPushButton" is
#  enabled or disabled) to be trivially set on transitioning to and from a
#  state. In theory, leveraging this should simplify our life with respect to
#  updating widget states.
#* History. The "QStateMachine" API provides the concept of "history states,"
#  which would permit the current state of the simulator to be saved and
#  restored (e.g., across desktop sessions). Probably essential, at some point.
#* Animations. The "QStateMachine" API provides the concept of "transition
#  animations," permitting the properties of arbitrary "QObject" instances to be
#  animated between... seemlessly. Nice, but hardly essential.
#
#Fortunately, Qt's documentation for this API is phenomenal. See the article
#entitled "The State Machine Framework." It's a surprisingly stunning read.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
from abc import abstractmethod
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunstate import SimmerState
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimmerStatefulABC(QBetseeControllerABC):
    '''
    Abstract base class of all **stateful simulator controller** (i.e.,
    :mod:`PySide2`-based object controlling the internal and possibly external
    state of some aspect of the simulator) subclasses.

    Attributes (Private: Non-widgets)
    ----------
    _state : SimmerState
        Current state of this simulator controller, exactly analogous to the
        current state of a finite state automata. For safety, this variable
        should *only* be set by the public :meth:`state` setter.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this stateful simulator controller.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Default this controller's state to the unqueued state.
        self._state = SimmerState.UNQUEUED

        # Nullify all remaining instance variables for safety.
        # self._state = None

    # ..................{ PROPERTIES ~ bool                  }..................
    @abstractproperty
    def is_queued(self) -> bool:
        '''
        ``True`` only if this stateful simulator controller is currently queued
        for modelling and/or exporting one or more simulator phases.
        '''

        pass

    # ..................{ PROPERTIES ~ state                 }..................
    @property
    def state(self) -> SimmerState:
        '''
        Current state of this simulator controller, exactly analogous to the
        current state of a finite state automata.
        '''

        return self._state


    @state.setter
    def state(self, state: SimmerState) -> None:
        '''
        Set the current state of this simulator controller to the passed state
        *and* signal all slots connected to the :attr:`set_state_signal` of this
        state change.
        '''

        # Set the current state of this simulator controller to this state.
        self._state = state

        # Signal all connected slots *AFTER* setting this state.
        self.set_state_signal.emit(self)

    # ..................{ SIGNALS                            }..................
    set_state_signal = Signal(QObject)
    '''
    Signal passed this simulator controller on each change to the current state
    of that phase, either due to user interaction or programmatic
    non-interaction.
    '''

    # ..................{ EXCEPTIONS                         }..................
    def _die_unless_queued(self) -> None:
        '''
        Raise an exception unless this stateful simulator controller is
        currently queued for modelling and/or exporting one or more simulator
        phases.

        Equivalently, this method raises an exception if *no* such phase is
        currently queued.

        See Also
        ----------
        :meth:`is_queued`
            Further details.
        '''

        if not self.is_queued:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmer', 'Simulator currently running.'))

    # ..................{ SLOTS                              }..................
    @Slot()
    def update_state(self) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically interacting with any widget relevant to the current
        state of this stateful simulator controller, including phase-specific
        checkboxes queueing that simulator phase for modelling and/or exporting.
        '''

        # Update the state of this controller to reflect these changes.
        self._update_state()

        # Update the state of controller widgets to reflect these changes
        # *AFTER* updating the state of this controller, as the latter typically
        # depends upon the former.
        self._update_widgets()

    # ..................{ SLOTS ~ updaters                   }..................
    def _update_state(self) -> None:
        '''
        Update the current public state of this stateful simulator controller
        (i.e., the :meth:`state` property) to reflect its current private state
        (e.g., child objects, widgets, and data structures).
        '''

        pass


    @abstractmethod
    def _update_widgets(self) -> None:
        '''
        Update the contents of all widgets controlled by this stateful simulator
        controller to reflect this state.
        '''

        pass

    # ..................{ QUEUERS                            }..................
    def enqueue_running(self) -> None:
        '''
        Enqueue (i.e., append onto this controller's internal queue) all actions
        performed by a subsequent call to the :meth:`run_enqueued` method.

        Raises
        ----------
        BetseeSimmerException
            If this controller is *not* currently queued.
        '''

        # If this controller is *NOT* currently queued, raise an exception.
        self._die_unless_queued()


    def dequeue_running(self) -> None:
        '''
        Dequeue (i.e., remove from this controller's internal queue) all actions
        enqueued by a prior call to the :meth:`enqueue_running` method.
        '''

        pass


    @abstractmethod
    def run_enqueued(self) -> None:
        '''
        Perform each action enqueued by a prior call to the
        :meth:`enqueue_running` method (in the order in which these actions were
        enqueued).
        '''

        pass
