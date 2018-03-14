#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **application dependency** (i.e., both mandatory and optional
third-party Python packages required by this application) facilities.

This low-level submodule defines functions intended to be called by high-level
submodules (e.g., :mod:`betse.util.cli.cliabc`) *before* attempting to import any
such dependencies.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on missing mandatory dependencies,
# the top-level of this module may import *ONLY* from packages guaranteed to
# exist at initial runtime (i.e., standard Python and application packages,
# including both BETSEE and BETSE packages).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from betse.lib import libs as betse_libs
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee import guimetadata, guimetadeps

# ....................{ EXCEPTIONS                         }....................
def die_unless_runtime_mandatory_all() -> None:
    '''
    Raise an exception unless all mandatory runtime dependencies of this
    application are **satisfiable** (i.e., both importable and of a satisfactory
    version) *and* all external commands required by these dependencies (e.g.,
    GraphViz's ``dot`` command) reside in the current ``${PATH}``.

    Raises
    ----------
    BetseLibException
        If at least one mandatory runtime dependency is unsatisfiable.

    See Also
    ----------
    :func:`betse_libs.die_unless_runtime_mandatory_all`
        Further details.
    '''

    betse_libs.die_unless_requirements_dict(
        guimetadeps.RUNTIME_MANDATORY)


@type_check
def die_unless_runtime_optional(*requirement_names: str) -> None:
    '''
    Raise an exception unless all optional runtime dependencies of this
    application with the passed :mod:`setuptools`-specific project names are
    **satisfiable** (i.e., both importable and of a satisfactory version)
    *and* all external commands required by these dependencies (e.g.,
    GraphViz's ``dot`` command) reside in the current ``${PATH}``.

    Parameters
    ----------
    requirement_names : Tuple[str]
        Tuple of the names of all :mod:`setuptools`-specific projects
        implementing these dependencies (e.g., ``NetworkX``). If any such name
        is unrecognized (i.e., is *not* a key of the
        :data:`guimetadeps.RUNTIME_OPTIONAL` dictionary), an exception is
        raised.

    Raises
    ----------
    BetseLibException
        If at least one such dependency is unsatisfiable.

    See Also
    ----------
    :func:`betse_libs.die_unless_runtime_mandatory_all`
        Further details.
    '''

    betse_libs.die_unless_requirements_dict_keys(
        guimetadeps.RUNTIME_OPTIONAL, *requirement_names)

# ....................{ TESTERS                            }....................
@type_check
def is_runtime_optional(*requirement_names: str) -> bool:
    '''
    ``True`` only if all optional runtime dependencies of this application with
    the passed :mod:`setuptools`-specific project names are **satisfiable**
    (i.e., both importable and of a satisfactory version) *and* all external
    commands required by these dependencies (e.g., GraphViz's ``dot`` command)
    reside in the current ``${PATH}``.

    Parameters
    ----------
    requirement_names : Tuple[str]
        Tuple of the names of all :mod:`setuptools`-specific projects
        implementing these dependencies (e.g., ``NetworkX``). If any such
        name is *not* a key of the :data:`guimetadeps.RUNTIME_OPTIONAL`
        dictionary and is thus unrecognized, an exception is raised.

    See Also
    ----------
    :func:`betse_libs.die_unless_runtime_mandatory_all`
        Further details.
    '''

    return betse_libs.is_requirements_dict_keys(
        guimetadeps.RUNTIME_OPTIONAL, *requirement_names)

# ....................{ IMPORTERS                          }....................
@type_check
def import_runtime_optional(*requirement_names: str) -> object:
    '''
    Import and return the top-level module object satisfying each optional
    runtime dependency of this application with the passed name.

    Parameters
    ----------
    requirement_names : tuple[str]
        Tuple of the names of all :mod:`setuptools`-specific projects
        implementing these dependencies (e.g., ``NetworkX``). If any such name
        is unrecognized (i.e., is *not* a key of the
        :data:`guimetadeps.RUNTIME_OPTIONAL` dictionary), an exception is
        raised.

    See Also
    ----------
    :func:`betse_libs.import_requirements_dict_keys`
        Further details.
    '''

    return betse_libs.import_requirements_dict_keys(
        guimetadeps.RUNTIME_OPTIONAL, *requirement_names)

# ....................{ INITIALIZERS                       }....................
def reinit() -> None:
    '''
    (Re-)initialize all mandatory runtime dependencies of this application,
    thus including both BETSE and BETSEE.
    '''

    # Defer heavyweight imports.
    from betsee.util.app import guiapp

    # Log this initialization. Since initializing heavyweight third-party
    # dependencies (especially matplotlib) consumes non-trivial time, this
    # message is intentionally exposed to all users by default.
    logs.log_info('Loading third-party %s dependencies...', guimetadata.NAME)

    # Initialize PySide2 by instantiating the "QApplication" singleton *BEFORE*
    # initializing BETSE dependencies. Why? The reason is subtle, but critical:
    # initializing BETSE initializes matplotlib with the "Qt5Agg" backend, which
    # instantiates the "QApplication" singleton if this singleton has *NOT*
    # already been initialized. However, various application-wide settings
    # (e.g., metadata, high-DPI scaling emulation) *MUST* be initialized before
    # this singleton is instantiated. Permitting "Qt5Agg" to instantiate this
    # singleton first prevents us from initializing these settings here. This
    # singleton *MUST* thus be instantiated by us first.
    guiapp.init()

    # Initialize all mandatory runtime dependencies of BETSE.
    betse_libs.reinit(matplotlib_backend_name='Qt5Agg')
