#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level PySide2 library facilities.
'''

# ....................{ IMPORTS                           }....................
import PySide2
from betse.util.io.log import logs
from betse.util.type.decorator.decmemo import func_cached
# from betse.util.type.types import type_check, IterableTypes

# ....................{ GGLOBALS                          }....................
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
    Initialize PySide2.

    Specifically, this function:

    * Monkey-patches *all* :mod:`PySide2` callables whose version-specific
      implementations are well-known to be broken (if any).
    '''

    # Avoid circular import dependencies.
    from betsee.lib.pyside2 import guipsdpatch

    # Log this initialization.
    logs.log_info('Loading PySide2...')

    # Conditionally monkey-patch PySide2 callables well-known to be broken.
    guipsdpatch.patch_all()
