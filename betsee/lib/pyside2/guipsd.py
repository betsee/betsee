#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2` facilities.
'''

# ....................{ IMPORTS                           }....................
import PySide2
from betse.util.io.log import logs
from betse.util.type.decorator.decmemo import func_cached
from betse.util.type.numeric import versions
from betse.util.type.types import type_check
from betsee.lib.pyside2.cache.guipsdcache import CachePolicy

# ....................{ GLOBALS                           }....................
VERSION = PySide2.__version__
'''
Human-readable :mod:`PySide2` version string (e.g., ``5.6.0~a1``).
'''

# ....................{ INITIALIZERS                      }....................
@type_check
def init(cache_policy: CachePolicy) -> None:
    '''
    Initialize :mod:`PySide2`.

    Specifically, this function:

    * Contextually caches all :mod:`PySide2`-based submodules required at
      runtime by this GUI.
    * Initializes PySide2-based multithreading facilities.

    Parameters
    ----------
    cache_policy : CachePolicy
        Type of :mod:`PySide2`-based submodule caching to be performed.
    '''

    # Avoid circular import dependencies.
    from betsee.lib.pyside2.cache import guipsdcache
    from betsee.util.thread import guithread

    # Log this initialization.
    logs.log_info('Initializing PySide2 %s...', VERSION)

    # Cache all PySide2-based submodules required at runtime by this GUI.
    guipsdcache.init(cache_policy=cache_policy)

    # Initialize PySide2-based multithreading facilities.
    guithread.init()

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

    return versions.is_less_than(VERSION, '5.7.0')
