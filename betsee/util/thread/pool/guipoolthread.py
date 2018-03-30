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
# from PySide2.QtCore import (
#     QAbstractEventDispatcher, QCoreApplication, QEventLoop, QThread)
# from betse.util.io.log import logs
# from betse.util.type.types import type_check
# from betsee.guiexception import BetseePySideThreadException
# from betsee.util.type.guitype import (
#     QAbstractEventDispatcherOrNoneTypes, QThreadOrNoneTypes)

# ....................{ GETTERS ~ current : thread         }....................
def get_thread_pool() -> QThreadPool:
    '''
    Singleton **worker thread pool** (i.e., platform-portable, pure-Qt,
    :class:`QThreadPool`-based container of one or more threads, each running
    exactly one :class:`QRunnable`-based worker at a given time).

    This singleton is safely reusable across the entire application.
    '''

    return QThreadPool.globalInstance()
