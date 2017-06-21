#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for :mod:`PySide2`, the principal mandatory
runtime dependency of this application.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT* include
#   BETSE modules, which is *NOT* guaranteed to exist at this point. For
#   simplicity, PySide2 is assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtWidgets import QApplication

# ....................{ GLOBALS                            }....................
# For safety, initialize this widget with *NO* command-line arguments regardless
# of whether the current application CLI was passed arguments. The subset of
# arguments parsed by this widget appear to have little to no consequence to end
# users and developers alike. Since this widget consumes all arguments it
# parses, permitting this widget to arbitrarily parse and hence consume
# arguments encourages conflicts with future versions of Qt. In theory, Qt could
# expand the subset of arguments parsed by this widget to those already parsed
# by the current application CLI -- which would be bad.
APP_WIDGET = QApplication([])
'''
:mod:`PySide2`-driven root Qt widget containing all Qt widgets to be displayed.

For safety, this instance is persisted as a module rather than local variable
(e.g., of the :func:`_show_betse_exception` function). Since the order in which
Python garbage collects local variables that have left scope is effectively
random, persisting this instance as a local variable would permit Python to
garbage collect this application *before* this application's child widgets on
program termination, resulting in non-human-readable Qt exceptions on some but
not all terminations. (That would be bad.)

See Also
----------
:data:`PySide2.QtWidgets.qApp`
    Synonym of this attribute, providing the same underlying instance.
'''
