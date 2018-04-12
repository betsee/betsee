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
import traceback, sys
from PySide2.QtCore import (
    QMutex, QMutexLocker, QObject, QRunnable, Signal)  # QCoreApplication,
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
from betse.util.type.call.memoizers import property_cached
from betse.util.type.types import (
    type_check,
    CallableTypes,
    MappingOrNoneTypes,
    SequenceOrNoneTypes,
)
from betsee.guiexception import BetseePySideThreadWorkerStopException
from betsee.util.thread import guithread
from betsee.util.thread.guithreadenum import ThreadWorkerState

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
    failed = Signal(tuple)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method on catching
    a fatal exception raised by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed the 2-tuple
    ``(exception, exception_traceback)`` describing that exception, where:

    * ``exception`` is the raised exception.
    * ``exception_traceback`` is the traceback object associated with that
      exception, suitable for passing as is to utility functions in the
      standard :mod:`traceback` module accepting a traceback object (e.g.,
      :func:`traceback.format_exception`, :func:`traceback.print_exception`).
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

    Attributes
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
        re-instantiated in each `with` context.

    See Also
    ----------
    https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool
        Prominent blog article entitled "Multithreading PyQt applications with
        QThreadPool," strongly inspiring this implementation.
    https://stackoverflow.com/a/34302791/2809027
        StackOverflow answer strongly inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self) -> None:
        '''
        Initialize this pooled worker.
        '''

        # Initialize our superclass.
        super().__init__()

        # Classify all mutual exclusion objects.
        self._state_lock = QMutex()

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

        # Attempt to...
        try:
            # Value returned by performing all subclass-specific business logic.
            return_value = self._work()
        # If this worker raised an exception...
        except:
            #FIXME: Refactor to emit a 2-tuple as described above instead.
            #FIXME: Log something up.
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.failed.emit((exctype, value, traceback.format_exc()))
        # Else, this worker raised no exception. In this case...
        else:
            #FIXME: Log something up.
            self.signals.succeeded.emit(return_value)
        # In either case, this worker completed. In this case...
        finally:
            #FIXME: Log something up.
            self.signals.finished.emit()


    #FIXME: Integrate into the run() method above.
    def start(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) performing *all*
        subclass-specific business logic for this worker.

        This slot works in a thread-safe manner safely pausable and stoppable at
        any time (e.g., by emitting a signal connected to the :meth:`pause` or
        :meth:`stop` slots).

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.IDLE` state, this
        slot changes to the :attr:`ThreadWorkerState.WORKING` state and calls
        the subclass :meth:`_work` method.

        If this worker is in the :attr:`ThreadWorkerState.PAUSED` state, this
        slot interprets this signal as a request to resume the work presumably
        previously performed by this worker by a prior signalling of this slot.
        To avoid reentrancy issues, this slot changes to the
        :attr:`ThreadWorkerState.WORKING` state and immediately returns.
        Assuming that a prior call to this slot is still executing, that call
        will internally detect this change and resume working as expected.

        If this worker is in the :attr:`ThreadWorkerState.WORKING` state, this
        slot interprets this signal as an accidental attempt by an external
        caller to re-perform the work concurrently being performed by a prior
        call to this slot. In that case, this slot safely logs a non-fatal
        warning and immediately returns.

        See the :meth:`pause` slot for commentary on these design decisions.

        Signals
        ----------
        This slot emits the following signals:

        * :attr:`started` immediately *before* this slot performs any
          subclass-specific business logic for this worker.
        * :attr:`finished` immediately *after* this slot performs all
          subclass-specific business logic for this worker.

        Caveats
        ----------
        Subclasses must override the :meth:`_work` method rather than this slot
        to perform subclass-specific business logic. This slot is neither
        intended nor designed to be overriden by subclasses.
        '''

        # True only if the _work() method called below returns successfully
        # (i.e., *WITHOUT* raising exceptions). Defaults to False for safety.
        is_success = False

        # If this worker is currently paused, resume the prior call to this
        # start() slot by changing to the working state and returning. See the
        # method docstring for commentary.
        if self._state is ThreadWorkerState.PAUSED:
            logs.log_debug(
                'Resuming thread "%d" worker "%s" '
                'via reentrant start() slot...',
                guithread.get_current_thread_id(), self.obj_name)
            self._state = ThreadWorkerState.WORKING
            return

        # If this worker is currently running, resume the prior call to this
        # start() slot by preserving the working state and returning. See the
        # method docstring for commentary. Unlike the prior logic, this logic
        # constitutes a non-fatal error and is logged as such.
        if self._state is ThreadWorkerState.WORKING:
            logs.log_warning(
                'Ignoring attempt to reenter '
                'thread "%d" worker "%s" start() slot.',
                guithread.get_current_thread_id(), self.obj_name)
            return

        # Log this beginning.
        logs.log_debug(
            'Starting thread "%d" worker "%s"...',
            guithread.get_current_thread_id(), self.obj_name)

        # Change to the working state.
        self._state = ThreadWorkerState.WORKING

        # Notify external subscribers *BEFORE* beginning subclass work.
        self.started.emit()

        # Attempt to...
        try:
            # If this worker or this worker's thread has been externally
            # requested to stop immediately after being requested to start,
            # promptly respect this wish on behalf of all workers. Although an
            # unlikely edge case, the fixed cost of this test is negligible.
            self._halt_work_if_requested()

            # Perform all subclass work.
            self._work()

            # Note the _work() method called above to have returned successfully
            # (i.e., *WITHOUT* raising exceptions).
            is_success = True

            # If the state of this worker is still the working state, set this
            # state to the idle (i.e., non-working) state to preserve sanity.
            if self._state is ThreadWorkerState.WORKING:
                self._state = ThreadWorkerState.IDLE
        # If a periodic call to the _halt_work_if_requested() method performed
        # within the above call detects either this worker or this worker's
        # thread has been externally requested to stop, do so gracefully by...
        # doing absolutely nothing. Welp, that was easy.
        except BetseePySideThreadWorkerStopException:
            pass

        # Log this completion.
        logs.log_debug(
            'Finishing thread "%d" worker "%s" with success status "%r"...',
            guithread.get_current_thread_id(),
            self.obj_name,
            is_success)

        # Notify external subscribers of whether this work succeeded or not
        # *AFTER* completing all such work.
        self.finished.emit(is_success)


    #FIXME: Everything that follows is "QObject"-based and must be refactored to
    #leverage the "QRunnable"-based approach. Unfortunately, this means that
    #*ALL* slots will need to be refactored into simple methods operating on
    #either Qt-specific atomic types (e.g., "QAtomicInt") *OR* Qt-specific
    #mutual exclusion primitives (e.g., "QMutexLocker"). Let's be honest: it's
    #hardly ideal, but things could be substantially worse. The best example of
    #this probably resides at... *shrug*

    # ..................{ PSEUDO-SLOTS                       }..................
    def stop(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) stopping all work
        performed by this worker.

        This slot prematurely halts this work in a thread-safe manner. Whether
        this work is safely restartable (e.g., by emitting a signal connected to
        the :meth:`start` slot) is a subclass-specific implementation detail.
        Subclasses may voluntarily elect to either prohibit or permit restarts.

        States
        ----------
        If this worker is in the :attr:`ThreadWorkerState.IDLE` state, this
        slot silently reduces to a noop and preserves the existing state. In
        this case, this worker remains idle.

        If this worker is in either the :attr:`ThreadWorkerState.WORKING` or
        :attr:`ThreadWorkerState.PAUSED`, implying this worker to either
        currently be or recently have been working, this slot changes the
        current state to the :attr:`ThreadWorkerState.IDLE` state. In either
        case, this worker ceases working.
        '''

        # Log this change.
        logs.log_debug(
            'Stopping thread "%d" worker "%s"...',
            guithread.get_current_thread_id(), self.obj_name)

        # If this worker is currently working or paused, stop this worker.
        if self._state is not ThreadWorkerState.IDLE:
            self._state = ThreadWorkerState.IDLE

    # ..................{ SLOTS ~ pause                      }..................
    def pause(self) -> None:
        '''
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) pausing all work
        performed by this worker.

        This slot temporarily halts this work in a thread-safe manner safely
        resumable at any time (e.g., by emitting a signal connected to the
        :meth:`resume` slot).

        States
        ----------
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

        # If this worker is *NOT* currently working...
        if self._state is not ThreadWorkerState.WORKING:
            # Log this attempt.
            logs.log_debug(
                'Ignoring attempt to pause idle or already paused '
                'thread "%d" worker "%s".',
                guithread.get_current_thread_id(), self.obj_name)

            # Safely reduce to a noop.
            return
        # Else, this worker is currently working.

        # Log this change.
        logs.log_debug(
            'Pausing thread "%d" worker "%s"...',
            guithread.get_current_thread_id(), self.obj_name)

        # Change this worker's state to paused.
        self._state = ThreadWorkerState.PAUSED

        # While this worker's state is paused, wait for the resume() slot to be
        # externally signalled by another object (typically in another thread).
        while self._state is ThreadWorkerState.PAUSED:
            guithread.wait_for_events_if_none(event_dispatcher)


    def resume(self) -> None:
        '''
        Slot
        Thread-safe psuedo-slot (i.e., non-slot method mimicking the
        thread-safe, push-based action of a genuine slot) unpausing this worker.

        This slot resumes work in a thread-safe manner safely re-pausable at any
        time (e.g., by re-calling the :meth:`pause` method).

        States
        ----------
        If this worker is in either of the following states, this slot silently
        reduces to a noop and preserves the existing state:

        * :attr:`ThreadWorkerState.IDLE`, implying this worker to *not*
          currently be paused. In this case, this worker remains idle.
        * :attr:`ThreadWorkerState.WORKING`, implying this worker to already
          have been resumed. In this case, this worker remains working.

        See the :meth:`pause` slot for commentary on this design decision.
        '''

        # Log this change.
        logs.log_debug(
            'Resuming thread "%d" worker "%s"...',
            guithread.get_current_thread_id(), self.obj_name)

        # If this worker is currently paused, unpause this worker.
        if self._state is ThreadWorkerState.PAUSED:
            self._state = ThreadWorkerState.WORKING

    # ..................{ METHODS ~ abstract                 }..................
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

    # ..................{ METHODS ~ concrete                 }..................
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
        This function imposes minor computational overhead and hence should be
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

        # Process all pending events currently queued with this worker's thread,
        # notably including any incoming signalling of the stop() slot by
        # objects in other threads..
        guithread.process_events()

        # If either:
        if (
            # This worker has been externally signalled to stop...
            self._state is ThreadWorkerState.IDLE or
            # This worker's thread has been externally requested to stop...
            guithread.should_halt_thread_work()
        # Then
        ):
            # Log this interrupt.
            logs.log_debug(
                'Interrupting thread "%d" worker "%s"...',
                guithread.get_current_thread_id(), self.obj_name)

            # Instruct the parent start() slot to stop.
            raise BetseePySideThreadWorkerStopException('So say we all.')

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
