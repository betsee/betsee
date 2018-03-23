#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **multithreading** (i.e., platform-portable, pure-Qt,
:class:`QThread`-based parallelization implemented external to Python and hence
Python's restrictive Global Interpreter Lock (GIL)) facilities.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import (
    QAbstractEventDispatcher, QCoreApplication, QEventLoop, QThread)
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideThreadException
from betsee.util.type.guitype import (
    QAbstractEventDispatcherOrNoneTypes, QThreadOrNoneTypes)

# ....................{ GETTERS                            }....................
def get_event_dispatcher(
    thread: QThreadOrNoneTypes = None) -> QAbstractEventDispatcher:
    '''
    Wrapper encapsulating the **event dispatcher** (i.e., Qt-specific
    object propagating events received from the underlying window system to the
    passed thread of execution) if this thread has an event dispatcher *or*
    raise an exception otherwise (i.e., if this thread has no event dispatcher).

    Parameters
    ----------
    thread : QThreadOrNoneTypes
        Thread to retrieve this event dispatcher from. Defaults to ``None``, in
        which case the current thread of execution is defaulted to.

    Returns
    ----------
    QAbstractEventDispatcher
        Wrapper encapsulating the event dispatcher for this thread.

    Raises
    ----------
    BetseePySideThreadException
        If the current thread of execution has *no* event dispatcher (i.e., if
        the :meth:`QThread.exec` method has been called more recently than the
        :meth:`QThread.exit` or :meth:`QThread.quit` methods for this thread).
    '''

    # Default this thread if unpassed to the current thread of execution.
    if thread is None:
        thread = get_current_thread()

    # Event dispatcher for this thread if any *OR* 0 otherwise.
    event_dispatcher = thread.eventDispatcher()

    # If this thread has *NO* event dispatcher, raise an exception.
    if not event_dispatcher:
        raise BetseePySideThreadException(QCoreApplication.translate(
            'get_current_event_dispatcher',
            'No event dispatcher running for thread "{}".'.format(
                thread.objectName())))
    # Else, this thread has an event dispatcher.

    # Return this event dispatcher.
    return event_dispatcher

# ....................{ GETTERS ~ current                  }....................
def get_current_thread() -> QThread:
    '''
    Wrapper encapsulating the **current thread** (i.e., Qt-specific thread of
    execution responsible for the call to this function).
    '''

    return QThread.currentThread()


def get_current_event_dispatcher() -> QAbstractEventDispatcher:
    '''
    Wrapper encapsulating the event dispatcher for the current thread of
    execution if this thread has an event dispatcher *or* raise an exception
    otherwise (i.e., if this thread has no event dispatcher).

    Returns
    ----------
    QAbstractEventDispatcher
        Wrapper encapsulating the event dispatcher for the current thread.

    Raises
    ----------
    BetseePySideThreadException
        If this thread has *no* event dispatcher.

    See Also
    ----------
    :func:`get_event_dispatcher`
        Further details.
    '''

    # Current thread of execution.
    thread = get_current_thread()

    # Return the event dispatcher for this thread.
    return get_event_dispatcher(thread)

# ....................{ PROCESSORS                         }....................
@type_check
def process_events(
    event_dispatcher: QAbstractEventDispatcherOrNoneTypes = None) -> (
    QAbstractEventDispatcher):
    '''
    Process all pending events currently queued with the thread of execution
    associated with the passed event dispatcher.

    This function unconditionally processes *all* such events, including both
    outgoing signals emitted by *and* incoming slots signalled on all workers
    currently running in this thread.

    Caveats
    ----------
    Avoid manually calling the static :func:`QCoreApplication.processEvents`
    function to process events for the current thread of execution. If this
    thread has *no* event dispatcher, this function silently and hence unsafely
    ignores all pending :class:`DeferredDelete` events currently queued for this
    thread. Since numerous standard widgets (e.g., :class:`QToolTip`) require
    these events to be processed in a timely manner, ignoring these events
    fundamentally disrupts all widget functionality.

    Parameters
    ----------
    event_dispatcher : QAbstractEventDispatcherOrNoneTypes
        Event dispatcher to process events for. Defaults to ``None``, in which
        case either:
        * If the current thread of execution has an event dispatcher, events are
          processed for this dispatcher.
        * Else, an exception is raised.
    '''

    # Default this event dispatcher if unpassed to that associated with the
    # current thread of execution.
    if event_dispatcher is None:
        event_dispatcher = get_current_event_dispatcher()

    # Process all pending events currently queued with this dispatcher.
    event_dispatcher.processEvents(QEventLoop.AllEvents)


#FIXME: Explicitly raise an exception if this event dispatcher is the main event
#dispatcher (i.e., event dispatcher running the main GUI event loop).
@type_check
def wait_for_events_if_none(
    event_dispatcher: QAbstractEventDispatcherOrNoneTypes = None) -> (
    QAbstractEventDispatcher):
    '''
    Indefinitely block the thread of execution associated with the passed
    event dispatcher until *another* thread of execution posts a new event to
    the former thread if *no* pending events are currently queued with this
    thread *or* safely return immediately otherwise (i.e., if one or more
    pending events are currently queued with this thread).

    This function is intended to be called *only* from the slots of workers
    currently running in the thread of execution associated with the passed
    event dispatcher. In this case, this function call gracefully returns when
    another object in another thread of execution emits a signal connected to a
    slot of such a worker.

    Caveats
    ----------
    **Never call this function from an object owned by the main event-handling
    thread.** Doing so effectively blocks the application GUI managed by this
    thread. Instead, only call this function from a worker guaranteed to be
    running in this thread.

    Parameters
    ----------
    event_dispatcher : QAbstractEventDispatcherOrNoneTypes
        Event dispatcher to process events for. Defaults to ``None``, in which
        case either:
        * If the current thread of execution has an event dispatcher, events are
          processed for this dispatcher.
        * Else, an exception is raised.
    '''

    # Default this event dispatcher if unpassed to that associated with the
    # current thread of execution.
    if event_dispatcher is None:
        event_dispatcher = get_current_event_dispatcher()

    # Process all pending events currently queued with this dispatcher.
    event_dispatcher.processEvents(QEventLoop.WaitForMoreEvents)
