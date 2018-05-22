#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **pooled worker** (i.e., thread-safe object implementing generically
startable, pausable, resumable, and stoppable business logic isolated to a
dedicated thread by a parent :class:`QThreadPool` container) classes.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import (
    # QCoreApplication,
    QMutex,
    QMutexLocker,
    QRunnable,
    QWaitCondition,
)
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
from betse.util.type.decorator.decmemo import property_cached
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
from betsee.util.thread.pool.guipoolworksig import (
    QBetseeThreadPoolWorkerSignals)

# ....................{ GLOBALS                           }....................
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

# ....................{ SUPERCLASSES                      }....................
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
    which this worker was instantiated *except* the following, which reside in
    a dedicated thread of a parent :class:`QThreadPool` container and hence are
    guaranteed to be thread-safe by definition:

    * The :meth:`run` method.
    * All local objects instantiated by the :meth:`run` method.

    All other attributes should be assumed to *not* be thread-safe. These
    attributes may nonetheless be rendered thread-safe by either:

    * Locking access to these attributes behind Qt-specific mutual exclusion
      primitives and context managers (e.g., :class:`QMutexLocker`).
    * Defining these attributes to be Qt-specific atomic types (e.g.,
      :class:`QAtomicInt`). Since no Python Qt frameworks expose these types,
      this approach applies *only* to C++-based Qt applications.

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
      method resides rather than the pooled thread in which this worker
      resides, care should be taken within the body of this method to
      protectively guard access to instance variables with Qt-specific mutual
      exclusion primitives.  While numerous primitives exist, the following
      maximize thread-safety in common edge cases (e.g., exceptions) and hence
      are strongly preferred:

      * :class:`QReadLocker` and :class:`QWriteLocker`, context managers
        suitable for general-purpose use in guarding access to variables
        safely:

        * Readable from multiple concurrent threads.
        * Writable from only a single thread at a time.

      * :class:`QMutexLocker`, a context manager suitable for general-purpose
        use in guarding access to variables safely readable *and* writable from
        only a single thread at a time.

    Lastly, note that Qt defines numerous atomic types publicly accessible to
    C++ but *not* Python applications (e.g., :class:`QtCore::QAtomicInt`).  In
    theory, these types could be leveraged as an efficient alternative to the
    primitives listed above. In practice, these types have yet to be exposed
    via any Python Qt framework (PyQt5, PySide2, or otherwise) and hence remain
    a pipe dream at best.

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
        :func:`PySide2.QtConcurrent.run` does not support canceling, pausing,
        or progress reporting. The :class:`PySide2.QtCore.QFuture` returned can
        only be used to query for the running/finished status and the return
        value of the function.

    One enterprising StackOverflower `circumvented this constraint`_ by
    defining a robust C++ :class:`PySide2.QtCore.QFuture` analogue supporting
    canceling, pausing, and progress reporting. Sadly, this analogue requires
    C++-specific facilities unavailable under Python, including:

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
    * Start, pause, resume, cancel, and restart these workers thread by
      emitting signals connected to slots defined on these workers.

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
        the :func:`id` builtin, this variable is *not* named ``_id``.

    Attributes (Private: State)
    ----------
    _state : ThreadWorkerState
        Non-thread-safe current execution state of this worker. This state is
        non-thread-safe and hence should *only* be accessed by instantiating an
        exception-safe :class:QMutexLocker` context manager nonce passed the
        :attr:`_state_lock` primitive as the target of a ``with`` context.
    _state_lock : QMutex
        Non-exception-safe mutual exclusion primitive rendering the
        :meth:`state` property thread-safe. This primitive is
        non-exception-safe and hence should *never* be accessed directly. Each
        access to this primitive should be encapsulated by instantiating an
        exception-safe :class:QMutexLocker` context manager nonce as the
        target of a ``with`` context. Note that the context provided by the
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

    # ..................{ INITIALIZERS                      }..................
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

        # Default this worker's initial state to the idle state.
        self._state = ThreadWorkerState.IDLE

    # ..................{ PROPERTIES                        }..................
    @property_cached
    def signals(self) -> QBetseeThreadPoolWorkerSignals:
        '''
        Low-level collection of all public signals thread-safely emittable by
        the :meth:`run` method from within an arbitrary pooled thread possibly
        running *no* Qt event loop.

        Design
        ----------
        This instance variable is intentionally implemented as a cached
        property to permit subclasses to expose subclass-specific signals
        (e.g., by trivially redefining this property to return a
        subclass-specific :class:`QBetseeThreadPoolWorkerSignals` instance).
        '''

        return QBetseeThreadPoolWorkerSignals(
            halt_work_if_requested=self._halt_work_if_requested)

    # ..................{ SLOTS                             }..................
    #FIXME: It would be great to additionally set the object name of (and hence
    #the name of the process associated with) the parent thread of this worker
    #to a human-readable name based on the subclass of this worker. For similar
    #logic, see the QBetseeObjectMixin.set_obj_name_from_class_name() method.
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
        method interprets this signal as a request to resume the work
        presumably previously performed by this worker by a prior signalling of
        this method.  To avoid reentrancy issues, this method changes to the
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
        This method emits the following signals (in order):

        * :attr:`signals.started` immediately *before* this method performs any
          subclass work.
        * :attr:`signals.failed` immediately *after* this method erroneously
          raises an unexpected exception while performing subclass work but
          *before* the :attr:`signals.finished` signal is emitted.
        * :attr:`signals.succeeded` immediately *after* all subclass work
          performed by this method successfully returns but *before* the
          :attr:`signals.finished` signal is emitted.
        * :attr:`signals.finished` immediately *after* this method performs all
          subclass work, regardless of whether that work succeeded or failed.

        Caveats
        ----------
        Subclasses must override the :meth:`_work` method rather than this
        method to perform subclass-specific business logic. This method is
        neither intended nor designed to be redefined by subclasses.
        '''

        # True only if the _work() method called below returns successfully
        # (i.e., *WITHOUT* raising exceptions). Defaults to False for safety.
        is_success = False

        # To ensure that callers receive notification of *ALL* exceptions
        # raised by this method, the remainder of this method *MUST* be
        # embedded within an exception handler.
        try:
            # Log this run.
            logs.log_debug(
                'Starting thread "%d" worker "%d"...',
                guithread.get_current_thread_id(), self._worker_id)

            # Within a thread- and exception-safe context manager synchronizing
            # access to this state across multiple threads...
            with QMutexLocker(self._state_lock):
                # If this worker is *NOT* currently idle (i.e., is either
                # currently working or paused), the Universe is on the verge of
                # imploding. In short, this should *NEVER* happen; if it does,
                # the caller probably erroneously attempted to manually call
                # this method multiple times from the calling thread.
                #
                # Regardless, this constitutes an error. Raise an exception!
                if self._state is not ThreadWorkerState.IDLE:
                    raise BetseePySideThreadWorkerException(
                        'Non-reentrant thread "%d" worker "%d" run() method '
                        'called reentrantly (i.e., multiple times).')

                # Change to the working state.
                self._state = ThreadWorkerState.WORKING

            # Notify external subscribers *BEFORE* beginning subclass work.
            self.signals.started.emit()

            # If this worker or this worker's thread has been externally
            # requested to halt immediately after being requested to start,
            # respect this wish. While an unlikely edge case, the fixed cost of
            # this test is negligible. Ergo, we do so.
            self._halt_work_if_requested()

            # Retain this purely for exception testing purposes.
            # raise ValueError('wat?')

            # Value returned by performing subclass-specific business logic.
            return_value = self._work()
        # If a periodic call to the _halt_work_if_requested() method performed
        # within the above call detects either this worker or this worker's
        # thread has been externally requested to stop, do so gracefully by...
        except BetseePySideThreadWorkerStopException:
            # Log this cessation. That's it. Welp, that was easy.
            logs.log_debug(
                'Stopping thread "%d" worker "%d"...',
                guithread.get_current_thread_id(), self._worker_id)
        # If this worker raised any other exception...
        except Exception as exception:
            # Log this failure.
            logs.log_debug(
                'Emitting thread "%d" worker "%d" exception "%r"...',
                guithread.get_current_thread_id(), self._worker_id, exception)

            # Emit this exception to external subscribers.
            self.signals.failed.emit(exception)
        # Else, this worker raised no exception. In this case...
        else:
            # Note the _work() method called above to have returned
            # successfully (i.e., *WITHOUT* raising exceptions).
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
                'Finishing thread "%d" worker "%d" with exit status "%r"...',
                guithread.get_current_thread_id(),
                self._worker_id,
                is_success)

            # Within a thread- and exception-safe context manager synchronizing
            # access to this state across multiple threads...
            with QMutexLocker(self._state_lock):
                # If this worker's state is working, set this state to the idle
                # (i.e., non-working) state.
                if self._state is ThreadWorkerState.WORKING:
                    self._state = ThreadWorkerState.IDLE

            # Emit this completion status to external subscribers.
            self.signals.finished.emit(is_success)

    # ..................{ PSEUDO-SLOTS                      }..................
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
        Regardless of the current state of this worker, this method halts work
        by changing this state to :attr:`ThreadWorkerState.IDLE`. The
        :meth:`_halt_work_if_requested` method in the thread running this
        worker then detects this state change and responds by raising an
        exception internally caught by the parent :meth:`run` method.
        '''

        # Log this action.
        logs.log_debug(
            'Requesting thread "%d" worker "%d" to stop...',
            guithread.get_current_thread_id(), self._worker_id)

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads...
        with QMutexLocker(self._state_lock):
            # Regardless of the current state of this worker, change this
            # worker's state to idle (i.e., non-working).
            self._state = ThreadWorkerState.IDLE

            # Unblock the parent thread of this worker if currently blocked.
            # Deadlocks are unlikely but feasible in edge cases unless this
            # method is unconditionally called here.
            #
            # Note that, as the prior logic is sufficiently simplistic to
            # ensure *NO* exception to be raised, this call need not be
            # embedded in a try-finally block for safety.
            self._unblock_work()

    # ..................{ SLOTS ~ pause                     }..................
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
        method in the thread running this worker then detects this state change
        and responds by indefinitely blocking on this synchronization primitive
        until subsequently awoken by a call to the :meth:`resume` method.

        If this worker is in any other state, this method silently reduces to a
        noop and hence preserves the existing state.
        '''

        # Log this action.
        logs.log_debug(
            'Requesting thread "%d" worker "%d" to pause...',
            guithread.get_current_thread_id(), self._worker_id)

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads...
        with QMutexLocker(self._state_lock):
            # If this worker is *NOT* currently working...
            if self._state is not ThreadWorkerState.WORKING:
                # Log this attempt.
                logs.log_debug(
                    'Ignoring attempt to pause idle or already paused '
                    'thread "%d" worker "%d".',
                    guithread.get_current_thread_id(), self._worker_id)

                # Safely reduce to a noop.
                return
            # Else, this worker is currently working.

            # Change this worker's state to paused.
            self._state = ThreadWorkerState.PAUSED


    def resume(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) unpausing this
        worker.

        This method resumes work in a thread-safe manner safely re-pausable at
        any time by re-calling the :meth:`pause` method.

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.PAUSED` state,
        this method resumes work by changing this state to
        :attr:`ThreadWorkerState.WORKING` and waking up the currently blocked
        synchronization primitive if any. The :meth:`_halt_work_if_requested`
        method in the thread running this worker then detects this state change
        and responds by unblocking from this primitive and returning to the
        subclass-specific :meth:`_work` method.

        If this worker is in any other state, this method silently reduces to a
        noop and hence preserves the existing state.
        '''

        # Log this action.
        logs.log_debug(
            'Requesting thread "%d" worker "%d" to resume...',
            guithread.get_current_thread_id(), self._worker_id)

        # Within a thread- and exception-safe context manager synchronizing
        # access to this state across multiple threads...
        with QMutexLocker(self._state_lock):
            # Attempt to...
            try:
                # If this worker is *NOT* currently paused...
                if self._state is not ThreadWorkerState.PAUSED:
                    # Log this attempt.
                    logs.log_debug(
                        'Ignoring attempt to resume idle or already working '
                        'thread "%d" worker "%d".',
                        guithread.get_current_thread_id(), self._worker_id)

                    # Safely reduce to a noop.
                    return
                # Else, this worker is currently paused.

                # Change this worker's state to working, thus unpausing.
                self._state = ThreadWorkerState.WORKING
            # Regardless of whether doing so raised an exception or not...
            finally:
                # Unblock the parent thread of this worker if currently
                # blocked.  Deadlocks are unlikely but feasible in edge cases
                # unless this method is unconditionally called here.
                self._unblock_work()

    # ..................{ WORKERS ~ abstract                }..................
    # Abstract methods required to be redefined by subclasses.

    def _work(self) -> None:
        '''
        Perform *all* subclass-specific business logic for this worker.

        The superclass :meth:`start` slot internally calls this method in a
        thread-safe manner safely pausable *and* stoppable at any time (e.g.,
        by emitting a signal connected to the :meth:`pause` or :meth:`stop`
        slots).

        Design
        ----------
        Subclasses are required to redefine this method to perform this logic
        in an iterative manner periodically calling the
        :meth:`_halt_work_if_requested` method.

        If either:

        * This worker has been externally signalled to stop (e.g., by emitting
          a signal connected to the :meth:`stop` slot).
        * The thread of execution currently running this worker has been
          externally requested to stop (e.g., by calling the
          :func:`guithread.halt_thread_work` function).

        Then the next such call to the :meth:`_halt_work_if_requested` method
        will raise an exception caught by the parent :meth:`start` slot,
        signalling that slot to immediately terminate this worker. Ergo, that
        method should be called *only* when the subclass is in an
        **interruptible state** (i.e., a self-consistent internal state in
        which this subclass is fully prepared to be immediately terminated).
        '''

        # The next best thing to a properly abstract method, given "QObject"
        # constraints against declaring an "ABCMeta" metaclass. *shrug*
        raise BetseMethodUnimplementedException()

    # ..................{ WORKERS ~ concrete                }..................
    # Concrete methods intended to be called but *NOT* overriden by subclasses.

    def _halt_work_if_requested(self) -> None:
        '''
        Temporarily or permanently halt all subclass-specific business logic
        when requested to do so by external callers residing in other threads.

        This function is intended to be periodically called by the subclass
        :meth:`_work` function. Specifically, this method:

        * Raises an exception (expected to be caught by the :meth:`run` method
          calling the :meth:`_work` function) if either:

          * This worker has been externally signalled to stop (e.g., by an
            external call to the the :meth:`stop` method).
          * The thread of execution currently running this worker has been
            externally requested to stop (e.g., by calling the
            :func:`guithread.halt_thread_work` function).

        * Pauses this worker if this worker has been externally signalled to
          pause (e.g., by an external call to the the :meth:`pause` method).

        Caveats
        ----------
        This method imposes minor computational overhead and hence should be
        called intermittently (rather than overly frequently). Notably, each
        call to this method processes *all* pending events currently queued
        with this worker's thread -- including those queued for all other
        workers currently running in this thread.

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
            # ...then permanently halt this worker.
            ):
                self._stop_work()

            # If an external call to the pause() method from another thread has
            # requested this worker to temporarily halt work, do so *AFTER*
            # detecting and handling a request to permanently halt work. Why?
            # Requests to permanently halt take priority over requests to
            # temporarily halt.
            if self._state is ThreadWorkerState.PAUSED:
                self._block_work()

    # ..................{ STOPPERS                          }..................
    def _stop_work(self) -> None:
        '''
        Gracefully terminate all subclass-specific business logic performed by
        this worker.

        This method raises an internal exception expected to be caught *only*
        by the parent :meth:`run` method, as a crude form of coordinating
        signalling between this and that method.
        '''

        # Log this action.
        logs.log_debug(
            'Stopping thread "%d" worker "%d" work...',
            guithread.get_current_thread_id(), self._worker_id)

        # Instruct the parent run() method to stop.
        raise BetseePySideThreadWorkerStopException('So say we all.')

    # ..................{ (UN)BLOCKERS                      }..................
    def _block_work(self) -> None:
        '''
        Indefinitely block all subclass-specific business logic performed by
        this worker.

        This method waits for an external call from another thread to a worker
        pseudo-slot (e.g., the :meth:`resume` method), all of which internally
        call the :meth:`_unblock_work` method to safely resume work.

        Caveats
        ----------
        The :attr:`_state_lock` primitive *must* be acquired (i.e., locked)
        before this method is called. To guarantee this, the call to this
        method should typically be embedded in a context manager of the form
        ``with QMutexLocker(self._state_lock):``, which thread- and
        exception-safely synchronizes access across multiple threads.

        If this is *not* the case, the behaviour of this method is undefined.
        Presumably, that's bad.
        '''

        # Log this blocking behaviour.
        logs.log_debug(
            'Pausing thread "%d" worker "%d"...',
            guithread.get_current_thread_id(), self._worker_id)

        # Notify callers that this worker is now paused immediately *BEFORE*
        # blocking this worker.
        self.signals.paused.emit()

        # Indefinitely wait for an external call to the resume() method from
        # another thread to request this worker to resume work.  This has
        # several consequences, including (in temporal order):
        #
        # 1. The "_state_lock" *MUST* be acquired (i.e., locked) before calling
        #    the QWaitCondition.wait() method on this lock. This is the
        #    caller's responsibility, sadly.
        # 2. The QWaitCondition.wait() method immediately releases (i.e.,
        #    unlocks) this lock.
        # 3. The QWaitCondition.wait() method blocks indefinitely until the
        #    QWaitCondition.wakeOne() or wakeAll() methods are called -- in
        #    this case, by a call to our resume() method.
        # 4. The QWaitCondition.wait() method immediately re-acquires (i.e.,
        #    relocks) this lock.
        # 5. The QWaitCondition.wait() method returns.
        #
        # While it is typically inadvisable to mix "QMutexLocker"-style
        # implicit lock management with "QMutex"-style explicit lock control,
        # doing so here is the simplest, sanest, and safest approach.
        self._state_unpaused.wait(self._state_lock)

        # Notify callers that this worker is now resumed immediately *AFTER*
        # unblocking this worker.
        self.signals.resumed.emit()


    def _unblock_work(self) -> None:
        '''
        Unblock all subclass-specific business logic performed by this worker.

        This method wakes up the parent thread of this worker and hence this
        worker *after* the :meth:`_halt_work_if_requested` called the
        :meth:`_block_work` method to indefinitely block that thread. Moreover,
        this method is typically called by an external call in another thread
        to a worker pseudo-slot (e.g., the :meth:`resume` method), all of which
        internally call this method to request this worker safely resume work.

        If the parent thread of this worker is *NOT* currently blocked, this
        method silently reduces to a noop.

        Caveats
        ----------
        The :attr:`_state_lock` primitive *must* be acquired (i.e., locked)
        before this method is called. See the :meth:`_block_work` method.
        '''

        # Log this unblocking behaviour.
        logs.log_debug(
            'Resuming thread "%d" worker "%d"...',
            guithread.get_current_thread_id(), self._worker_id)

        # Wake up the parent thread of this worker if currently blocking.
        self._state_unpaused.wakeOne()

# ....................{ SUPERCLASSES ~ callable           }....................
class QBetseeThreadPoolWorkerCallable(QBetseeThreadPoolWorker):
    '''
    Low-level **callable-defined pooled worker** (i.e., pooled worker whose
    business logic is encapsulated by a caller-defined callable at worker
    initialization time).

    This superclass is a convenience wrapper for the
    :class:`QBetseeThreadPoolWorker` superclass, simplifying usage in the
    common case of business logic definable by a single callable. Under the
    more general-purpose :class:`QBetseeThreadPoolWorker` API, each novel type
    of business logic must be implemented as a distinct subclass overriding the
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

    # ..................{ INITIALIZERS                      }..................
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

    # ..................{ WORKERS                           }..................
    def _work(self) -> object:

        # Call this callable with these positional and keyword arguments and
        # return the value returned by this callable, which the parent run()
        # method will emit to slots connected to the "succeeded" signal.
        return self._func(*self._func_args, **self._func_kwargs)

# ....................{ GETTERS                           }....................
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
