#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **pooled worker signals** (i.e., collection of all :class:`Signal`
instances thread-safely emittable by the :meth:`QBetseeThreadPoolWorker.run`
method from an arbitrary pooled thread possibly running *no* Qt event loop)
classes.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QObject, Signal
# from betse.exceptions import BetseMethodUnimplementedException
# from betse.util.io.log import logs
# from betse.util.type.types import type_check

#FIXME: To avoid thread and widget (de)synchronization issues, we should also
#connect the "paused" and "resumed" signals defined below to corresponding slots
#of the "QBetseeSimmer" controller.

# ....................{ SUPERCLASSES                       }....................
class QBetseeThreadPoolWorkerSignals(QObject):
    '''
    Low-level **pooled worker signals** (i.e., collection of all :class:`Signal`
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
    all subclass-specific business logic, passed the minimum.
    '''

    # ..................{ SIGNALS ~ progress                 }..................
    progress_ranged = Signal(int, int)
    '''
    Signal optionally emitted by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed the pair of integers
    ``progress_min`` and ``progress_max`` signifying the minimum and maximum
    **progress values** (i.e., integers subsequently emitted by the
    :attr:`progressed` signal) for this worker.

    Caveats
    ----------
    **This signal is neither guaranteed to be emitted nor guaranteed to be
    emitted in a timely manner.** This signal is only emitted at the optional
    discretion of subclass-specific business logic. Thanks to this uncertainty,
    slots connected to this signal are advised to perform only non-essential
    logic (e.g., by calling only a :meth:`QProgressBar.setRange` method).
    '''


    progressed = Signal(int)
    '''
    Signal optionally and repeatedly emitted by the subclass-specific
    :meth:`QBetseeThreadPoolWorker._work` method, passed an integer signifying
    the current progress of work completed by this worker.

    This integer is assumed to be in the range ``[progress_min, progress_max]``,
    where ``progress_min`` and ``progress_max`` are the pair of integers
    previously emitted from the :attr:`progress_ranged` signal (assuming the
    :meth:`QBetseeThreadPoolWorker._work` method previously did so).

    Caveats
    ----------
    **This signal is neither guaranteed to be emitted nor guaranteed to be
    emitted in a timely manner.** This signal is only emitted at the optional
    discretion of subclass-specific business logic. Thanks to this uncertainty,
    slots connected to this signal are advised to perform only non-essential
    logic (e.g., by calling only a :meth:`QProgressBar.setValue` method).
    '''

    # ..................{ SIGNALS ~ paused                   }..................
    paused = Signal()
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker._block_work` method
    immediately before indefinitely blocking this worker.
    '''


    resumed = Signal()
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker._block_work` method
    immediately after unblocking this worker.
    '''

    # ..................{ SIGNALS ~ finished                 }..................
    finished = Signal(bool)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method immediately
    before returning from that method, passed either ``True`` if that method
    successfully performed all worker-specific business logic (i.e., if the
    :meth:`_work` method successfully returned *without* raising exceptions)
    *or* ``False`` otherwise.

    For finer-grained control over worker results, consider connecting instead
    to the:

    * :attr:`failed` signal for exceptions raised by this worker.
    * :attr:`succeeded` signal for objects returned by this worker.
    '''


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


    succeeded = Signal(object)
    '''
    Signal emitted by the :meth:`QBetseeThreadPoolWorker.run` method on
    successfully completing this worker, passed the arbitrary value returned by
    the subclass-specific :meth:`QBetseeThreadPoolWorker._work` method if that
    method returned a value *or* ``None`` otherwise (i.e., in the case that
    method returned no value).
    '''
