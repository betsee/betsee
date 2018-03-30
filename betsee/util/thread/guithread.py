#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **multithreading** (i.e., platform-portable, pure-Qt,
:class:`QThread`-based parallelization implemented external to Python and hence
Python's restrictive Global Interpreter Lock (GIL)) facilities.
'''

#FIXME: This submodule is increasingly awkward, largely due to the unctuous
#requirement that a "thread" reference always be passed whenever an
#"event_dispatcher" reference is required. Instead, do the following:
#
#* Define a new "ThreadEventDispatcherWrapper" class subclassing "object" rather
#  than "QObject" in this submodule.
#* Define the following instance variables of this class:
#  * "thread".
#  * "event_dispatcher".
#* Redefine the process_events() and wait_for_events_if_none() functions into
#  methods of this class operating upon these variables.
#* Redefine the get_current_event_dispatcher() to return an instance of the
#  "ThreadEventDispatcherWrapper" class.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import (
    QAbstractEventDispatcher, QCoreApplication, QEventLoop, QThread)
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideThreadException
from betsee.util.type.guitype import (
    QAbstractEventDispatcherOrNoneTypes, QThreadOrNoneTypes)

# ....................{ TESTERS                            }....................
@type_check
def should_halt_thread_work(thread: QThreadOrNoneTypes = None) -> bool:
    '''
    ``True`` only if some object has requested that the passed thread of
    execution voluntarily halt *all* tasks (e.g., overriden :meth:`QThread.run`
    method) and workers (e.g., subclassed :class:`QBetseeThreadWorkerABC` object)
    currently running in this thread.

    This function is intended to be voluntarily called by tasks and workers.

    Caveats
    ----------
    One parent thread may run an arbitrary number of child workers. However, the
    request to halt tested by this function is a low-level condition applying to
    a single thread rather than a single worker. Hence, if this function returns
    ``False``, *all* tasks and workers currently running in this thread are
    expected to gracefully halt all work being performed and then terminate.

    For fine-grained control over worker lifecycles, external callers are
    strongly advised to signal each such worker to gracefully halt (e.g., by
    emitting a signal connected to the :meth:`QBetseeThreadWorkerABC.stop` slot)
    rather than requesting that the thread running those workers halt (e.g., by
    calling the :meth:`QThread.requestInterruption` method). Nonetheless,
    workers are expected to respect both types of requests.

    For convenience, note that the
    :meth:`QBetseeThreadWorkerABC._halt_work_if_requested` method implicitly
    respects both types of requests. Ergo, :class:`QBetseeThreadWorkerABC`
    subclasses need *not* and should *not* explicitly call this function.

    Parameters
    ----------
    thread : QThreadOrNoneTypes
        Thread to request to be halted. Defaults to ``None``, in which case the
        current thread of execution is requested to be halted.

    Returns
    ----------
    bool
        ``True`` only if some object has requested this thread to voluntarily
        halt *all* tasks and workers currently running in this thread.

    See Also
    ----------
    :func:`halt_thread_work`
        Companion function requesting this thread to voluntarily halt these
        tasks and workers.
    '''

    # Default this thread if unpassed to the current thread of execution.
    if thread is None:
        thread = get_current_thread()

    # Return true only if this thread has been requested to be halted.
    return thread.isInterruptionRequested()

# ....................{ GETTERS                            }....................
#FIXME: *NO*. This function is fundamentally broken, as some combination of
#PySide2 and/or Qt erroneously garbage collect event dispatchers unless the
#threads owning those dispatchers are also in scope. See the above "FIXME".
@type_check
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

# ....................{ GETTERS ~ current : thread         }....................
def get_current_thread() -> QThread:
    '''
    Wrapper encapsulating the **current thread** (i.e., Qt-specific thread of
    execution responsible for the call to this function).
    '''

    return QThread.currentThread()


def get_current_thread_id() -> int:
    '''
    Arbitrary Qt-specific integer uniquely identifying the current thread within
    the active Python interpreter.

    See Also
    ----------
    :func:`get_current_thread`
        Further details.
    '''

    return QThread.currentThreadId()


def get_current_thread_process_name() -> str:
    '''
    Name of the OS-level process associated with the current thread, equivalent
    to the Qt-specific name of this object.

    See Also
    ----------
    :meth:`betsee.util.thread.guithreadcls.QBetseeWorkerThread.process_name`
        Further details.
    '''

    # Current thread.
    thread = get_current_thread()

    # Return this thread's process name.
    return thread.objectName()

# ....................{ GETTERS ~ current : event          }....................
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

# ....................{ HALTERS                            }....................
@type_check
def halt_thread_work(thread: QThreadOrNoneTypes = None) -> bool:
    '''
    Requested that the passed thread of execution voluntarily halt *all* tasks
    (e.g., overriden :meth:`QThread.run` method) and workers (e.g., subclassed
    :class:`QBetseeThreadWorkerABC` object) currently running in this thread.

    This function is intended to be called from objects in other threads.

    Caveats
    ----------
    After this function is called, this request will be unconditionally
    preserved in this thread until this thread is manually halted and restarted
    (e.g., by calling the :meth:`QBetseeWorkerThread.halt` and
    :meth:`QBetseeWorkerThread.start` methods in that order). However, doing so:

    * Terminates all tasks and workers currently running in this thread,
      typically in a non-graceful manner resulting in in-memory or on-disk data
      corruption.
    * Discards all pending events currently queued with this thread -- including
      both outgoing signals emitted by *and* incoming slots signalled on any
      workers still running in this thread.

    Hence, due to long-standing deficiencies in the Qt API, this request
    *cannot* be gracefully "undone." Attempting to do so *always* runs a risk of
    non-gracefully terminating running and pending work. The only alternative to
    this extremely concerning caveat is to signal each such worker to gracefully
    halt (e.g., by emitting a signal connected to the
    :meth:`QBetseeThreadWorkerABC.stop` slot) rather than calling this method.

    **You have been warned.** There be vicious vipers scuttling about here.

    Parameters
    ----------
    thread : QThreadOrNoneTypes
        Thread to request to be halted. Defaults to ``None``, in which case the
        current thread of execution is requested to be halted.

    See Also
    ----------
    :func:`should_halt_thread_work`
        Further details.
    https://forum.qt.io/topic/43067/qthread-requestinterruption-cannot-be-undone
        Prominent Qt forum discussion on this lamentable topic.
    '''

    # Default this thread if unpassed to the current thread of execution.
    if thread is None:
        thread = get_current_thread()

    # Request this thread's work to be halted.
    return thread.requestInterruption()

# ....................{ PROCESSORS                         }....................
#FIXME: This and the function below require fundamental refactoring. Why? It
#appears infeasible to pass arbitrary "event_dispatcher" objects around. For
#unknown reasons, Python and/or Qt aggressively garbage collect these objects in
#the absence of a reference to the threads owning these objects. Ergo:
#
#* Refactor this function to accept an additional preceding "thread" argument.
#* Likewise for the function defined below.
@type_check
def process_events(
    event_dispatcher: QAbstractEventDispatcherOrNoneTypes = None) -> None:
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
        thread, event_dispatcher = get_current_thread_event_dispatcher()

    # Process all pending events currently queued with this dispatcher.
    event_dispatcher.processEvents(QEventLoop.AllEvents)


#FIXME: Shift above, please.
#FIXME: Annotate and document properly, please.
#FIXME: Replace *ALL* calls to the get_current_event_dispatcher() function with
#calls to this function instead.
def get_current_thread_event_dispatcher():
    thread = QThread.currentThread()
    event_dispatcher = thread.eventDispatcher()
    if not event_dispatcher:
        raise BetseePySideThreadException(QCoreApplication.translate(
            'get_current_event_dispatcher',
            'No event dispatcher running for thread "{}".'.format(
                thread.objectName())))

    return thread, event_dispatcher


#FIXME: Explicitly raise an exception if this event dispatcher is the main event
#dispatcher (i.e., event dispatcher running the main GUI event loop). Permitting
#this edge case results in the main GUI being blocked -- which is bad.
@type_check
def wait_for_events_if_none(
    event_dispatcher: QAbstractEventDispatcherOrNoneTypes = None) -> None:
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
