#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Top-level classes defining this application's main window.

Motivation
----------
To avoid collisions between the names assigned by :mod:`PySide2`'s UI compiler
(UIC) to widget variables owned by the current :class:`QBetseeMainWindow`
instance, these names are typically prefixed or suffixed by common substrings
signifying ad-hoc namespaces. For example, all widgets with variable names
prefixed by :data:`SIM_CONF_STACK_PAGE_NAME_PREFIX` identify pages of the
top-level stack widget.

For maintainability, these prefixes and suffixes are centralized here rather
than chaotically dispersed throughout the codebase.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.gui.window"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ GLOBALS ~ sim conf                }....................
SIM_CONF_STACK_PAGE_ITEMIZED_NAME_SUFFIX = '_item'
'''
Substring suffixing the name of each :class:`QBetseeMainWindow` variable
providing an **itemized page** (i.e., page associated with zero or more tree
items masquerading as list items) of the top-level stack widget for the main
window.
'''


SIM_CONF_STACK_PAGE_NAME_PREFIX = 'sim_conf_stack_page_'
'''
Substring prefixing the name of each :class:`QBetseeMainWindow` variable
providing a page of the top-level stack widget for the main window.
'''
