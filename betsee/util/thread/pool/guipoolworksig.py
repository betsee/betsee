#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **pooled worker signals** (i.e., collection of all :class:`Signal`
instances thread-safely emittable by the :meth:`QBetseeThreadPoolWorker.run`
method from an arbitrary pooled thread possibly running *no* Qt event loop)
classes.
'''

#FIXME: To avoid thread and widget (de)synchronization issues, we should also
#connect the "paused" and "resumed" signals defined below to corresponding
#slots of the "QBetseeSimmer" controller.

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QObject, Signal
# from betse.util.io.log import logs
from betse.util.type.types import type_check, CallableTypes

# ....................{ SUPERCLASSES                      }....................
class QBetseeThreadPoolWorkerSignals(QObject):
    '''
    Low-level **pooled worker signals** (i.e., collection of all
    :class:`Signal` instances thread-safely emittable by the
    :meth:`QBetseeThreadPoolWorker.run` method from an arbitrary pooled thread
    possibly running *no* Qt event loop).

    Each instance of this class is owned by a pooled worker (i.e.,
    :class:`QBetseeThreadPoolWorker` instance), whose :meth:`run` method emits
    signals defined by this class typically connected to slots defined by
    objects residing in the original thread in which this worker was
    instantiated (e.g., the main event thread).

    Signal Emission
    ----------
    External callers attempting to emit signals defined by this collection
    should typically prefer to call the higher-level wrapper methods whose
    names are prefixed by ``emit_`` (e.g., :meth:`emit_progress_range`) in
    lieu of the associate lower-level signals (e.g., :attr:`progress_ranged`).
    The former wrap the latter with essential multithreading handling,
    including guaranteeably calling the vital :meth:`halt_work_if_requested`
    method *after* emitting each such signal. Nonetheless, to permit these
    signals to be trivially connected to, these signals necessarily remain
    public rather than private variables.

    Thread Affinity
    ----------
    Each instance of this class resides in the original thread in which this
    worker was instantiated and resides. Hence, neither this class nor any
    subclass of this class should define slots. Why? Qt would execute these
    slots in that original thread rather than the thread running this worker.

    Attributes
    ----------
    _halt_work_if_requested : CallableTypes
        Callable temporarily or permanently halting all business logic
        performed by the parent worker that owns this collection when requested
        to do so by external callers residing in other threads. For
        convenience, this is typically the
        :meth:`guipoolwork.QBetseeThreadPoolWorker._halt_work_if_requested`
        method bound to this parent worker.
    '''

    # ..................{ SIGNALS                           }..................
    started = Signal()
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method
    immediately before running the :meth:`QBetseeThreadPoolWorker._work` method
    performing all subclass-specific business logic, passed the minimum.
    '''

    # ..................{ SIGNALS ~ progress                }..................
    progress_ranged = Signal(int, int)
    '''
    Signal optionally emitted by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed the pair of integers
    ``progress_min`` and ``progress_max`` signifying the minimum and maximum
    **progress values** (i.e., integers subsequently emitted by the
    :attr:`progressed` signal) for the parent worker.

    Caveats
    ----------
    **This signal is neither guaranteed to be emitted nor guaranteed to be
    emitted in a timely manner.** This signal is only emitted at the optional
    discretion of subclass-specific business logic. Thanks to this uncertainty,
    slots connected to this signal are advised to perform only non-essential
    logic (e.g., by calling only a :meth:`QProgressBar.setRange` method).

    This signal should be emitted by calling the higher-level
    :meth:`emit_progress_range` wrapper method rather than the lower-level
    :meth:`QSignal.emit` method of this signal.
    '''


    progressed = Signal(int)
    '''
    Signal optionally and repeatedly emitted by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed an integer signifying
    the current progress of work completed by the parent worker.

    This integer is assumed to be in the range ``[progress_min,
    progress_max]``, where ``progress_min`` and ``progress_max`` are the pair
    of integers previously emitted from the :attr:`progress_ranged` signal
    (assuming the :meth:`QBetseeThreadPoolWorker._work` method previously did
    so).

    Caveats
    ----------
    **This signal is neither guaranteed to be emitted nor guaranteed to be
    emitted in a timely manner.** This signal is only emitted at the optional
    discretion of subclass-specific business logic. Thanks to this uncertainty,
    slots connected to this signal are advised to perform only non-essential
    logic (e.g., by calling only a :meth:`QProgressBar.setValue` method).

    This signal should be emitted by calling the higher-level
    :meth:`emit_progress` wrapper method rather than the lower-level
    :meth:`QSignal.emit` method of this signal.
    '''

    # ..................{ SIGNALS ~ paused                  }..................
    paused = Signal()
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker._block_work` method
    immediately before indefinitely blocking the parent worker.
    '''


    resumed = Signal()
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker._block_work` method
    immediately after unblocking the parent worker.
    '''

    # ..................{ SIGNALS ~ finished                }..................
    finished = Signal(bool)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method
    immediately before returning from that method, passed either ``True`` if
    that method successfully performed all worker-specific business logic
    (i.e., if the :meth:`_work` method successfully returned *without* raising
    exceptions) *or* ``False`` otherwise.

    For finer-grained control over worker results, consider connecting instead
    to the:

    * :attr:`failed` signal for exceptions raised by the parent worker.
    * :attr:`succeeded` signal for objects returned by the parent worker.
    '''


    failed = Signal(Exception)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method on
    catching a fatal exception raised by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed this exception as is.

    Usage
    ----------
    Since this is Python 3.x rather than Python 2.x, slots connected to this
    signal may trivially reraise this exception from any other thread (complete
    with a contextual traceback specific to the stack for this thread) via the
    usual ``from`` clause of a ``raise`` statement.

    For this reason, this signal was intentionally designed *not* to emit the
    3-tuple returned by the standard :func:`sys.exc_info` function -- as would
    be required under Python 2.x to properly reraise this exception. Note that
    a little-known alternative to the ``from`` clause of a ``raise`` statement
    does technically exist: the :meth:`Exception.with_traceback` method. By
    explicitly calling this method on a newly instantiated exception passed
    `sys.exc_info()[2]`` (e.g., as ``raise
    MyNewException('wat?').with_traceback(sys.exc_info()[2])``), a similar
    effect is achievable. Since this is substantially less trivial, however,
    the prior approach is currently preferred.
    '''


    succeeded = Signal(object)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method on
    successfully completing the parent worker, passed the arbitrary value
    returned by the subclass-specific :meth:`QBetseeThreadPoolWorker._work`
    method if that method returned a value *or* ``None`` otherwise (i.e., in
    the case that method returned no value).
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def __init__(self, halt_work_if_requested: CallableTypes) -> None:
        '''
        Initialize this pooled worker signals collection.

        Parameters
        ----------
        halt_work_if_requested : CallableTypes
            Callable temporarily or permanently halting all business logic
            performed by the parent worker that owns this collection when
            requested to do so by external callers residing in other threads.
            For convenience, this is typically the
            :meth:`guipoolwork.QBetseeThreadPoolWorker._halt_work_if_requested`
            method bound to this parent worker. Accepting a reference to this
            method rather than this parent worker avoids circular object
            references between this parent worker and this child collection.
        '''

        # Initialize our superclass.
        super().__init__()

        # Classify all passed parameters.
        self._halt_work_if_requested = halt_work_if_requested

    # ..................{ EMITTERS ~ progress               }..................
    @type_check
    def emit_progress_range(
        self, progress_min: int, progress_max: int) -> None:
        '''
        Emit the :attr:`progress_ranged` signal with the passed range of all
        possible **progress values** (i.e., integers subsequently emitted by
        the :attr:`emit_progress` signal method) for the parent worker.

        Parameters
        ----------
        progress_min : int
            Minimum progress value emitted by :attr:`emit_progressed`.
        progress_max : int
            Maximum progress value emitted by :attr:`emit_progressed`.

        See Also
        ----------
        :attr:`progress_ranged`
            Further details.
        '''

        # Signal all slots connected to this signal with these parameters.
        self.progress_ranged.emit(progress_min, progress_max)

        # Temporarily or permanently halt all worker-specific business logic
        # when requested to do so by external callers in other threads *AFTER*
        # successfully emitting this signal.
        self._halt_work_if_requested()


    @type_check
    def emit_progress(self, progress: int) -> None:
        '''
        Emit the :attr:`progressed` signal with the passed **progress value**
        (i.e., integer signifying the progress of work completed) for the
        parent worker.

        Parameters
        ----------
        progress : int
            Integer signifying the progress of work completed.

        See Also
        ----------
        :attr:`progressed`
            Further details.
        '''

        # Signal all slots connected to this signal with these parameters.
        self.progressed.emit(progress)

        # Temporarily or permanently halt all worker-specific business logic
        # when requested to do so by external callers in other threads *AFTER*
        # successfully emitting this signal.
        self._halt_work_if_requested()
