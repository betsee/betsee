#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QTextEdit` widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QPlainTextEdit

# ....................{ SUBCLASSES                         }....................
class QBetseePlainTextEdit(QPlainTextEdit):
    '''
    :mod:`QPlainTextEdit`-based widget optimized for intelligent display of
    plaintext (rather than rich text or hypertext).

    This application-specific widget augments the stock :class:`QPlainTextEdit`
    widget with additional support for intelligent text appending, including:

    * **Auto-scrolling,** automatically scrolling this widget to the most
      recently appended text.
    * **Thread-safe appending,** permitting different threads other than the
      thread owning this widget to safely append text to this widget via a
      preconfigured text appending signal and slot.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Connect the text appending signal to the corresponding slot.
        self.append_text_signal.connect(self.append_text)

    # ..................{ SIGNALS                            }..................
    append_text_signal = Signal(str)
    '''
    Signal accepting a single string, connected to a slot of the same widget at
    widget initialization time to intelligently append this string to this
    widget.

    This signal is connected to the :meth:`append_text` slot at widget
    initialization time, enabling callers in different threads to thread-safely
    append text to this widget.
    '''

    # ..................{ SLOTS                              }..................
    @Slot(str)
    def append_text(self, text: str) -> None:
        '''
        Append the passed plain text to the text currently displayed by this
        widget and scroll this widget to display that text.

        This slot is connected to the :attr:`append_text_signal` signal at
        widget initialization time, permitting callers in different threads to
        thread-safely append text to this widget.

        Parameters
        ----------
        text : str
            Text to be appended.
        '''

        # Append this text to this widget.
        self.appendPlainText(text)

        # Scroll this widget to display this text.
        self.ensureCursorVisible()
