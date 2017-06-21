#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Main entry point of this application's command line interface (CLI).

This submodule is a thin wrapper intended to be:

* Indirectly imported and run from external entry point scripts installed by
  setuptools (e.g., the ``betsee`` command).
* Directly imported and run from the command line (e.g., via
  ``python -m betsee.cli``).
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on missing mandatory dependencies,
# this module may import *ONLY* from standard Python packages and
# application-specific packages importing *ONLY* from standard Python packages.
# By definition, this excludes all third-party packages and most
# application-specific packages.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import sys
from betsee import metadata
from betsee.metadata import BETSE_VERSION_REQUIRED_MIN, NAME
from betsee.exceptions import BetseeException, BetseeLibException

# ....................{ MAIN                               }....................
def main(arg_list: list = None) -> int:
    '''
    Run this application's command-line interface (CLI) with the passed
    arguments if non-``None`` *or* with the arguments passed on the command line
    (i.e., :attr:`sys.argv`) otherwise.

    This function is provided as a convenience to callers requiring procedural
    functions rather than conventional methods (e.g., :mod:`setuptools`).

    Parameters
    ----------
    arg_list : list
        List of zero or more arguments to pass to this interface. Defaults to
        ``None``, in which case arguments passed on the command line (i.e.,
        :attr:`sys.argv`) will be used instead.

    Returns
    ----------
    int
        Exit status of this interface and hence this process as an unsigned byte
        (i.e., integer in the range ``[0, 255]``).
    '''

    # Validate whether BETSE is satisfied or not.
    try:
        _die_unless_betse()
    # If BETSE is unsatisfied, display this exception in an appropriate manner
    # and return the exit status of doing so.
    except BetseeLibException as exception:
        return _show_betse_exception(exception)

    # Else, BETSE is satisfied. Import us up the BETSEE package tree, most of
    # which assumes BETSE to be importable.
    from betsee.cli.climain import BetseeCLI

    # Run the BETSEE CLI and return the exit status of doing so.
    return BetseeCLI().run(arg_list)

# ....................{ EXCEPTIONS                         }....................
def _die_unless_betse() -> None:
    '''
    Raise an exception unless BETSE, the principal mandatory dependency of this
    application, is **satisfied** (i.e., both importable and of a version
    greater than or equal to that required by this application).

    Raises
    ----------
    BetseeLibException
        If BETSE is unsatisfied (i.e., either unimportable or of a version
        less than that required by this application).
    '''

    # Title of all exceptions raised below.
    EXCEPTION_TITLE = 'BETSE Unsatisfied'

    # Attempt to import BETSE.
    try:
        import betse
    # If BETSE is unimportable, chain this low-level "ImportError" exception
    # into a higher-level application-specific exception.
    except ImportError as import_error:
        raise BetseeLibException(
            title=EXCEPTION_TITLE,
            synopsis='BETSE not found.',
            exegesis='Python package "betse" not importable.',
        ) from import_error
    # Else, BETSE is importable.

    # Minimum version of BETSE required by this application as a
    # machine-readable tuple of integers. Since this tuple is only required once
    # (namely, here), this tuple is *NOT* persisted as a "metadata" global.
    BETSE_VERSION_REQUIRED_MIN_PARTS = metadata._convert_version_str_to_tuple(
        BETSE_VERSION_REQUIRED_MIN)

    # If the current version of BETSE is insufficient, raise an exception.
    if betse.__version_info__ < BETSE_VERSION_REQUIRED_MIN_PARTS:
        raise BetseeLibException(
            title=EXCEPTION_TITLE,
            synopsis='Obsolete version of BETSE found.',
            exegesis=(
                '{} requires at least BETSE {}, '
                'but only BETSE {} is currently installed.'.format(
                    NAME, BETSE_VERSION_REQUIRED_MIN, betse.__version__)))

    # raise BetseeLibException(
    #     title=EXCEPTION_TITLE,
    #     synopsis='BETSE not found.',
    #     exegesis='Python package "betse" not importable.',
    # )

# ....................{ EXCEPTIONS                         }....................
def _show_betse_exception(exception: BetseeException) -> int:
    '''
    Display the passed exception signifying BETSE to be unsatisfied in an
    appropriate manner.

    Parameters
    ----------
    exception : BetseeException
        Exception to be displayed.

    Returns
    ----------
    int
        Exit status implying failure (i.e., 1).
    '''

    assert isinstance(exception, BetseeLibException), (
        '"{}" not a BETSEE library exception.'.format(exception))

    # Always redirect this exception message to the standard error file handle
    # for the terminal running this CLI command if any.
    print(str(exception), file=sys.stderr)

    # Additionally attempt to...
    try:
        # Import PySide2.
        from betsee.util.io import psderr

        # Display a PySide2-based message box displaying this exception.
        psderr.show_exception(exception)
    # If PySide2 or any other module indirectly imported above is unimportable,
    # print this exception message in the same manner as above but otherwise
    # ignore this exception. Why? Because we have more significant fish to fry.
    except ImportError as import_error:
        print(str(import_error), file=sys.stderr)

    # Report failure to our parent process.
    return 1

# ....................{ MAIN                               }....................
# If this module is imported from the command line, run this application's CLI;
# else, noop. For POSIX compliance, the exit status returned by this function
# is propagated to the caller as this script's exit status.
if __name__ == '__main__':
    sys.exit(main())
