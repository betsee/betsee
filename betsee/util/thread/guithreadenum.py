#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **thread enumeration** (e.g., :class:`enum.Enum` subclass describing
different types of multithreading behaviour) functionality.
'''

# ....................{ IMPORTS                           }....................
from betse.util.type.enums import make_enum

# ....................{ ENUMERATIONS                      }....................
ThreadWorkerState = make_enum(
    class_name='ThreadWorkerState',
    member_names=('IDLE', 'RUNNING', 'PAUSED', 'DELETED',))
'''
Enumeration of all supported types of **multithreaded worker state** (i.e.,
mutually exclusive execution state of a :class:`QObject`- or
:class:`QRunnable`-derived worker object, analogous to a state in a finite
state automata).

Attributes
----------
IDLE : enum
    Idle state, implying this worker to be **idle** (i.e., neither working nor
    paused while working). From this state, this worker may freely transition
    to the working but *not* paused state.
RUNNING : enum
    Running state, implying this worker to be **running** (i.e., performing
    subclass-specific business logic, typically expected to be long-running).
    From this state, this worker may freely transition to *any* other state.
PAUSED : enum
    Paused state, implying this worker to be **paused** (i.e., temporarily
    halted from performing subclass-specific business logic). From this state,
    this worker may freely transition to *any* other state. Transitioning from
    this state to the running state is also referred to as "resuming."
DELETED : enum
    Deleted state, implying this worker to be scheduled for deletion by a
    recent call to a ``delete_later`` method defined on this worker (e.g., the
    :meth:`QBetseeThreadPoolWorker.delete_later` method). From this state, this
    worker cannot freely transition to *any* other state.
'''
