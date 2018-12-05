#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2` facilities.
'''

# ....................{ IMPORTS                           }....................
import PySide2
from betse.util.io.log import logs
from betse.util.type.decorator.decmemo import func_cached
# from betse.util.type.types import type_check, IterableTypes

# ....................{ GLOBALS                           }....................
VERSION_PARTS = PySide2.__version_info__
'''
Machine-readable :mod:`PySide2` version as a tuple of integers (e.g.,
``(5, 6, 0, "a", 1)`` for the corresponding human-readable version
``5.6.0~a1``).
'''

# ....................{ TESTERS                           }....................
@func_cached
def is_version_5_6() -> bool:
    '''
    ``True`` only if the currently installed version of :mod:`PySide2` targets
    the long-obsolete Qt 5.6 (LTS) line of stable releases.
    '''

    return VERSION_PARTS[0:2] == (5, 6)

# ....................{ INITIALIZERS                      }....................
def init() -> None:
    '''
    Initialize :mod:`PySide2`.

    Specifically, this function:

    * Contextually caches all :mod:`PySide2`-based submodules required at
      runtime by this GUI.
    '''

    # Avoid circular import dependencies.
    from betsee.lib.pyside2.cache import guipsdcache

    # Log this initialization.
    logs.log_info('Initializing PySide2...')

    # Cache all PySide2-based submodules required at runtime by this GUI.
    guipsdcache.init()
