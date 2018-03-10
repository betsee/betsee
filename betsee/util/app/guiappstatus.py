#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application **status bar** (i.e., :class:`QStatusBar` widget synopsizing
application status in the :class:`QMainWindow` singleton for this application)
facilities.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QStatusBar
# from betse.util.io.log import logs
from betse.util.type.types import type_check
# from betsee.guiexception import BetseePySideWindowException

# ....................{ GETTERS                            }....................
def get_status_bar() -> QStatusBar:
    '''
    Singleton status bar widget for this application.

    Specifically, this function returns either:

    * If this main window defines an instance variable named ``status_bar``,
      the value of this variable.
    * Else, the value returned by the :meth:`QMainWindow.statusBar` method.
      Since this method is `considered problematic`_ by some in the Qt
      development community, this method is *only* called as a fallback.

    .. _considered problematic:
       https://plashless.wordpress.com/2013/09/14/qt-qmainwindow-statusbar-dont-use-it

    Design
    ----------
    To avoid circular import dependencies, this getter intentionally resides in
    this submodule known *not* to be subject to these dependencies rather than
    in an arguably more germain submodule known to be subject to these
    dependencies (e.g., :mod:`betsee.gui.window.guimainwindow`).

    Returns
    ----------
    QStatusBar
        This widget.

    Raises
    ----------
    BetseePySideWindowException
        If the main window widget for this application is uninstantiated.
    '''

    # Avoid circular import dependencies.
    from betsee.util.app import guiappwindow

    # Main window singleton.
    main_window = guiappwindow.get_main_window()

    # Application-specific status bar widget defined by this window if any *OR*
    # "None" otherwise.
    status_bar = getattr(main_window, 'status_bar', None)

    # If this window defines no such widget, fallback to the
    # application-agnostic status bar defined by *ALL* "QMainWindow" widgets
    if status_bar is None:
        status_bar = main_window.statusBar()

    # Return this status bar.
    return status_bar

# ....................{ STATUS                             }....................
@type_check
def show_status(text: str) -> None:
    '''
    Display the passed string as a **temporary message** (i.e., string
    temporarily replacing any normal message currently displayed) in the
    status bar.
    '''

    # Singleton status bar widget for this application.
    status_bar = get_status_bar()

    #FIXME: Validate this string to contain no newlines. Additionally, consider
    #emitting a warning if the length of this string exceeds a sensible maximum
    #(say, 160 characters or so).

    # Display this temporary message with no timeout.
    status_bar.showMessage(text)


def clear_status() -> None:
    '''
    Remove the temporary message currently displayed in the status bar if any
    *or* reduce to a noop otherwise.

    This function restores any "permanent" message displayed in the status bar
    (if any) prior to the recent temporary message displayed in the status bar
    (if any) by calls to the :func:`show_status` function. (It's complicated.)
    '''

    # Singleton status bar widget for this application.
    status_bar = get_status_bar()

    # Remove the temporary message currently displayed in the status bar if any.
    status_bar.clearMessage()
