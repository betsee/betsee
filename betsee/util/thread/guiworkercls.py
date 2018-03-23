#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **worker** (i.e., thread-safe object implementing generically
startable, pausable, resumable, and haltable business logic in a multithreaded
manner intended to be moved to the thread encapsulated by a :class:`QThread`
object) classes.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
# from betse.util.io.log import logs
from betse.util.type.enums import make_enum
# from betse.util.type.types import type_check
# from betsee.guiexception import BetseePySideThreadException
from betsee.util.thread import guithread

# ....................{ ENUMERATIONS                       }....................
QBetseeWorkerState = make_enum(
    class_name='QBetseeWorkerState',
    member_names=('IDLE', 'WORKING', 'PAUSED',))
'''
Enumeration of all supported types of **worker state** (i.e., mutually
exclusive high-level execution state of a :class:`QBetseeWorkerABC` instance,
analogous to a state in a finite state automata).

Attributes
----------
IDLE : enum
    Idle state, implying this worker to be **idle** (i.e., neither working nor
    paused while working). From this state, this worker may freely transition to
    the working but *not* paused state.
WORKING : enum
    Working state, implying this worker to be **working** (i.e., performing
    subclass-specific business logic, typically expected to be long-running).
    From this state, this worker may freely transition to *any* other state.
PAUSED : enum
    Paused state, implying this worker to be **paused** (i.e., temporarily
    halted from performing subclass-specific business logic). From this state,
    this worker may freely transition to *any* other state. Transitioning from
    this state to the working state is also referred to as "resuming."
'''

# ....................{ SUPERCLASS                         }....................
class QBetseeWorkerABC(QObject):
    '''
    Low-level **worker** (i.e., thread-safe object implementing generically
    startable, pausable, resumable, and haltable business logic in a
    multithreaded manner intended to be moved to the thread encapsulated by a
    :class:`QThread` object).

    Attributes
    ----------
    _state : QBetseeWorkerState
        Current execution state of this worker. For thread-safety, this state
        should *not* be externally accessed by objects residing in other
        threads.

    See Also
    ----------
    https://codereview.stackexchange.com/a/173258/124625
        StackOverflow answer strongly inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this worker.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Default this worker's initial state to the idle state.
        self._state = QBetseeWorkerState.IDLE

        # Garbage collect all child objects of this parent worker *AFTER* this
        # worker gracefully (i.e., successfully) terminates.
        self.finished.connect(self.deleteLater)

    # ..................{ SLOTS                              }..................
    @Slot()
    def pause(self) -> None:
        '''
        Slot pausing all work performed by this worker.

        This slot temporarily halts this work in a thread-safe manner safely
        resumable at any time (e.g., by emitting a signal connected to the
        :meth:`resume` slot).

        If this worker is *not* currently working, this slot silently reduces to
        a noop. While raising a fatal exception in this edge case might
        superficially appear to be reasonable, the queued nature of signal-slot
        connections introduces unavoidable delays in event delivery and hence
        slot execution. In particular, raising an exception would introduce a
        race condition between the time that a user interactively requests a
        working worker to be paused and that worker's completion of its work.
        '''

        # Event dispatcher associated with the current thread of execution,
        # obtained *BEFORE* modifying the state of this worker to raise an
        # exception in the event that this thread has no such dispatcher.
        event_dispatcher = guithread.get_current_event_dispatcher()

        # If this worker is *NOT* currently working, safely reduce to a noop.
        if self._state != QBetseeWorkerState.WORKING:
            return
        # Else, this worker is currently working.

        # Change this worker's state to paused.
        self._state = QBetseeWorkerState.PAUSED

        # While this worker's state is paused, wait for the resume() slot to be
        # externally signalled by another object (typically in another thread).
        while self._state == QBetseeWorkerState.PAUSED:
            guithread.wait_for_events_if_none(event_dispatcher)
