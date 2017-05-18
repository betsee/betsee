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
#   BETSE modules, which is *NOT* guaranteed to exist at this point. For
#   simplicity, PySide2 is assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtWidgets import QMessageBox
from betsee.exceptions import BetseeException

# ....................{ EXCEPTIONS                         }....................
def show_exception(exception: Exception) -> None:
    '''
    Display the passed exception in a :mod:`PySide2`-driven modal message box of
    the current application widget, creating this widget if necessary.

    Parameters
    ----------
    exception : Exception
        Exception to be displayed.
    '''

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
        #FIXME: Non-ideal. For legibility, spaces should be inserted between all
        #boundaries between non-capitalized characters and capitalized letters
        #(e.g., from "ValueError" to "Value Error").
        exception_title = type(exception).__name__
        exception_synopsis = str(exception)
        exception_exegesis = None

    # Attempt to obtain an exception traceback via BETSE, which is *NOT*
    # guaranteed to exist at this point.
    try:
        from betse.util.io import exceptions
        _, exception_traceback = exceptions.get_metadata(exception)
    # If BETSE is unimportable, ignore this exception traceback.
    except ImportError:
        pass

    # Message box displaying this exception metadata.
    message_box = QMessageBox()
    message_box.setWindowTitle(exception_title)
    message_box.setText(exception_synopsis)
    message_box.setIcon(QMessageBox.Critical)
    message_box.setStandardButtons(QMessageBox.Ok)

    # If this exception provides optional metadata, display this metadata.
    if exception_exegesis is not None:
        message_box.setInformativeText(exception_exegesis)
    if exception_traceback is not None:
        message_box.setDetailedText(exception_traceback)

    # Finalize this message box *AFTER* setting all widget proporties above.
    message_box.show()

    # Display this message box.
    message_box.exec_()
    # APPLICATION_WIDGET.exec_()
