#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
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

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Signal  #QObject, Slot
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
from betsee.gui.simtab.run.guisimrunstate import SimmerState
from betsee.util.widget.abc.control.guictlabc import QBetseeControllerABC

# ....................{ SUPERCLASSES                      }....................
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

    # ..................{ SIGNALS                           }..................
    state_changed = Signal(object, object)
    '''
    Signal passed the current and previous simulator states on each change to
    the state of this simulator controller, either due to user interaction or
    programmatic non-interaction.

    Caveats (Value)
    ----------
    **Note that the two passed states may be the same state.** This slot is
    unconditionally signalled on each attempt to assign this controller a new
    state, including those implicitly preserving the current state by
    reassigning this controller the same state. Why? Because slots connected to
    this signal expect to be called on each state assignment even if that
    assignment preserves that existing state. Why? Because the mere act of
    assignment signifies that lower-level metadata synopsizing this high-level
    state *may* have changed, despite this state *not* having changed.

    The canonical example is the total number of queued simulator phases. When
    the user queues any simulator phase *or* unqueues any simulator phase
    excluding the last queued phase, the proactor remains in the same queued
    state while the number of queued simulator phases changes. If the proactor
    did *not* unconditionally signal this slot, then:

    * The proactor would need to define a new signal and emit that signal on
      each change to the number of queued simulator phases.
    * The simulator would need to define a new slot and connect that slot to
      that signal to update its display of this number.

    Instead, this slot is unconditionally signalled.

    Caveats (Type)
    ----------
    **This signal should only be passed states of type :class:`SimmerState`,**
    despite accepting objects of arbitrary type. Ideally, this signal would be
    refactored to unambiguously accept objects of type :class:`SimmerState`.
    Sadly, doing so induces non-human-readable segmentation faults resembling:

    .. code::

        Fatal Python error: Segmentation fault

        Current thread 0x00007f2d83afd540 (most recent call first):
        File "./betsee/gui/simtab/run/guisimrunabc.py", line 63 in QBetseeSimmerStatefulABC
        File "./betsee/gui/simtab/run/guisimrunabc.py", line 48 in <module>
        File "<frozen importlib._bootstrap>", line 222 in _call_with_frames_removed
        File "<frozen importlib._bootstrap_external>", line 697 in exec_module
        File "<frozen importlib._bootstrap>", line 673 in _load_unlocked
        File "<frozen importlib._bootstrap>", line 957 in _find_and_load_unlocked
        File "<frozen importlib._bootstrap>", line 968 in _find_and_load
        File "./betsee/gui/simtab/run/guisimrunact.py", line 36 in <module>
        File "<frozen importlib._bootstrap>", line 222 in _call_with_frames_removed
        File "<frozen importlib._bootstrap_external>", line 697 in exec_module
        File "<frozen importlib._bootstrap>", line 673 in _load_unlocked
        File "<frozen importlib._bootstrap>", line 957 in _find_and_load_unlocked
        File "<frozen importlib._bootstrap>", line 968 in _find_and_load
        File "./betsee/gui/simtab/run/guisimrun.py", line 49 in <module>
        File "<frozen importlib._bootstrap>", line 222 in _call_with_frames_removed
        File "<frozen importlib._bootstrap_external>", line 697 in exec_module
        File "<frozen importlib._bootstrap>", line 673 in _load_unlocked
        File "<frozen importlib._bootstrap>", line 957 in _find_and_load_unlocked
        File "<frozen importlib._bootstrap>", line 968 in _find_and_load
        File "./betsee/gui/simtab/guisimtab.py", line 48 in __init__
        File "<string>", line 5 in func_type_checked
        File "./betsee/data/py/betsee_ui.py", line 1988 in setupUi
        File "./betsee/gui/window/guiwindow.py", line 184 in __init__
        File "<string>", line 25 in func_type_checked
        File "./betsee/gui/guimain.py", line 313 in _make_main_window
        File "./betsee/gui/guimain.py", line 276 in run
        File "./betsee/cli/guicli.py", line 240 in _do
        File "/home/leycec/py/betse/betse/util/py/pyprofile.py", line 130 in _profile_callable_none
        File "/home/leycec/py/betse/betse/util/py/pyprofile.py", line 114 in profile_callable
        File "<string>", line 65 in func_type_checked
        File "/home/leycec/py/betse/betse/util/cli/cliabc.py", line 180 in run
        File "<string>", line 15 in func_type_checked
        File "./betsee/__main__.py", line 98 in main
        File "/usr/bin/betsee", line 66 in <module>
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this stateful simulator controller.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Default this controller's state to the unqueued state.
        self._state = SimmerState.UNQUEUED

    # ..................{ PROPERTIES ~ state                }..................
    @property
    def state(self) -> SimmerState:
        '''
        Current state of this simulator controller, exactly analogous to the
        current state of a finite state automata.
        '''

        return self._state


    @state.setter
    @type_check
    def state(self, state: SimmerState) -> None:
        '''
        Set the current state of this simulator controller to the passed state
        *and* signal all slots connected to the :attr:`state_changed` of
        this state change.
        '''

        # New and old states to be passed to all slots connected to the
        # "state_changed" signal *BEFORE* re-assigning these states.
        state_new = state
        state_old = self._state

        # Set the current state of this simulator controller to this state.
        self._state = state_new

        # Update the current state of both this simulator controller and
        # widgets controlled by this controller given this state.
        self._update_state()

        # Signal all connected slots *AFTER* internally updating this state.
        self.state_changed.emit(state_new, state_old)

    # ..................{ EXCEPTIONS                        }..................
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
                'QBetseeSimmerStatefulABC',
                'Simulator controller not queued.'))

    # ..................{ SUBCLASS ~ properties             }..................
    # Abstract read-only properties required to be overridden by subclasses.

    @abstractproperty
    def is_queued(self) -> bool:
        '''
        ``True`` only if this stateful simulator controller is currently queued
        for modelling and/or exporting one or more simulator phases.
        '''

        pass

    # ..................{ SUBCLASS ~ methods                }..................
    # Concrete methods intended (but *NOT* required) to be overridden by
    # subclasses.

    def _update_state(self) -> None:
        '''
        Update the internal state of this stateful simulator controller and the
        contents of widgets controlled by this controller to reflect the
        current external state of this controller.

        The :meth:`state` setter property method internally calls this method
        to perform subclass-specific business logic on either the user
        interactively *or* the codebase programmatically interacting with any
        widget relevant to the current state of this controller (e.g., a
        checkbox queueing a simulation phase for exporting).

        Design
        ----------
        The default implementation of this method reduces to a noop and is thus
        intended (but *not* required) to be overridden by subclasses requiring
        subclass-specific business logic to be performed when this controller's
        :meth:`state` property is set. Overriding setter property methods in a
        manner internally calling the superclass method is highly non-trivial;
        hence, the :meth:`state` setter property method internally calls this
        method instead.
        '''

        pass
