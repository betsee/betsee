#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
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
from betsee.metadata import (
    BETSE_VERSION_REQUIRED_MIN, NAME, convert_version_str_to_tuple)
from betsee.exceptions import BetseeLibException

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
        die_unless_betse()

    #FIXME: If the "PySide2.QtWidgets" subpackage is importable, display this
    #exception with a graphical dialogue error message; else, display the raw
    #text of this exception as is. For the former, something resembling the
    #following should suffice:
    #
    #    from PySide2.QtWidgets import QApplication, QPushButton
    #
    #    betse_unsatisfied_window = QApplication()
    #    betse_unsatisfied_widget = QPushButton(str(exception))
    #    betse_unsatisfied_widget.show()
    #    betse_unsatisfied_window.exec_()

    # If BETSE is unsatsified, display this exception in an appropriate manner.
    except BetseeLibException as exception:
        # If the "PySide2.QtWidgets" subpackage is importable, embed this
        # exception message in a GUI-enabled modal dialogue box.

        # Else, redirect this exception message to the standard error file
        # handle for the terminal running this CLI command.
        print(str(exception), file=sys.stderr)

        # In either case, report failure to our parent process.
        return 1

    #FIXME: Uncomment after worky.
    # from betsee.cli.climain import CLIMain
    # return CLIMain().run(arg_list)
    return 0

# ....................{ EXCEPTIONS                         }....................
def die_unless_betse() -> None:
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

    # Attempt to import BETSE.
    try:
        import betse
    # If BETSE is unimportable, chain this low-level "ImportError" exception
    # into a higher-level application-specific exception.
    except ImportError as import_error:
        raise BetseeLibException(
            'BETSE not found (i.e., package "betse" not importable).'
        ) from import_error
    # Else, BETSE is importable.

    # Minimum version of BETSE required by this application as a
    # machine-readable tuple of integers. Since this tuple is only required once
    # (namely, here), this tuple is *NOT* persisted as a "metadata" global.
    BETSE_VERSION_REQUIRED_MIN_PARTS = convert_version_str_to_tuple(
        BETSE_VERSION_REQUIRED_MIN)

    # If the current version of BETSE is insufficient, raise an exception.
    if betse.__version_info__ < BETSE_VERSION_REQUIRED_MIN_PARTS:
        raise BetseeLibException(
            '{} requires at least BETSE {}, '
            'but only BETSE {} is currently installed. '
            'Endless sorrow is a feeling deep inside.'.format(
                NAME, BETSE_VERSION_REQUIRED_MIN, betse.__version__))

# ....................{ MAIN                               }....................
# If this module is imported from the command line, run this application's CLI;
# else, noop. For POSIX compliance, the exit status returned by this function
# is propagated to the caller as this script's exit status.
if __name__ == '__main__':
    sys.exit(main())
