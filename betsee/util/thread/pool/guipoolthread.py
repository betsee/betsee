#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **worker thread pool** (i.e., platform-portable, pure-Qt,
:class:`QThreadPool`-based container of one or more threads, each running
exactly one :class:`QRunnable`-based worker at a given time) classes.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QThreadPool
# from betse.util.io.log import logs
from betse.util.type.types import type_check
# from betsee.guiexception import BetseePySideThreadException
from betsee.util.type.guitype import QThreadPoolOrNoneTypes
from betsee.util.thread.pool.guipoolwork import QBetseeThreadPoolWorker

# ....................{ TESTERS                            }....................
@type_check
def is_worker(thread_pool: QThreadPoolOrNoneTypes = None) -> bool:
    '''
    ``True`` only if one or more workers are currently running in one or more
    non-idle threads of the passed thread pool.

    Parameters
    ----------
    thread_pool : QThreadPoolOrNoneTypes
        Thread pool to run this worker in. Defaults to ``None``, in which case
        the singleton thread pool returned by the :func:`get_thread_pool`
        function is defaulted to.
    '''

    # Default this thread pool to the singleton thread pool if needed.
    if thread_pool is None:
        thread_pool = get_thread_pool()

    # Return true only if this thread pool has at least one non-idle thread.
    return thread_pool.activeThreadCount() > 0

# ....................{ GETTERS                            }....................
def get_thread_pool() -> QThreadPool:
    '''
    Singleton **worker thread pool** (i.e., platform-portable, pure-Qt,
    :class:`QThreadPool`-based container of one or more threads, each running
    exactly one :class:`QRunnable`-based worker at a given time).

    This singleton is globally reusable across the entire application.
    '''

    return QThreadPool.globalInstance()

# ....................{ RUNNERS                            }....................
@type_check
def run_worker(
    worker: QBetseeThreadPoolWorker,
    thread_pool: QThreadPoolOrNoneTypes = None,
) -> None:
    '''
    Run the passed thread pool worker in the passed thread pool.

    Specifically, this function:

    * If this thread pool contains at least one idle thread:
      * Moves this worker from the original thread in which this worker was
        instantiated into this idle thread.
      * Calls the :meth:`QBetseeThreadPoolWorker.run` method of this worker.
      * Garbage collects this worker when this method returns.
    * Else, queues a request to subsequently run this worker in the next idle
      thread in this thread pool.

    Parameters
    ----------
    worker : QBetseeThreadPoolWorker
        Worker to be run in this thread pool.
    thread_pool : QThreadPoolOrNoneTypes
        Thread pool to run this worker in. Defaults to ``None``, in which case
        the singleton thread pool returned by the :func:`get_thread_pool`
        function is defaulted to.
    '''

    # Default this thread pool to the singleton thread pool if needed.
    if thread_pool is None:
        thread_pool = get_thread_pool()

    # Run this worker in this thread pool.
    thread_pool.start(worker)
