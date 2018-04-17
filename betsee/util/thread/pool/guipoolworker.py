#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **pooled worker** (i.e., thread-safe object implementing generically
startable, pausable, resumable, and stoppable business logic isolated to a
dedicated thread by a parent :class:`QThreadPool` container) classes.
'''

# ....................{ IMPORTS                            }....................
# import traceback, sys
from PySide2.QtCore import (
    QMutex,
    QMutexLocker,
    QObject,
    QRunnable,
    QWaitCondition,
    Signal,
)  # QCoreApplication,
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
from betse.util.type.call.memoizers import property_cached
from betse.util.type.types import (
    type_check,
    CallableTypes,
    MappingOrNoneTypes,
    SequenceOrNoneTypes,
    # StrOrNoneTypes,
)
from betsee.guiexception import (
    BetseePySideThreadWorkerException,
    BetseePySideThreadWorkerStopException,
)
from betsee.util.thread import guithread
from betsee.util.thread.guithreadenum import ThreadWorkerState

# ..................{ GLOBALS                            }..................
_worker_id_next = 0
'''
Non-thread-safe 0-based integer uniquely identifying the next **pooled worker**
(i.e., instance of the :class:`QBetseeThreadPoolWorker` superclass).
'''


_worker_id_lock = QMutex()
'''
Non-exception-safe mutual exclusion primitive rendering the
:func:`_get_worker_id_next` function thread-safe. This primitive is
non-exception-safe and hence should *never* be accessed directly. Each access to
this primitive should be encapsulated by instantiating a one-off exception-safe
:class:QMutexLocker` context manager as the target of a `with` context. Note
that the context provided by the :class:QMutexLocker` class is *not* safely
reusable and hence *must* be re-instantiated in each ``with`` context.
'''

# ....................{ SUPERCLASSES ~ worker : signal     }....................
class QBetseeThreadPoolWorkerSignals(QObject):
    '''
    Low-level collection of all **pooled worker signals** (i.e., :class:`Signal`
    instances thread-safely emittable by the :meth:`QBetseeThreadPoolWorker.run`
    method from an arbitrary pooled thread possibly running *no* Qt event loop).

    Each instance of this class is owned by a pooled worker (i.e.,
    :class:`QBetseeThreadPoolWorker` instance), whose :meth:`run` method emits
    signals defined by this class typically connected to slots defined by
    objects residing in the original thread in which this worker was
    instantiated (e.g., the main event thread).

    Thread Affinity
    ----------
    Each instance of this class resides in the original thread in which this
    worker was instantiated and resides. Hence, neither this class nor any
    subclass of this class should define slots. Why? Qt would execute these
    slots in that original thread rather than the thread running this worker.
    '''

    # ..................{ SIGNALS                            }..................
    started = Signal()
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method immediately
    before running the :meth:`QBetseeThreadPoolWorker._work` method performing
    all subclass-specific business logic.
    '''

    # ..................{ SIGNALS ~ finished                 }..................
    failed = Signal(Exception)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method on catching
    a fatal exception raised by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed this exception as is.

    Usage
    ----------
    Since this is Python 3.x rather than Python 2.x, slots connected to this
    signal may trivially reraise this exception from any other thread (complete
    with a contextual traceback specific to the stack for this thread) via the
    usual ``from`` clause of a ``raise`` statement.

    For this reason, this signal was intentionally designed *not* to emit the
    3-tuple returned by the standard :func:`sys.exc_info` function -- as would
    be required under Python 2.x to properly reraise this exception. Note that a
    little-known alternative to the ``from`` clause of a ``raise`` statement
    does technically exist: the :meth:`Exception.with_traceback` method. By
    explicitly calling this method on a newly instantiated exception passed
    `sys.exc_info()[2]`` (e.g., as
    ``raise MyNewException('wat?').with_traceback(sys.exc_info()[2])``), a
    similar effect is achievable. Since this is substantially less trivial,
    however, the prior approach is currently preferred.
    '''



    finished = Signal(bool)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method immediately
    before returning from that method, passed either ``True`` if that method
    successfully performed all worker-specific business logic (i.e., if the
    :meth:`_work` method successfully returned *without* raising exceptions)
    *or* ``False`` otherwise.

    For finer-grained control over worker results, connect to:

    * The :attr:`failed` signal to obtain exceptions raised by this worker.
    * The :attr:`succeeded` signal to obtain objects returned by this worker.
    '''


    progressed = Signal(int)
    '''
    Signal repeatedly emitted by the :meth:`QBetseeThreadPoolWorker.run` method,
    passed the **progress percentage** (i.e., non-negative integer in the
    range ``[0, 100]``) of work currently completed by this worker.
    '''


    succeeded = Signal(object)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method on
    successfully completing this worker, passed the arbitrary value returned by
    the subclass-specific :meth:`QBetseeThreadPoolWorker._work` method if that
    method returned a value *or* ``None`` otherwise (i.e., in the case that
    method returned no value).
    '''

# ....................{ SUPERCLASSES                       }....................
class QBetseeThreadPoolWorker(QRunnable):
    '''
    Low-level **pooled worker** (i.e., thread-safe object implementing
    generically startable, pausable, resumable, and stoppable business logic
    isolated to a dedicated thread by a parent :class:`QThreadPool` container).

    Lifecycle
    ----------
    By default, workers are **non-recyclable** (i.e., implicitly garbage
    collected by their parent :class:`QThreadPool` container immediately on
    returning from the :meth:`run` method).

    Thread Affinity
    ----------
    All attributes of instances of this class reside in the original thread in
    which this worker was instantiated *except* the following, which reside in a
    dedicated thread of a parent :class:`QThreadPool` container and hence are
    guaranteed to be thread-safe by definition:

    * The :meth:`run` method.
    * All local objects instantiated by the :meth:`run` method.

    All other attributes guaranteed to *not* initially be thread-safe. These
    attributes may nonetheless be rendered thread-safe as follows; either:

    * Define these attributes to be Qt-specific atomic types (e.g.,
      :class:`QAtomicInt`).
    * Lock access to these attributes behind Qt-specific mutual exclusion
      primitives and context managers (e.g., :class:`QMutexLocker`).

    Signal-slot Connections
    ----------
    This class subclasses the :class:`QRunnable` interface rather than the
    standard :class:`QObject` base class. This has various real-world
    implications. In particular, subclasses of this class *cannot* directly
    participate in standard queued signal-slot connections and hence should
    define neither signals *nor* slots.

    Instead, to emit signals from this worker to slots on objects residing in
    other threads:

    * Declare a separate :class:`QObject` subclass defining these signals.
    * Instantiate an instance of this subclass in the parent thread in which
      this worker is instantiated.
    * Pass this instance to this worker's :meth:`__init__` method.

    By definition, this worker *cannot* receive any signals emitted from any
    objects residing in other threads as conventional slots. Instead:

    * Define each such slot as a simple method of this subclass. Since this
      method will be run from the other thread in which the object calling this
      method resides rather than the pooled thread in which this worker resides,
      care should be taken within the body of this method to protectively guard
      access to instance variables with Qt-specific mutual exclusion primitives.
      While numerous primitives exist, the following maximize thread-safety in
      common edge cases (e.g., exceptions) and hence are strongly preferred:

      * :class:`QReadLocker` and :class:`QWriteLocker`, context managers
        suitable for general-purpose use in guarding access to variables safely:

        * Readable from multiple concurrent threads.
        * Writable from only a single thread at a time.

      * :class:`QMutexLocker`, a context manager suitable for general-purpose
        use in guarding access to variables safely readable *and* writable from
        only a single thread at a time.

    Lastly, note that Qt defines numerous atomic types publicly accessible to
    C++ but *not* Python applications (e.g., :class:`QtCore::QAtomicInt`).
    In theory, these types could be leveraged as an efficient alternative to the
    primitives listed above. In practice, these types have yet to be exposed via
    any Python Qt framework (PyQt5, PySide2, or otherwise) and hence remain a
    pipe dream at best.

    Versus QtConcurrent
    ----------
    The API published by this superclass bears a mildly passing resemblance to
    the API published by the QtConcurrent framework -- notably, the
    :class:`PySide2.QtCore.QFuture` class. Unfortunately, the latter imposes
    extreme constraints *not* imposed by this superclass.

    The QtConcurrent framework only provides a single means of multithreading
    arbitrary long-running tasks: :func:`PySide2.QtConcurrent.run`. The
    official documentation publicly admits the uselessness of this function:

        Note that the :class:`PySide2.QtCore.QFuture` returned by
        :func:`PySide2.QtConcurrent.run` does not support canceling, pausing, or
        progress reporting. The :class:`PySide2.QtCore.QFuture` returned can
        only be used to query for the running/finished status and the return
        value of the function.

    One enterprising StackOverflower `circumvented this constraint`_ by defining
    a robust C++ :class:`PySide2.QtCore.QFuture` analogue supporting canceling,
    pausing, and progress reporting. Sadly, this analogue requires C++-specific
    facilities unavailable under Python, including:

    * **Templating.** Since the :class:`PySide2.QtCore.QFuture` API is
      templated, all analogues of that API are also necessarily templated.
    * Private, undocumented Qt APIs (e.g., ``QFutureInterface``,
      ``QFutureInterfaceBase``).

    Ergo, the QtConcurrent framework is largely inapplicable in Python and
    certainly inapplicable for multithreading arbitrary long-running tasks.

    .. _circumvented this constraint:
       https://stackoverflow.com/a/16729619/2809027

    Versus QThread + QObject
    ----------
    The API published by this superclass also bears a passing resemblance to
    various third-party APIs duplicating the common worker-thread Qt model.
    These models typically:

    * Define one or more application-specific **worker types** (i.e.,
      :class:`QObject` subclasses performing long-running tasks to be
      multithreaded).
    * Instantiate these subclasses as local worker objects.
    * Instantiate a local :class:`QThread` object.
    * Move these workers into this thread via the :class:`QObject.moveToThread`
      method.
    * Start this thread by calling the :class:`QThread.start` method.
    * Start, pause, resume, cancel, and restart these workers thread by emitting
      signals connected to slots defined on these workers.

    As with the aforementioned QtConcurrent framework, this approach
    fundamentally works in C++ but fails in Python. For unknown reasons, the
    :class:`QObject.moveToThread` method silently fails to properly move worker
    objects in entirety from the main thread into the worker thread. Slots
    defined on workers claim to run from within their worker thread but instead
    run from within the main thread, as trivially observed with logging.

    Ergo, the worker-thread Qt model is also largely inapplicable in Python and
    certainly inapplicable for multithreading arbitrary long-running tasks.

    Attributes (Public)
    ----------
    _worker_id : int
        0-based integer uniquely identifying this worker. This worker is
        guaranteed to be the *only* instance of this class assigned this
        integer for the lifetime of the current process. For disambiguity with
        the :func:`id` builtin, this variable is explicitly *not* named ``_id``.

    Attributes (Private: State)
    ----------
    _state : ThreadWorkerState:
        Non-thread-safe current execution state of this worker. This state is
        non-thread-safe and hence should *never* be accessed by any callable
        except the thread-safe :meth:`state` property guarding this state with
        mutual exclusion primitives.
    _state_lock : QMutex
        Non-exception-safe mutual exclusion primitive rendering the
        :meth:`state` property thread-safe. This primitive is non-exception-safe
        and hence should *never* be accessed directly. Each access to this
        primitive should be encapsulated by instantiating a one-off
        exception-safe :class:QMutexLocker` context manager as the target of a
        `with` context. Note that the context provided by the
        :class:QMutexLocker` class is *not* safely reusable and hence *must* be
        re-instantiated in each ``with`` context.
    _state_unpaused : QWaitCondition
        Thread synchronization primitive, permitting this worker when paused in
        its parent thread to indefinitely block until an object in another
        thread (e.g., the main thread) requests this worker be unpaused by
        waking up this primitive and hence this worker.

    See Also
    ----------
    https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool
        Prominent blog article entitled "Multithreading PyQt applications with
        QThreadPool," strongly inspiring this implementation.
    https://stackoverflow.com/a/34302791/2809027
        StackOverflow answer strongly inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self) -> None:
        '''
        Initialize this pooled worker.
        '''

        # Initialize our superclass.
        super().__init__()

        # 0-based integer uniquely identifying this worker.
        self._worker_id = _get_worker_id_next()

        # Classify all mutual exclusion objects.
        self._state_lock = QMutex()
        self._state_unpaused = QWaitCondition()

        # Nullify all remaining instance variables for safety.
        self._state = None

        # Default this worker's initial state to the idle state *AFTER*
        # initializing all instance variables, which this property setter
        # internally assumes to be initialized.
        self.state = ThreadWorkerState.IDLE

    # ..................{ PROPERTIES                         }..................
    @property_cached
    def signals(self) -> QBetseeThreadPoolWorkerSignals:
        '''
        Low-level collection of all public signals thread-safely emittable by
        the :meth:`run` method from within an arbitrary pooled thread possibly
        running *no* Qt event loop.

        Design
        ----------
        This instance variable is intentionally implemented as a cached property
        to permit subclasses to expose subclass-specific signals (e.g., by
        trivially redefining this property to return a
        subclass-specific :class:`QBetseeThreadPoolWorkerSignals` instance).
        '''

        return QBetseeThreadPoolWorkerSignals()

    # ..................{ PROPERTIES ~ state                 }..................
    @property
    def state(self) -> ThreadWorkerState:
        '''
        Current execution state of this worker, thread-safely accessible from
        *any* object in *any* thread (including this worker in its own thread).
        '''

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads, return this state.
        #
        # Note that this "QMutexLocker" object is *NOT* safely reusable and
        # hence *MUST* be re-instantiated in each "with" context.
        with QMutexLocker(self._state_lock):
            return self._state


    @state.setter
    def state(self, state: ThreadWorkerState) -> None:
        '''
        Thread-safely set the current execution state of this worker to the
        passed state in a manner settable from *any* object in *any* thread
        (including this worker in its own thread).

        Parameters
        ----------
        state : ThreadWorkerState
            Execution state to set this worker to.
        '''

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads, set this state.
        #
        # Note that this "QMutexLocker" object is *NOT* safely reusable and
        # hence *MUST* be re-instantiated in each "with" context.
        with QMutexLocker(self._state_lock):
            self._state = state

    # ..................{ SLOTS                              }..................
    def run(self):
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine method) performing *all*
        subclass-specific business logic for this worker.

        This method works in a thread-safe manner safely pausable, resumable,
        and stoppable at any time from any object in any thread by directly
        calling the equally thread-safe :meth:`pause`, :meth:`resume`, and
        :meth :meth:`stop` methods.

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.IDLE` state, this
        method changes to the :attr:`ThreadWorkerState.WORKING` state and calls
        the subclass :meth:`_work` method.

        If this worker is in the :attr:`ThreadWorkerState.PAUSED` state, this
        method interprets this signal as a request to resume the work presumably
        previously performed by this worker by a prior signalling of this method.
        To avoid reentrancy issues, this method changes to the
        :attr:`ThreadWorkerState.WORKING` state and immediately returns.
        Assuming that a prior call to this method is still executing, that call
        will internally detect this change and resume working as expected.

        If this worker is in the :attr:`ThreadWorkerState.WORKING` state, this
        method interprets this signal as an accidental attempt by an external
        caller to re-perform the work concurrently being performed by a prior
        call to this method. In that case, this method safely logs a non-fatal
        warning and immediately returns.

        See the :meth:`pause` method for commentary on these design decisions.

        Signals
        ----------
        This method emits the following signals:

        * :attr:`started` immediately *before* this method performs any
          subclass-specific business logic for this worker.
        * :attr:`failed` immediately *after* this method raises an exception
          while performing subclass-specific business logic for this worker.
        * :attr:`finished` immediately *after* this method performs all
          subclass-specific business logic for this worker.

        Caveats
        ----------
        Subclasses must override the :meth:`_work` method rather than this
        method to perform subclass-specific business logic. This method is
        neither intended nor designed to be redefined by subclasses.
        '''

        # True only if the _work() method called below returns successfully
        # (i.e., *WITHOUT* raising exceptions). Defaults to False for safety.
        is_success = False

        # To ensure that callers receive notification of *ALL* exceptions raised
        # by this method, the remainder of this method *MUST* be embedded within
        # an exception handler.
        try:
            # Log this run.
            logs.log_debug(
                'Starting thread "%d" worker "%d"...',
                guithread.get_current_thread_id(), self._worker_id)

            # If this worker is *NOT* currently idle (i.e., is either currently
            # working or paused), the Universe is on the verge of imploding. In
            # short, this should *NEVER* happen; if it does, the caller probably
            # erroneously attempted to manually call this method multiple times
            # from the calling thread.
            #
            # Regardless, this constitutes a fatal error. Raise an exception!
            if self.state is not ThreadWorkerState.IDLE:
                raise BetseePySideThreadWorkerException(
                    'Non-reentrant thread "%d" worker "%d" run() method '
                    'called reentrantly (i.e., multiple times).')

            # Change to the working state.
            self.state = ThreadWorkerState.WORKING

            # Notify external subscribers *BEFORE* beginning subclass work.
            self.started.emit()

            # If this worker or this worker's thread has been externally
            # requested to halt immediately after being requested to start,
            # respect this wish. While an unlikely edge case, the fixed cost of
            # this test is negligible. Ergo, we do so.
            self._halt_work_if_requested()

            # Value returned by performing all subclass-specific business logic.
            return_value = self._work()
        # If a periodic call to the _halt_work_if_requested() method performed
        # within the above call detects either this worker or this worker's
        # thread has been externally requested to stop, do so gracefully by...
        # doing absolutely nothing. Welp, that was easy.
        except BetseePySideThreadWorkerStopException:
            pass
        # If this worker raised any other exception...
        except Exception as exception:
            # Log this failure.
            logs.log_debug(
                'Reraising thread "%d" worker "%d" exception "%r"...',
                guithread.get_current_thread_id(), self._worker_id, exception)

            # Emit this exception to external subscribers.
            self.signals.failed.emit(exception)
        # Else, this worker raised no exception. In this case...
        else:
            # Note the _work() method called above to have returned successfully
            # (i.e., *WITHOUT* raising exceptions).
            is_success = True

            # Log this success.
            logs.log_debug(
                'Returning thread "%d" worker "%d" value "%r"...',
                guithread.get_current_thread_id(),
                self._worker_id,
                return_value)

            # Emit this return value to external subscribers.
            self.signals.succeeded.emit(return_value)
        # In either case, this worker completed. In this case...
        finally:
            # Log this completion.
            logs.log_debug(
                'Finishing thread "%d" worker "%d" with success status "%r"...',
                guithread.get_current_thread_id(),
                self._worker_id,
                is_success)

            # If the state of this worker is still the working state, set this
            # state to the idle (i.e., non-working) state to preserve sanity.
            if self.state is ThreadWorkerState.WORKING:
                self.state = ThreadWorkerState.IDLE

            # Emit this completion status to external subscribers.
            self.signals.finished.emit()

    # ..................{ PSEUDO-SLOTS                       }..................
    def stop(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) gracefully and
        permanently halting all work performed by this worker.

        By :class:`QRunnable` design, this worker is *not* safely restartable
        after finishing -- whether by this method being called, the
        :meth:`_work` method either raising an exception or returning
        successfully without doing so, the parent thread running this worker
        being terminated, or otherwise. Ergo, completion is permanent.

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.IDLE` state, this
        method silently reduces to a noop and preserves the existing state. In
        this case, this worker remains idle.

        If this worker is in either the :attr:`ThreadWorkerState.WORKING` or
        :attr:`ThreadWorkerState.PAUSED` states (implying this worker to either
        currently be or recently have been working), this method changes the
        current state to the :attr:`ThreadWorkerState.IDLE` state. In either
        case, this worker ceases working.
        '''

        # Attempt to...
        try:
            # Log this change.
            logs.log_debug(
                'Stopping thread "%d" worker "%d"...',
                guithread.get_current_thread_id(), self._worker_id)

            # If this worker is currently working or paused, stop this worker.
            if self.state is not ThreadWorkerState.IDLE:
                self.state = ThreadWorkerState.IDLE
        # Regardless of whether the prior logic raised an exception or not...
        finally:
            # Unblock the parent thread of this worker if currently blocking.
            # Deadlocks are unlikely but feasible in edge cases unless this
            # method is unconditionally called here.
            self._unblock_work()

    # ..................{ SLOTS ~ pause                      }..................
    def pause(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) pausing all work
        performed by this worker.

        This slot temporarily halts this work in a thread-safe manner safely
        resumable at any time by calling the :meth:`resume` method.

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.WORKING` state,
        this method pauses work by changing this state to
        :attr:`ThreadWorkerState.PAUSED`. The :meth:`_halt_work_if_requested`
        method is then expected to detect this state change and respond by
        indefinitely blocking on the thread synchronization primitive until
        subsequently awoken by a call to the :meth:`resume` method.

        If this worker is in any other state, this method silently reduces to a
        noop and hence preserves the existing state.
        '''

        # If this worker is *NOT* currently working...
        if self.state is not ThreadWorkerState.WORKING:
            # Log this attempt.
            logs.log_debug(
                'Ignoring attempt to pause idle or already paused '
                'thread "%d" worker "%d".',
                guithread.get_current_thread_id(), self._worker_id)

            # Safely reduce to a noop.
            return
        # Else, this worker is currently working.

        # Log this change.
        logs.log_debug(
            'Pausing thread "%d" worker "%d"...',
            guithread.get_current_thread_id(), self._worker_id)

        # Change this worker's state to paused.
        self.state = ThreadWorkerState.PAUSED


    def resume(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) unpausing this worker.

        This method resumes work in a thread-safe manner safely re-pausable at
        any time by re-calling the :meth:`pause` method.

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.PAUSED` state,
        this method resumes work by changing this state to
        :attr:`ThreadWorkerState.WORKING` and waking up the currently blocked
        thread synchronization primitive if any. The
        :meth:`_halt_work_if_requested` method is then expected to detect this
        state change and respond by unblocking from this primitive and returning
        to the subclass-specific :meth:`_work` method.

        If this worker is in any other state, this method silently reduces to a
        noop and hence preserves the existing state.
        '''

        # Attempt to...
        try:
            # If this worker is *NOT* currently paused...
            if self.state is not ThreadWorkerState.PAUSED:
                # Log this attempt.
                logs.log_debug(
                    'Ignoring attempt to resume idle or already working '
                    'thread "%d" worker "%d".',
                    guithread.get_current_thread_id(), self._worker_id)

                # Safely reduce to a noop.
                return
                # Else, this worker is currently paused.

            # Log this change.
            logs.log_debug(
                'Resuming thread "%d" worker "%d"...',
                guithread.get_current_thread_id(), self._worker_id)

            # If this worker is currently paused, unpause this worker.
            if self.state is ThreadWorkerState.PAUSED:
                self.state = ThreadWorkerState.WORKING
        # Regardless of whether the prior logic raised an exception or not...
        finally:
            # Unblock the parent thread of this worker if currently blocking.
            # Deadlocks are unlikely but feasible in edge cases unless this
            # method is unconditionally called here.
            self._unblock_work()

    # ..................{ WORKERS ~ abstract                 }..................
    # Abstract methods required to be redefined by subclasses.

    def _work(self) -> None:
        '''
        Perform *all* subclass-specific business logic for this worker.

        The superclass :meth:`start` slot internally calls this method in a
        thread-safe manner safely pausable *and* stoppable at any time (e.g., by
        emitting a signal connected to the :meth:`pause` or :meth:`stop` slots).

        Design
        ----------
        Subclasses are required to redefine this method to perform this logic in
        an iterative manner periodically calling the
        :meth:`_halt_work_if_requested` method.

        If either:

        * This worker has been externally signalled to stop (e.g., by emitting a
          signal connected to the :meth:`stop` slot).
        * The thread of execution currently running this worker has been
          externally requested to stop (e.g., by calling the
          :func:`guithread.halt_thread_work` function).

        Then the next such call to the :meth:`_halt_work_if_requested` method
        will raise an exception caught by the parent :meth:`start` slot,
        signalling that slot to immediately terminate this worker. Ergo, that
        method should be called *only* when the subclass is in an
        **interruptible state** (i.e., a self-consistent internal state in which
        this subclass is fully prepared to be immediately terminated).
        '''

        # The next best thing to a properly abstract method, given "QObject"
        # constraints against declaring an "ABCMeta" metaclass. *shrug*
        raise BetseMethodUnimplementedException()

    # ..................{ WORKERS ~ concrete                 }..................
    # Concrete methods intended to be called but *NOT* overriden by subclasses.

    def _halt_work_if_requested(self) -> None:
        '''
        Raise an exception if either:

        * This worker has been externally signalled to stop (e.g., by emitting a
          signal connected to the :meth:`stop` slot).
        * The thread of execution currently running this worker has been
          externally requested to stop (e.g., by calling the
          :func:`guithread.halt_thread_work` function).

        This function is intended to be periodically called by the subclass
        :meth:`_work` function. The exception raised by this function is
        guaranteed to be caught by the :meth:`start` method calling that
        :meth:`_work` function.

        Caveats
        ----------
        This method imposes minor computational overhead and hence should be
        called intermittently (rather than overly frequently). Notably, each
        call to this method processes *all* pending events currently queued with
        this worker's thread -- including those queued for all other workers
        currently running in this thread.

        Raises
        ----------
        BetseePySideThreadWorkerStopException
            If this worker or this worker's thread of execution has been
            signalled or requested to be stopped.
        '''

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads...
        with QMutexLocker(self._state_lock):
            # If either:
            if (
                # If an external call to the stop() method has requested
                # This worker has been externally signalled to stop...
                self._state is ThreadWorkerState.IDLE or
                # This worker's thread has been externally requested to stop...
                guithread.should_halt_thread_work()
            ):
                # Log this interrupt.
                logs.log_debug(
                    'Stopping thread "%d" worker "%d" work...',
                    guithread.get_current_thread_id(), self._worker_id)

                # Instruct the parent run() method to stop.
                raise BetseePySideThreadWorkerStopException('So say we all.')

            # If an external call to the pause() method from another thread has
            # requested this worker to temporarily halt work, do so *AFTER*
            # detecting and handling a request to permanently halt work. Why?
            # Requests to permanently halt take priority over requests to
            # temporarily halt.
            if self._state is ThreadWorkerState.PAUSED:
                self._block_work()

    # ..................{ (UN)BLOCKERS                       }..................
    def _block_work(self) -> None:
        '''
        Indefinitely block all subclass-specific business logic performed by
        this worker.

        This method waits for an external call in another thread to a worker
        pseudo-slot (e.g., the :meth:`resume` method), all of which internally
        call the :meth:`_unblock_work` method to request this worker safely
        resume work.

        Caveats
        ----------
        The :attr:`_state_lock` primitive *must* be acquired (i.e., locked)
        before this method is called. To guarantee this, the call to this method
        should typically be embedded in a context manager of the form ``with
        QMutexLocker(self._state_lock):``, which thread- and exception-safely
        synchronizes access across multiple threads.

        If this is *not* the case, the behaviour of this method is undefined.
        Presumably, that's bad.
        '''

        # Log this blocking behaviour.
        logs.log_debug(
            'Blocking thread "%d" worker "%d"...',
            guithread.get_current_thread_id(), self._worker_id)

        # Indefinitely wait for an external call to the resume() method from
        # another thread to request this worker to resume work.  This has
        # several consequences, including (in temporal order):
        #
        # 1. The "_state_lock" *MUST* be acquired (i.e., locked) before calling
        #    the QWaitCondition.wait() method on this lock. This is the caller's
        #    responsibility, sadly.
        # 2. The QWaitCondition.wait() method immediately releases (i.e.,
        #    unlocks) this lock.
        # 3. The QWaitCondition.wait() method blocks indefinitely until the
        #    QWaitCondition.wakeOne() or wakeAll() methods are called -- in this
        #    case, by a call to our resume() method.
        # 4. The QWaitCondition.wait() method immediately re-acquires (i.e.,
        #    relocks) this lock.
        # 5. The QWaitCondition.wait() method returns.
        #
        # While it is typically inadvisable to mix "QMutexLocker"-style implicit
        # lock management with "QMutex"-style explicit lock control, doing so
        # here is the simplest, sanest, and safest approach.
        self._state_unpaused.wait(self._state_lock)


    def _unblock_work(self) -> None:
        '''
        Unblock all subclass-specific business logic performed by this worker.

        This method wakes up the parent thread of this worker and hence this
        worker *after* the :meth:`_halt_work_if_requested` called the
        :meth:`_block_work` method to indefinitely block that thread. Moreover,
        this method is typically called by an external call in another thread to
        a worker pseudo-slot (e.g., the :meth:`resume` method), all of which
        internally call this method to request this worker safely resume work.

        If the parent thread of this worker is *NOT* currently blocked, this
        method silently reduces to a noop.
        '''

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads...
        with QMutexLocker(self._state_lock):
            # Log this unblocking behaviour.
            logs.log_debug(
                'Unblocking thread "%d" worker "%d"...',
                guithread.get_current_thread_id(), self._worker_id)

            # Wake up the parent thread of this worker if currently blocking.
            self._state_unpaused.wakeOne()

# ....................{ SUPERCLASSES ~ callable            }....................
class QBetseeThreadPoolWorkerCallable(QBetseeThreadPoolWorker):
    '''
    Low-level **callable-defined pooled worker** (i.e., pooled worker whose
    business logic is encapsulated by a caller-defined callable at worker
    initialization time).

    This superclass is a convenience wrapper for the
    :class:`QBetseeThreadPoolWorker` superclass, simplifying usage in the common
    case of business logic definable by a single callable. Under the more
    general-purpose :class:`QBetseeThreadPoolWorker` API, each novel type of
    business logic must be implemented as a distinct subclass overriding the
    :meth:`_work` method to perform that specific logic. Under the less
    general-purpose API provided by this superclass, each such type of business
    logic is instead implemented as a simple callable (e.g., function, lambda)
    performing that specific logic; no new subclasses need be defined.

    Attributes
    ----------
    _func : CallableTypes
        Callable to be subsequently called by the :meth:`start` method,
        performing all business logic isolated to this worker within its parent
        thread.
    _func_args : SequenceTypes
        Sequence of all positional arguments to be passed to the :func:`func`
        callable when subsequently called.
    _func_kwargs : MappingType
        Mapping of all keyword arguments to be passed to the :func:`func`
        callable when subsequently called.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(
        self,

        # Mandatory parameters.
        func: CallableTypes,

        # Optional parameters.
        func_args: SequenceOrNoneTypes,
        func_kwargs: MappingOrNoneTypes,
    ) -> None:
        '''
        Initialize this callable-defined pooled worker with the passed callable
        and positional and keyword arguments to be passed to that callable when
        subsequently called by the :meth:`start` method.

        Parameters
        ----------
        func : CallableTypes
            Callable to be subsequently called by the :meth:`start` method,
            performing all business logic isolated to this worker within its
            parent thread.
        func_args : SequenceOrNoneTypes
            Sequence of all positional arguments to be passed to the
            :func:`func` callable when subsequently called. Defaults to
            ``None``, in which case this sequence defaults to the empty tuple.
        func_kwargs : MappingOrNoneTypes
            Mapping of all keyword arguments to be passed to the :func:`func`
            callable when subsequently called. Defaults to ``None``, in which
            case this mapping defaults to the empty dictionary.
        '''

        # Initialize our superclass.
        super().__init__()

        # Default all unpassed optional parameters to sane defaults.
        if func_args is None:
            func_args = ()
        if func_kwargs is None:
            func_kwargs = {}

        # Classify all passed parameters *AFTER* defaulting these parameters.
        self._func = func
        self._func_args = func_args
        self._func_kwargs = func_kwargs

    # ..................{ WORKERS                            }..................
    def _work(self) -> object:

        # Call this callable with these positional and keyword arguments and
        # return the value returned by this callable, which the parent run()
        # method will emit to slots connected to the "succeeded" signal.
        return self._func(*self._func_args, **self._func_kwargs)

# ..................{ GETTERS                            }..................
def _get_worker_id_next() -> int:
    '''
    Thread-safe 0-based integer uniquely identifying the next **pooled worker**
    (i.e., instance of the :class:`QBetseeThreadPoolWorker` superclass).

    This function internally increments this integer in a thread-safe manner,
    ensuring each of several concurrently instantiated workers to be assigned a
    unique 0-based integer.
    '''

    # Permit this global to be thread-safely incremented.
    global _worker_id_next

    # Within a thread- and exception-safe context manager synchronizing access
    # to this global across multiple threads...
    with QMutexLocker(_worker_id_lock):
        # 0-based integer uniquely identifying the next pooled worker.
        worker_id_next = _worker_id_next

        # Thread-safely increment this integer.
        _worker_id_next += 1

        # Return this integer.
        return worker_id_next
