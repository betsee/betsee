#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
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

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on missing mandatory
# dependencies, this module may import *ONLY* from standard Python packages and
# application-specific packages importing *ONLY* from standard Python packages.
# By definition, this excludes all third-party packages and most
# application-specific packages.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import sys
from betsee import guimetadata, guimetadeps

# ....................{ EXCEPTIONS                        }....................
class _BetseNotFoundException(Exception):
    '''
    Exception raised on detecting BETSE (i.e., this application's core
    mandatory dependency) to be unimportable by the active Python interpreter.

    Design
    ----------
    This subclass intentionally complies with the public API of the
    :class:`betsee.guiexception.BetseeException` superclass to enable duck
    typing between the two classes (e.g., by the
    :func:`betsee.util.io.ioerr.show_exception` function). As the
    :mod:`betsee.guiexception` submodule necessarily imports from and hence
    assumes the importability of the mandatory third-party :mod:`PySide2`
    package whose importability has *not* yet been validated at this early time
    in the application lifecycle, this submodule *cannot* safely import from
    that submodule and hence explicitly subclass that superclass.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, title: str, synopsis: str, exegesis: str) -> None:

        # Initialize our superclass.
        super().__init__(synopsis)

        # Classify all passed parameters to enable duck typing.
        self.title = title
        self.synopsis = synopsis
        self.exegesis = exegesis

# ....................{ MAIN                              }....................
def main(arg_list: list = None) -> int:
    '''
    Run this application's command-line interface (CLI) with the passed
    arguments if non-``None`` *or* with the arguments passed on the command
    line (i.e., :attr:`sys.argv`) otherwise.

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
        Exit status of this interface and hence this process as an unsigned
        byte (i.e., integer in the range ``[0, 255]``).
    '''

    # Validate BETSE to be satisfied *BEFORE* attempting to import from this
    # application's package tree, most of which requires BETSE.
    try:
        _die_unless_betse()
    # If BETSE is unsatisfied, display this exception in an appropriate manner
    # and return the exit status of doing so.
    except _BetseNotFoundException as exception:
        return _show_betse_exception(exception)

    # Import from this application's package tree *AFTER* validating BETSE.
    from betsee.cli.guicli import BetseeCLI

    # Run this application's CLI and return the exit status of doing so.
    return BetseeCLI().run(arg_list)

# ....................{ EXCEPTIONS                        }....................
def _die_unless_betse() -> None:
    '''
    Raise an exception unless BETSE, the principal mandatory dependency of this
    application, is **satisfied** (i.e., both importable and of a version
    greater than or equal to that required by this application).

    Raises
    ----------
    _BetseNotFoundException
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
        raise _BetseNotFoundException(
            title=EXCEPTION_TITLE,
            synopsis='Mandatory dependency BETSE not found.',
            exegesis='Python package "betse" unimportable.',
        ) from import_error
    # Else, BETSE is importable.

    # Minimum version of BETSE required by this application as a
    # machine-readable tuple of integers. This tuple is only required once
    # (i.e., here) and hence *NOT* persisted as a "guimetadata" global.
    BETSE_VERSION_MIN_PARTS = (
        guimetadata._convert_version_str_to_tuple(
            guimetadeps.BETSE_VERSION_MIN))

    # If the current version of BETSE is insufficient, raise an exception.
    if betse.__version_info__ < BETSE_VERSION_MIN_PARTS:
        raise _BetseNotFoundException(
            title=EXCEPTION_TITLE,
            synopsis='Obsolete version of mandatory dependency BETSE found.',
            exegesis=(
                '{} {} requires at least BETSE {}, '
                'but only BETSE {} is currently installed.'.format(
                    guimetadata.NAME,
                    guimetadata.VERSION,
                    guimetadeps.BETSE_VERSION_MIN,
                    betse.__version__,
                )))

    # Purely for testing purposes.
    # raise _BetseNotFoundException(
    #     title=EXCEPTION_TITLE,
    #     synopsis='BETSE not found.',
    #     exegesis='Python package "betse" not importable.',
    # )

# ....................{ PRINTERS                          }....................
def _show_betse_exception(exception: _BetseNotFoundException) -> int:
    '''
    Display the passed exception signifying BETSE to be unsatisfied in an
    appropriate manner.

    Parameters
    ----------
    exception : _BetseNotFoundException
        Exception to be displayed.

    Returns
    ----------
    int
        Exit status implying failure (i.e., 1).
    '''

    assert isinstance(exception, _BetseNotFoundException), (
        '"{}" not a BETSE-not-found exception.'.format(exception))

    # Exception message to be redirected to standard error, crudely synthesized
    # from the synopsis and exegesis embedded in the passed exception.
    exception_stderr_message = '{} (i.e., {}).'.format(
        _remove_suffix_if_found(text=exception.synopsis, suffix='.'),
        _remove_suffix_if_found(text=exception.exegesis, suffix='.'))

    # Always redirect this exception message to the standard error file handle
    # for the terminal running this CLI command (if any).
    print(exception_stderr_message, file=sys.stderr)

    # Additionally attempt to...
    try:
        # Import PySide2.
        from betsee.util.io import guierror

        # Display a PySide2-based message box displaying this exception.
        guierror.show_exception(exception)
    # If PySide2 or any other module indirectly imported above is unimportable,
    # print this exception message in the same manner as above but otherwise
    # ignore this exception. Why? Because we have more significant fish to fry.
    except ImportError as import_error:
        print(str(import_error), file=sys.stderr)

    # Report failure to our parent process.
    return 1

# ....................{ PRINTERS                          }....................
def _remove_suffix_if_found(text: str, suffix: str) -> str:
    '''
    Passed string with the passed suffix removed if present *or* the passed
    string as is otherwise.

    Parameters
    ----------
    text : str
        String to be examined. Since strings are immutable in Python, this
        string remains unmodified.
    suffix : str
        Suffix to remove from this string.

    Returns
    ----------
    str
        Resulting string as described above.

    See Also
    ----------
    :func:`betse.util.type.text.strs.remove_suffix_if_found`
        Original function from which this function is copy-and-pasted. Although
        BETSE is a mandatory dependency of this application, BETSE is *not*
        guaranteed to exist this "early" in the application startup.
    '''

    # See betse.util.type.text.strs.remove_suffix_if_found().
    return text[:-len(suffix)] if suffix and text.endswith(suffix) else text

# ....................{ MAIN                              }....................
# If this module is imported from the command line, run this application's CLI;
# else, noop. For POSIX compliance, the exit status returned by this function
# is propagated to the caller as this script's exit status.
if __name__ == '__main__':
    sys.exit(main())
