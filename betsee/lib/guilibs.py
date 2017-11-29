#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **application dependency** (i.e., both mandatory and optional
third-party Python packages required by this application) facilities.

This low-level submodule defines functions intended to be called by high-level
submodules (e.g., :mod:`betse.cli.api.cliabc`) *before* attempting to import any
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
from betse.util.type.types import type_check
from betsee import guimetadeps

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

# ....................{ EXCEPTIONS                         }....................
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
