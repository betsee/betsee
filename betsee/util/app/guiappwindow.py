#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Submodule providing general-purpose access to the :class:`QMainWindow`
singleton for this application.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QMainWindow
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideWindowException

# ....................{ GLOBALS                            }....................
_MAIN_WINDOW = None
'''
Main window singleton widget for this application.
'''

# ....................{ GETTERS                            }....................
def get_main_window() -> QMainWindow:
    '''
    Singleton main window widget for this application if already instantiated
    by the :class:`betsee.gui.guimain.BetseeGUI` class *or* raise an exception
    otherwise (i.e., if this widget is uninstantiated).

    Design
    ----------
    To avoid circular import dependencies, this getter intentionally resides in
    this submodule known *not* to be subject to these dependencies rather than
    in an arguably more germane submodule known to be subject to these
    dependencies (e.g., :mod:`betsee.gui.window.guimainwindow`).

    Returns
    ----------
    QMainWindow
        This widget.

    Raises
    ----------
    BetseePySideWindowException
        If this widget has yet to be instantiated (i.e., if the
        :func:`set_main_window` function has yet to be called).
    '''

    # If this widget is uninstantiated. raise an exception.
    if _MAIN_WINDOW is None:
        raise BetseePySideWindowException(QCoreApplication.translate(
            'guiappwindow',
            'Main window singleton widget uninstantiated.'))

    # Else, this singleton has been instantiated. Return this singleton.
    return _MAIN_WINDOW

# ....................{ SETTERS                            }....................
@type_check
def set_main_window(main_window: QMainWindow) -> None:
    '''
    Set the main window singleton widget for this application.

    Parameters
    ----------
    main_window : QMainWindow
        Main window widget to set as this application's singleton.

    Raises
    ----------
    BetseePySideWindowException
        If this widget has already been instantiated (i.e., if the
        :class:`QApplication` singleton already defines the application-specific
        ``betsee_main_window`` attribute).
    '''

    # Globals modified below.
    global _MAIN_WINDOW

    # Log this attempt.
    logs.log_debug('Preserving main window...')

    # If this singleton is already instantiated. raise an exception.
    if _MAIN_WINDOW is not None:
        raise BetseePySideWindowException(QCoreApplication.translate(
            'guiappwindow',
            'Main window singleton widget already instantiated.'))

    # Set this global.
    _MAIN_WINDOW = main_window

# ....................{ UNSETTERS                          }....................
@type_check
def unset_main_window() -> None:
    '''
    Unset the main window singleton widget for this application.

    This function is intended to be called *only* on application destruction as
    a safety measure to avoid garbage collection issues.
    '''

    # Globals modified below.
    global _MAIN_WINDOW

    # Unset this global.
    _MAIN_WINDOW = None
