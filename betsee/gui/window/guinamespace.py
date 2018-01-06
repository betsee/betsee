#!/usr/bin/env python3
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Top-level classes defining this application's main window.

Motivation
----------
To avoid collisions between the names assigned by PySide2's UI compiler (UIC)
to widget variables owned by the current :class:`QBetseeMainWindow` instance,
these names are typically prefixed by common substrings signifying ad-hoc
namespaces. For example, all widgets with variable names prefixed by
``sim_conf_stack_page_`` signify pages of the top-level stack widget.

For maintainability, these prefixes are centralized here rather than chaotically
dispersed throughout the codebase.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.gui.window"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ GLOBALS ~ sim conf                 }....................
SIM_CONF_STACK_PAGE_NAME_PREFIX = 'sim_conf_stack_page_'
'''
Substring prefixing the name of each :class:`QBetseeMainWindow` variable
providing a page of the top-level stack widget for the main window.
'''
