#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application-wide **clipboard** (i.e., platform-specific system clipboard with
which arbitrary strings may be copied and cut to and pasted from) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtGui import QGuiApplication
# from PySide2.QtWidgets import QApplication, QWidget
from betsee.guiexceptions import BetseePySideClipboardException

# ....................{ EXCEPTIONS                         }....................
def die_unless_clipboard_text() -> None:
    '''
    Raise an exception unless the system clipboard's plaintext buffer is
    currently empty.

    Raises
    ----------
    BetseePySideClipboardException
        If this buffer is currently empty.

    See Also
    ----------
    :func:`is_clipboard_text`
        Further details.
    '''

    if not is_clipboard_text():
        raise BetseePySideClipboardException(
            QCoreApplication.translate(
                'die_if_clipboard_empty',
                'System clipboard text buffer empty.'))

# ....................{ TESTERS                            }....................
def is_clipboard_text() -> bool:
    '''
    ``True`` only if the system clipboard's plaintext buffer is currently empty
    (e.g., if no plaintext has been copied or cut into the clipboard for this
    windowing session).
    '''

    return not not QGuiApplication.clipboard().text()

# ....................{ GETTERS                            }....................
def get_clipboard_text() -> str:
    '''
    All text in the system clipboard's plaintext buffer if non-empty *or* raise
    an exception otherwise (e.g., if no plaintext has been copied or cut into
    the clipboard for this windowing session).

    Returns
    ----------
    str
        Most recently pasted plaintext in the system clipboard.

    Raises
    ----------
    BetseePySideClipboardException
        If this buffer is currently empty.
    '''

    # If this buffer is empty, raise an exception.
    die_unless_clipboard_text()

    # Else, this buffer is non-empty. Return its contents.
    return QGuiApplication.clipboard().text()
