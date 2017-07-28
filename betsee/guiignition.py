#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
High-level application initialization common to both the CLI and GUI.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To defer heavyweight and possibly circular imports, the top-level of
# this module may import *ONLY* from standard Python packages. All imports from
# application and third-party packages should be deferred to their point of use.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ INITIALIZERS                       }....................
def reinit() -> None:
    '''
    (Re)-initialize the current application with sane defaults.

    Specifically, this function (in order):

    #. Initializes all lower-level BETSE logic by calling the
       :func:`betse.ignition.init` function.
    #. Validates but does *not* initialize mandatory third-party dependencies of
       this application, which must be initialized independently by the
       :func:`betsee.lib.libs.init` function.

    Design
    ----------
    To support caller-specific error handling, this function is intended to be
    called immediately *after* this application begins catching otherwise
    uncaught exceptions.

    Whereas BETSE is intended to be both run non-interactively from the
    command-line and imported interactively from Python REPLs (e.g., Jupyter),
    BETSEE is intended to only be run non-interactively from desktop application
    launchers. In the former case, BETSE detects and ignores attempts to
    re-initialize itself in the same application process. In the latter case, no
    re-initialization is expected, detected, or ignored.
    '''

    # Defer heavyweight and possibly circular imports.
    from betse import ignition as betse_ignition
    from betsee.lib import libs as betsee_libs

    # Initialize all lower-level BETSE logic *BEFORE* any higher-level BETSEE
    # logic assuming the former to "be sane." See the
    # betse.climain.BetseCLI._ignite_app() method for details on why the
    # betse_ignition.reinit() rather than betse_ignition.init() function is
    # called here.
    betse_ignition.reinit()

    # Validate mandatory dependencies. Avoid initializing these dependencies
    # here (e.g., by calling libs.init()), which requires the logging
    # configuration to have been finalized (e.g., by parsing CLI options), which
    # has yet to occur this early in the application lifecycle.
    betsee_libs.die_unless_runtime_mandatory_all()
