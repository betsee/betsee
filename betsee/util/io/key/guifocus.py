#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application-wide **focus** (i.e., interactive keyboard input focus received by
the current application widget) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QApplication, QWidget
from betsee.guiexception import BetseePySideFocusException
from betsee.util.type.guitype import QWidgetOrNoneTypes

# ....................{ EXCEPTIONS                         }....................
def die_unless_widget_focused() -> None:
    '''
    Raise an exception if *no* application widget currently has the interactive
    keyboard input focus.

    Raises
    ----------
    BetseePySideFocusException
        If *no* widget is currently focused.

    See Also
    ----------
    :func:`is_widget_focused`
        Further details.
    '''

    if not is_widget_focused():
        raise BetseePySideFocusException(QCoreApplication.translate(
            'die_unless_widget_focused', 'No widget currently focused.'))

# ....................{ TESTERS                            }....................
def is_widget_focused() -> bool:
    '''
    ``True`` only if some application widget currently has the interactive
    keyboard input focus.
    '''

    # Don't ask. Don't tell.
    return QApplication.focusWidget() == 0

# ....................{ GETTERS                            }....................
def get_widget_focused() -> QWidget:
    '''
    Application widget that currently has the interactive keyboard input focus
    if any *or* raise an exception otherwise.

    Returns
    ----------
    QWidget
        Currently focused widget.

    Raises
    ----------
    BetseePySideFocusException
        If *no* widget is currently focused.
    '''

    # If no widget is currently focused, raise an exception.
    die_unless_widget_focused()

    # Else, some widget is currently focused. Return this widget.
    return QApplication.focusWidget()


def get_widget_focused_or_none() -> QWidgetOrNoneTypes:
    '''
    Application widget that currently has the interactive keyboard input focus
    if any *or* ``None`` otherwise.

    Returns
    ----------
    QWidgetOrNoneTypes
        Currently focused widget if any *or* ``None`` otherwise.
    '''

    # Currently focused widget if any or 0 otherwise.
    widget_focused = QApplication.focusWidget()

    # Return None if no widget is focused or this widget otherwise.
    return None if widget_focused == 0 else widget_focused
