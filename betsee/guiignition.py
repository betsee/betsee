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
    (Re-)initialize this application -- but *not* mandatory third-party
    dependencies of this application, which requires external resources (e.g.,
    command-line options, configuration files) to be parsed.

    Specifically, this function (in order):

    #. Initializes all lower-level BETSE logic by calling the
       :func:`betse.ignition.init` function.
    #. Validates but does *not* initialize mandatory third-party dependencies of
       this application, which must be initialized independently by the
       :func:`betsee.lib.guilibs.init` function.
    #. Validates that the active Python interpreter supports multithreading.

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

    See Also
    ----------
    :func:`betsee.lib.libs.reinit`
        Function (re)-initializing all mandatory third-party dependencies.
    '''

    # Defer heavyweight and possibly circular imports.
    from betse import ignition as betse_ignition
    from betse.util.py import pythread
    from betsee.lib import guilibs

    # Initialize all lower-level BETSE logic *BEFORE* any higher-level BETSEE
    # logic requiring the former. See the betse.guicli.BetseCLI._ignite_app()
    # method for details on why the betse_ignition.reinit() rather than
    # betse_ignition.init() function is called here.
    betse_ignition.reinit()

    # Validate mandatory dependencies *AFTER* BETSE is initialized.
    #
    # These dependencies are intentionally *NOT* initialized here (e.g., by
    # calling guilibs.init()), as doing so requires the logging configuration to
    # have been finalized (e.g., by parsing CLI options), which has yet to occur
    # this early in the application lifecycle.
    guilibs.die_unless_runtime_mandatory_all()

    # If the active Python interpreter does *NOT* support multithreading, raise
    # an exception *AFTER* BETSE is initialized.
    #
    # While Qt-based multithreading primitives are typically preferable to
    # Python-based multithreading primitives, the latter have their occasional
    # use. More critically, the lack of latter typically implies this
    # interpreter to be in insufficiently sane for our purposes.
    pythread.die_unless_threadable()
