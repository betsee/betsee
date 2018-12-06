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
from betse.util.type.numeric import versions
# from betse.util.type.types import type_check, IterableTypes

# ....................{ GLOBALS                           }....................
VERSION_PARTS = PySide2.__version_info__
'''
Machine-readable :mod:`PySide2` version as an efficiently comparable tuple of
integers (e.g., ``(5, 6, 0, "a", 1)`` for the corresponding human-readable
version ``5.6.0~a1``).
'''

# ....................{ TESTERS                           }....................
@func_cached
def is_version_5_6_or_older() -> bool:
    '''
    ``True`` only if the currently installed version of :mod:`PySide2` targets
    the Qt 5.6 (LTS) line of stable releases or older (e.g., Qt 5.5.0, Qt
    5.6.1).

    Versions of :mod:`PySide2` targetting such obsolete releases are well-known
    to suffer a medley of critical defects, including:

    * The entire :mod:`pyside2uic` package, which converts working
      XML-formatted user interface (UIC) files into broken pure-Python modules.
      Naturally, this is bad.
    '''

    return versions.is_less_than(VERSION_PARTS, '5.7.0')

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
