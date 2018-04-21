#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **non-pooled worker** (i.e., thread-safe object implementing
generically startable, pausable, resumable, and haltable business logic in a
multithreaded manner intended to be moved to the thread encapsulated by a
:class:`QThread` object) classes.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QObject, Signal, Slot  # QCoreApplication,
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
# from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideThreadWorkerStopException
from betsee.util.thread import guithread
from betsee.util.thread.guithreadenum import ThreadWorkerState
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUPERCLASSES                       }....................
class QBetseeLoneThreadWorkerABC(QBetseeObjectMixin, QObject):
    '''
    Abstract base class of all low-level **non-pooled worker** (i.e.,
    thread-safe object implementing generically startable, pausable, resumable,
    and haltable business logic in a multithreaded manner intended to be adopted
    by the thread encapsulated by a :class:`QBetseeLoneThread` object)
    subclasses.

    By default, workers are recyclable and hence may be reused (i.e., have their
    :meth:`start` slots signalled) an arbitrary number of times within any
    arbitrary thread. Where undesirable, see the
    :cless:`QBetseeLoneThreadWorkerThrowawayABC` for an alternative superclass
    constraining workers to be non-recyclable.

    Caveats
    ----------
    This obsolete superclass has been superceded by the superior
    :class:`betse.util.thread.pool.guipoolwork.QBetseeThreadPoolWorker`
    superclass, whose :class:`QRunnable`-based API requires substantially less
    boilerplate.

    Attributes
    ----------
    _state : ThreadWorkerState
        Current execution state of this worker. For thread-safety, this state
        should *not* be externally accessed by objects residing in other
        threads. Doing so safely would require thread-safe mutual exclusion
        (e.g., with a dedicated :class:`QMutexLocker` context manager), which
        currently exceeds the mandate of this superclass.

    See Also
    ----------
    https://codereview.stackexchange.com/a/173258/124625
        StackOverflow answer strongly inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self) -> None:
        '''
        Initialize this worker.

        Caveats
        ----------
        This method intentionally accepts *no* passed parameters and hence
        cannot be passed a parent `QObject`. So, this worker is **unparented**
        (i.e., has no such parent). Why? Because this worker will be
        subsequently adopted into a different thread than the original thread in
        which this worker was instantiated. However, most candidate `QObject`
        parents of this worker would presumably reside in that original thread.
        Objects in different threads should typically *not* control the
        lifecycle of each other, as the parent of a child `QObject` does;
        doing so typically violates thread-safety. (That's bad.)
        '''

        # Initialize our superclass with *NO* passed parameters. (See above.)
        super().__init__()

        # Default this worker's initial state to the idle state.
        self._state = ThreadWorkerState.IDLE

        # Connect this worker's external-facing signals to corresponding slots.
        self.start_signal .connect(self.start)
        self.stop_signal  .connect(self.stop)
        self.pause_signal .connect(self.pause)
        self.resume_signal.connect(self.resume)

    # ..................{ SIGNALS ~ external                 }..................
    # Signals externally emitted by callers owning instances of this superclass.

    #FIXME: Obviously, requiring a string be unconditionally passed to all
    #start_signal() invocations is... well, insane. Instead, this should be
    #refactored as follows:
    #
    #* Define a new "QBetseeLoneThreadWorkerStartArgsABC(QObject)" class in this
    #  or possibly another submodule (e.g., "guiworkerstartcls").
    #* Rewrite this signal to simply read:
    #     start_signal = Signal(QBetseeLoneThreadWorkerStartArgsABC)
    #* Rewrite the start() slot and _work() methods defined below to similarly
    #  accept instances of this "QBetseeLoneThreadWorkerStartArgsABC" class rather
    #  than... raw strings. *sigh*
    #* Refactor all subclasses of this class similarly.
    #* Refactor all emissions of this signal to emit
    #  "QBetseeLoneThreadWorkerStartArgsABC" instances rather than raw strings.
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
            self._work(arbitrary_str)

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

# ....................{ SUPERCLASSES ~ throwaway           }....................
class QBetseeLoneThreadWorkerThrowawayABC(QBetseeLoneThreadWorkerABC):
    '''
    Abstract base class of all low-level **throw-away non-pooled worker** (i.e.,
    non-pooled worker guaranteed to be garbage-collected after completing its
    work) subclasses.

    Equivalently, this is the superclass of all single-use, one-shot, one-time,
    non-recyclable non-pooled workers. By default, workers are recyclable and
    hence may be reused (i.e., have their :meth:`start` slots signalled) an
    arbitrary number of times within any arbitrary thread. Instances of this
    superclass are non-recyclable and hence may *not* be reused more than once,
    however.

    Usage
    ----------
    Ideally, the :meth:`start` slot of each instance of this superclass should
    be signalled at most once. Immediately *after* performing all
    subclass-specific work via the :meth:`_work` method, this slot (in order):

    #. Emits the :attr:`finished` signal.
    #. Signals itself to be garbage-collected via the :meth:`deleteLater` slot.
    #. Returns.

    After returning from the :meth:`start` slot, all external references to this
    worker are effectively invalidated and hence equivalent to ``None``; no such
    worker may be safely used for *any* subsequent purposes.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        #FIXME: Sadly, this connection now appears to induce segmentation
        #faults on worker completion. Our intuitive suspicion is that the
        #"finished" signal now emits booleans, which are probably being passed
        #to the deleteLater() slot, which doesn't expect to receive boolean
        #parameters and hence... fatally crashes? It seems to be the case,
        #curiously. The solution, of course, would be to connect the "finished"
        #signal to a new slot accepting (and ignoring) a passed boolean and
        #simply calling the self.deleteLater() slot directly -- say:
        #
        #   @Slot(bool)
        #   def _schedule_deletion(self, is_success: bool) -> None:
        #       '''
        #       Schedule this thread worker and *all* :class:`QObject` instances
        #       owned by this worker for subsequent deletion.
        #       '''
        #
        #       self.deleteLater()

        # Garbage collect all child objects of this parent worker *AFTER* this
        # worker gracefully (i.e., successfully) terminates.
        # self.finished.connect(self.deleteLater)
