#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level :mod:`PySide2`-driven error handling facilities.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT* include
#   BETSE modules, which are *NOT* guaranteed to exist at this point. For
#   simplicity, PySide2 is assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import re
from PySide2.QtWidgets import QMessageBox
from betsee.exceptions import BetseeException

# ....................{ ERRORS                             }....................
def show_error(
    # Mandatory parameters.
    title: str,
    synopsis: str,

    # Optional parameters.
    exegesis: str = None,
    details: str = None,
) -> None:
    '''
    Display the passed error as a :mod:`PySide2`-driven modal message box in
    the current application widget, creating this widget if necessary.

    Parameters
    ----------
    title : str
        Title of this error to be displayed as the title of this message box.
    synopsis : str
        Synopsis of this error to be displayed as the text of this message box.
    exegesis : optional[str]
        Exegesis (i.e., explanation) of this error to be displayed as the
        so-called "informative text" of this message box below the synopsis of
        this error. Defaults to ``None``, in which case no such text is
        displayed.
    details : optional[str]
        Technical details of this error to be displayed as the so-called
        "detailed text" of this message box in monospaced font below both the
        synopsis and exegesis of this error in a discrete fold-down text area.
        Defaults to ``None``, in which case no such text is displayed.
    '''

    # Type check manually.
    assert isinstance(title,    str), '"{}" not a string.'.format(title)
    assert isinstance(synopsis, str), '"{}" not a string.'.format(synopsis)

    # Message box displaying this error.
    error_box = QMessageBox()
    error_box.setWindowTitle(title)
    error_box.setText(synopsis)
    error_box.setIcon(QMessageBox.Critical)
    error_box.setStandardButtons(QMessageBox.Ok)

    # If this exception provides optional metadata, display this metadata.
    if exegesis is not None:
        assert isinstance(exegesis, str), '"{}" not a string.'.format(exegesis)
        error_box.setInformativeText(exegesis)
    if details is not None:
        assert isinstance(details, str), '"{}" not a string.'.format(details)
        error_box.setDetailedText(details)

    # Finalize this message box *AFTER* setting all widget proporties above.
    error_box.show()

    # Run this application's event loop, thus displaying this message box.
    error_box.exec_()

# ....................{ EXCEPTIONS                         }....................
def show_exception(exception: Exception) -> None:
    '''
    Display the passed exception as a :mod:`PySide2`-driven modal message box in
    the current application widget, creating this widget if necessary.

    Parameters
    ----------
    exception : Exception
        Exception to be displayed.
    '''

    # Type check manually.
    assert isinstance(exception, Exception), (
        '"{}" not an exception.'.format(exception))

    # Implicitly create the root Qt widget containing the message box to be
    # subsequently displayed, if needed.
    from betsee.lib.pyside import psdapp
    if False: psdapp  # squelch IDE warnings

    # If this is an application exception annotated with human-readable metadata
    # intended to be displayed, do so.
    if isinstance(exception, BetseeException):
        exception_title = exception.title
        exception_synopsis = exception.synopsis
        exception_exegesis = exception.exegesis
    # Else, synthesize this metadata from the contents of this exception.
    else:
        # Class name of this exception.
        exception_classname = type(exception).__name__

        # Human-readable type of this exception, synthesized from this
        # machine-readable class name by inserting spaces between all
        # boundaries between non-capitalized and capitalized letters (e.g., from
        # "ValueError" to "Value Error").
        exception_title = re.sub(
            r'([a-z])([A-Z])', r'\1 \2', exception_classname,)
        exception_synopsis = str(exception)
        exception_exegesis = None

    # Attempt to obtain an exception traceback via BETSE, which is *NOT*
    # guaranteed to exist at this point.
    try:
        from betse.util.io import exceptions
        _, exception_traceback = exceptions.get_metadata(exception)
    # If BETSE is unimportable, ignore this exception traceback.
    except ImportError:
        exception_traceback = None

    # Display this exception as a message box.
    show_error(
        title=exception_title,
        synopsis=exception_synopsis,
        exegesis=exception_exegesis,
        details=exception_traceback,
    )
