#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Submodule providing general-purpose access to the :class:`QMainWindow`
singleton for this application.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import QMainWindow
from betsee.guiexceptions import BetseePySideWindowException
from betsee.util.app import guiapp
from betse.util.type.types import type_check

# ....................{ GETTERS                            }....................
def get_main_window() -> QMainWindow:
    '''
    Main window singleton widget for this application if already instantiated
    by the :class:`betsee.gui.guimain.BetseeGUI` class *or* raise an exception
    otherwise (i.e., if this widget is uninstantiated).

    Design
    ----------
    To avoid circular import dependencies, this getter intentionally resides in
    this submodule known *not* to be subject to these dependencies rather than
    in an arguably more germain submodule known to be subject to these
    dependencies (e.g., :mod:`betsee.gui.widget.guimainwindow`).

    Returns
    ----------
    QMainWindow
        This widget.

    Raises
    ----------
    BetseePySideWindowException
        If this widget has yet to be instantiated (i.e., if the
        :class:`QApplication` singleton fails to define the application-specific
        ``betsee_main_window`` attribute).
    '''

    # Application singleton, localized to avoid retaining references.
    gui_app = guiapp.get_app()

    # Main window singleton widget for this application if already instantiated
    # *OR* "None" otherwise.
    main_window = getattr(gui_app, 'betsee_main_window', None)

    # If this widget is uninstantiated. raise an exception.
    if main_window is None:
        raise BetseePySideWindowException(
            'Main window singleton widget uninstantiated (i.e., '
            '"PySide2.QtWidgets.qApp.betsee_main_window" attribute None).')

    # Else, this singleton has been instantiated. Return this singleton.
    return main_window

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

    # Application singleton, localized to avoid retaining references.
    gui_app = guiapp.get_app()

    # Main window singleton widget for this application if already instantiated
    # *OR* "None" otherwise.
    main_window = getattr(gui_app, 'betsee_main_window', None)

    # If this singleton is already instantiated. raise an exception.
    if main_window is not None:
        raise BetseePySideWindowException(
            'Main window singleton widget already instantiated (i.e., '
            '"PySide2.QtWidgets.qApp.betsee_main_window" attribute non-None).')

    # Else, this singleton is uninstantiated. Set this singleton.
    gui_app.betsee_main_window = main_window
