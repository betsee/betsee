#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **pooled worker** (i.e., thread-safe object implementing generically
startable, pausable, resumable, and stoppable business logic isolated to a
dedicated thread by a parent :class:`QThreadPool` container) classes.
'''

#FIXME: Investigate the "QtConcurent" framework further. My working assumption
#is that this framework required a map-reduce architecture. If that is *NOT* the
#case, we may in fact prefer to leverage "QtConcurent", which would offer worker
#pausing functionality built-in. *shrug*

# ....................{ IMPORTS                            }....................
import traceback, sys
from PySide2.QtCore import QObject, QRunnable, Signal, Slot  # QCoreApplication,
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
from betse.util.type.enums import make_enum
# from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideThreadWorkerException
from betsee.util.thread import guithread
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ ENUMERATIONS                       }....................
#FIXME: Consider extracting into a new "betsee.util.thread.guithreadenum"
#submodule for use across multiple worker submodules.
_ThreadWorkerState = make_enum(
    class_name='_ThreadWorkerState',
    member_names=('IDLE', 'WORKING', 'PAUSED',))
'''
Enumeration of all supported types of **worker state** (i.e., mutually
exclusive high-level execution state of a :class:`QBetseeThreadPoolWorkerABC` instance,
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

# ....................{ EXCEPTIONS                         }....................
#FIXME: Genericize this as well. Maybe to a new "guithreadexception" submodule?
class _ThreadWorkerStopException(BetseePySideThreadWorkerException):
    '''
    :class:`QBetseeThreadPoolWorkerABC`-specific exception internally raised by the
    :meth:`QBetseeThreadPoolWorkerABC._halt_work_if_requested` method and caught by
    the :meth:`QBetseeThreadPoolWorkerABC.start` slot.

    This exception is intended exclusively for private use by the aforementioned
    methods as a crude, albeit sufficient, means of facilitating subclass
    intercommunication.
    '''

    pass

# ....................{ SUPERCLASSES ~ worker : signal     }....................
class QBetseeThreadPoolWorkerSignals(QObject):
    '''
    Low-level collection of all **pooled worker signals** (i.e., :class:`Signal`
    instances thread-safely emittable

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
    progress = Signal(int)
    '''
    Signal emitting an integer in the range ``[0, 100]`` indicating the current
    percentage of progress currently completed by this worker.
    '''


    finished = Signal()
    '''
    Signal emitted by the :meth:`run` method on completing this worker,
    regardless of whether this method successfully returned or raised an
    exception.
    '''


    result = Signal(object)
    '''
    Signal emitting the arbitrary value returned by the :meth:`run` method on
    successfully completing this worker if this method returned a value *or*
    ``None`` otherwise (i.e., if this method returned no value).
    '''


    error = Signal(tuple)
    '''
    Signal emitting a 3-tuple ``(exctype, value, traceback.format_exc())`` when
    an exception is raised by this worker.
    '''

# ....................{ SUPERCLASSES ~ worker              }....................
class QBetseeThreadPoolWorker(QBetseeObjectMixin, QRunnable):
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
    implications, including:

    * Instances of this class cannot directly participate in standard queued
      signal-slot connections. Hence, subclasses of this class should define
      neither signals *nor* slots. Instead:

      * To emit signals from this worker to slots on objects residing in other
        threads:

        * Declare a separate :class:`QObject` subclass defining these signals.
        * Instantiate an instance of this subclass in the parent thread in which
          this worker is instantiated.
        * Pass this instance to this worker's :meth:`__init__` method.

      * To receive signals emitted from objects residing in other threads into
        this worker:

    Attributes
    ----------
    _state : _ThreadWorkerState
        Current execution state of this worker. For thread-safety, this state
        should *not* be externally accessed by objects residing in other
        threads. Doing so safely would require thread-safe mutual exclusion
        (e.g., with a dedicated :class:`QMutexLocker` context manager), which
        currently exceeds the mandate of this superclass.

    See Also
    ----------
    https://martinfitzpatrick.name/article/multithreading-pyqt-applications-with-qthreadpool
        Prominent blog article entitled "Multithreading PyQt applications with
        QThreadPool," strongly inspiring this implementation.
    https://stackoverflow.com/a/34302791/2809027
        StackOverflow answer strongly inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, fn, *args, **kwargs):
        '''
        Initialize this pooled worker.
        '''

        # Initialize our superclass.
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        #FIXME: This object should probably be optionally passed to this method
        #by the external caller, permitting callers to define additional
        #signals. Or perhaps not? Perhaps the default signals suffice. *shrug*
        self.signals = QBetseeThreadPoolWorkerSignals()

        # Default this worker's initial state to the idle state.
        self._state = _ThreadWorkerState.IDLE

        #FIXME: We'll probably want at least the "start_signal" attribute to be
        #shifted into the QBetseeThreadPoolWorkerSignals() class. The remainder
        #are probably safely deletable, now.

        # Connect this worker's external-facing signals to corresponding slots.
        # self.start_signal .connect(self.start)
        # self.stop_signal  .connect(self.stop)
        # self.pause_signal .connect(self.pause)
        # self.resume_signal.connect(self.resume)

    # ..................{ SLOTS                              }..................
    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


    #FIXME: Everything that follows is "QObject"-based and must be refactored to
    #leverage the "QRunnable"-based approach. Unfortunately, this means that
    #*ALL* slots will need to be refactored into simple methods operating on
    #either Qt-specific atomic types (e.g., "QAtomicInt") *OR* Qt-specific
    #mutual exclusion primitives (e.g., "QMutexLocker"). Let's be honest: it's
    #hardly ideal, but things could be substantially worse. The best example of
    #this probably resides at:
    #
    #

    # ..................{ SIGNALS ~ external                 }..................
    # Signals externally emitted by callers owning instances of this superclass.

    #FIXME: Obviously, requiring a string be unconditionally passed to all
    #start_signal() invocations is... well, insane. Instead, this should be
    #refactored as follows:
    #
    #* Define a new "QBetseeThreadPoolWorkerStartArgsABC(QObject)" class in this
    #  or possibly another submodule (e.g., "guiworkerstartcls").
    #* Rewrite this signal to simply read:
    #     start_signal = Signal(QBetseeThreadPoolWorkerStartArgsABC)
    #* Rewrite the start() slot and _work() methods defined below to similarly
    #  accept instances of this "QBetseeThreadPoolWorkerStartArgsABC" class rather
    #  than... raw strings. *sigh*
    #* Refactor all subclasses of this class similarly.
    #* Refactor all emissions of this signal to emit
    #  "QBetseeThreadPoolWorkerStartArgsABC" instances rather than raw strings.
    #FIXME: Actually, we didn't realize that signals could emit arbitrary Python
    #objects. Apparently, they can. Ergo, the above plan should be refactored to
    #instead subclass "ThreadWorkerStartArgsABC(object, meta=ABCMeta)". Maybe?
    start_signal = Signal(str)
    '''
    Signal connected the :meth:`start` slot starting this worker.

    This signal is a caller convenience simplifying worker usage. Alternately,
    callers may elect to connect caller-defined signals to this slot as needed.
    '''


    stop_signal = Signal()
    '''
    Signal connected the :meth:`stop` slot starting this worker.

    This signal is a caller convenience simplifying worker usage. Alternately,
    callers may elect to connect caller-defined signals to this slot as needed.
    '''


    pause_signal = Signal()
    '''
    Signal connected the :meth:`pause` slot pausing this worker.

    This signal is a caller convenience simplifying worker usage. Alternately,
    callers may elect to connect caller-defined signals to this slot as needed.
    '''


    resume_signal = Signal()
    '''
    Signal connected the :meth:`resume` slot resuming this worker.

    This signal is a caller convenience simplifying worker usage. Alternately,
    callers may elect to connect caller-defined signals to this slot as needed.
    '''

    # ..................{ SIGNALS ~ internal                 }..................
    # Signals internally emitted by instances of this superclass.

    started = Signal()
    '''
    Signal emitted immediately on entering the :meth:`start` slot starting this
    worker.

    This signal is emitted *before* that slot performs *any* subclass-specific
    business logic for this worker.
    '''


    finished = Signal(bool)
    '''
    Signal emitted immediately before returning from the :meth:`start` slot for
    this worker, passed either ``True`` if this slot successfully performed all
    subclass-specific business logic for this worker (i.e., if the :meth:`_work`
    method returns *without* raising exceptions) *or* ``False`` otherwise.

    This signal is emitted *after* that slot performs *all* subclass-specific
    business logic for this worker.
    '''

    # ..................{ SLOTS                              }..................
    #FIXME: Obviously, forcing "str" usage is awful. See above for solutions.
    @Slot(str)
    def start(self, arbitrary_str: str) -> None:
        '''
        Slot performing *all* subclass-specific business logic for this worker.

        This slot works in a thread-safe manner safely pausable and stoppable at
        any time (e.g., by emitting a signal connected to the :meth:`pause` or
        :meth:`stop` slots).

        States
        ----------
        If this worker is in the :attr:`_ThreadWorkerState.IDLE` state, this
        slot changes to the :attr:`_ThreadWorkerState.WORKING` state and calls
        the subclass :meth:`_work` method.

        If this worker is in the :attr:`_ThreadWorkerState.PAUSED` state, this
        slot interprets this signal as a request to resume the work presumably
        previously performed by this worker by a prior signalling of this slot.
        To avoid reentrancy issues, this slot changes to the
        :attr:`_ThreadWorkerState.WORKING` state and immediately returns.
        Assuming that a prior call to this slot is still executing, that call
        will internally detect this change and resume working as expected.

        If this worker is in the :attr:`_ThreadWorkerState.WORKING` state, this
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
        if self._state is _ThreadWorkerState.PAUSED:
            logs.log_debug(
                'Resuming thread "%d" worker "%s" '
                'via reentrant start() slot...',
                guithread.get_current_thread_id(), self.obj_name)
            self._state = _ThreadWorkerState.WORKING
            return

        # If this worker is currently running, resume the prior call to this
        # start() slot by preserving the working state and returning. See the
        # method docstring for commentary. Unlike the prior logic, this logic
        # constitutes a non-fatal error and is logged as such.
        if self._state is _ThreadWorkerState.WORKING:
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
        self._state = _ThreadWorkerState.WORKING

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
            self._work(arbitrary_str)

            # Note the _work() method called above to have returned successfully
            # (i.e., *WITHOUT* raising exceptions).
            is_success = True

            # If the state of this worker is still the working state, set this
            # state to the idle (i.e., non-working) state to preserve sanity.
            if self._state is _ThreadWorkerState.WORKING:
                self._state = _ThreadWorkerState.IDLE
        # If a periodic call to the _halt_work_if_requested() method performed
        # within the above call detects either this worker or this worker's
        # thread has been externally requested to stop, do so gracefully by...
        # doing absolutely nothing. Welp, that was easy.
        except _ThreadWorkerStopException:
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


    @Slot()
    def stop(self) -> None:
        '''
        Slot stopping all work performed by this worker.

        This slot prematurely halts this work in a thread-safe manner. Whether
        this work is safely restartable (e.g., by emitting a signal connected to
        the :meth:`start` slot) is a subclass-specific implementation detail.
        Subclasses may voluntarily elect to either prohibit or permit restarts.

        States
        ----------
        If this worker is in the :attr:`_ThreadWorkerState.IDLE` state, this
        slot silently reduces to a noop and preserves the existing state. In
        this case, this worker remains idle.

        If this worker is in either the :attr:`_ThreadWorkerState.WORKING` or
        :attr:`_ThreadWorkerState.PAUSED`, implying this worker to either
        currently be or recently have been working, this slot changes the
        current state to the :attr:`_ThreadWorkerState.IDLE` state. In either
        case, this worker ceases working.
        '''

        # Log this change.
        logs.log_debug(
            'Stopping thread "%d" worker "%s"...',
            guithread.get_current_thread_id(), self.obj_name)

        # If this worker is currently working or paused, stop this worker.
        if self._state is not _ThreadWorkerState.IDLE:
            self._state = _ThreadWorkerState.IDLE

    # ..................{ SLOTS ~ pause                      }..................
    @Slot()
    def pause(self) -> None:
        '''
        Slot pausing all work performed by this worker.

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
        if self._state is not _ThreadWorkerState.WORKING:
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
        self._state = _ThreadWorkerState.PAUSED

        # While this worker's state is paused, wait for the resume() slot to be
        # externally signalled by another object (typically in another thread).
        while self._state is _ThreadWorkerState.PAUSED:
            guithread.wait_for_events_if_none(event_dispatcher)


    @Slot()
    def resume(self) -> None:
        '''
        Slot **resuming** (i.e., unpausing) this worker.

        This slot resumes working in a thread-safe manner safely re-pausable at
        any time (e.g., by re-emitting a signal connected to the :meth:`pause`
        slot).

        States
        ----------
        If this worker is in either of the following states, this slot silently
        reduces to a noop and preserves the existing state:

        * :attr:`_ThreadWorkerState.IDLE`, implying this worker to *not*
          currently be paused. In this case, this worker remains idle.
        * :attr:`_ThreadWorkerState.WORKING`, implying this worker to already
          have been resumed. In this case, this worker remains working.

        See the :meth:`pause` slot for commentary on this design decision.
        '''

        # Log this change.
        logs.log_debug(
            'Resuming thread "%d" worker "%s"...',
            guithread.get_current_thread_id(), self.obj_name)

        # If this worker is currently paused, unpause this worker.
        if self._state is _ThreadWorkerState.PAUSED:
            self._state = _ThreadWorkerState.WORKING

    # ..................{ METHODS ~ abstract                 }..................
    # Abstract methods required to be redefined by subclasses.

    #FIXME: Obviously, forcing "str" usage is awful. See above for solutions.
    def _work(self, arbitrary_str: str) -> None:
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
        _ThreadWorkerStopException
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
            self._state is _ThreadWorkerState.IDLE or
            # This worker's thread has been externally requested to stop...
            guithread.should_halt_thread_work()
        # Then
        ):
            # Log this interrupt.
            logs.log_debug(
                'Interrupting thread "%d" worker "%s"...',
                guithread.get_current_thread_id(), self.obj_name)

            # Instruct the parent start() slot to stop.
            raise _ThreadWorkerStopException('So say we all.')
