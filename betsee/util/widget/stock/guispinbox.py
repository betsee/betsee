#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
General-purpose :mod:`QAbstractSpinBox` widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Signal, Slot
from PySide2.QtGui import QValidator
from PySide2.QtGui.QValidator import State
from PySide2.QtWidgets import QDoubleSpinBox
from betse.util.type.numeric import floats
from betse.util.type.text import regexes
from betse.util.type.types import type_check, RegexCompiledType

# ....................{ SUBCLASSES                         }....................
class QBetseeDoubleSpinBox(QDoubleSpinBox):
    '''
    :mod:`QDoubleSpinBox`-based widget optimized for intelligent display of
    floating point numbers.

    This application-specific widget augments the stock :class:`QDoubleSpinBox`
    widget with additional support for scientific notation, permitting *only*
    characters permissible in both:

    * Decimal notation (e.g., digits, signs, and the radix point).
    * Scientific notation (e.g., digits, signs, the radix point, and the letter
      "e" in both capitalized and uncapitalized variants).

    See Also
    ----------
    https://jdreaver.com/posts/2014-07-28-scientific-notation-spin-box-pyside.html
        Blog post strongly inspiring this implementation.
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

        pass

# ....................{ SUBCLASSES ~ validator             }....................
class QBetseeDoubleValidator(QValidator):
    '''
    :mod:`QDoubleSpinBox`-specific validator permitting entry and display of
    floating point numbers in both decimal and scientific notation by the
    :mod:`QBetseeDoubleSpinBox` class.

    This application-specific widget augments the stock
    :class:`QDoubleValidator` validator with additional support for scientific
    notation.

    Parameters
    ----------
    _float_regex : RegexCompiledType
        Compiled regular expression matching a floating point number.
    '''

    # ..................{ CONSTANTS                          }..................
    _CHARS_NONDIGIT = {'e', 'E', '.', '-', '+'}
    '''
    Set of all permissible non-digit characters in floating point numbers in
    either decimal or scientific notation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Compiled regular expression matching a floating point number in any
        # format, cached to ignorably improve efficiency in the frequently
        # called fixup() method.
        self._float_regex = floats.get_float_regex()

    # ..................{ VALIDATORS                         }..................
    @type_check
    def validate(self, text: str, char_index: int) -> State:
        '''
        Validate the passed input text at the passed character index of this
        text to be a valid floating point number or not.

        Parameters
        ----------
        text : str
            Input text to be validated.
        char_index : int
            0-based character index of the input cursor in this text.

        Returns
        ----------
        State
            Whether this text is a valid floating point number or not.
        '''

        # If this text is a valid floating point number, inform the caller.
        if floats.is_float_str(text):
            return State.Acceptable
        # Else, this text is *NOT* a valid floating point number.
        #
        # If this text is either the empty string *OR* the character
        # preceding the current character in this text is a permissible
        # non-digit in either decimal or scientific notation, this text could
        # conceivably be transformed into a valid floating point number by
        # subsequent entry of one or more printable characters.
        elif text == '' or text[char_index-1] in self._CHARS_NONDIGIT:
            return State.Intermediate
        # Else, this text is definitively an invalid floating point number.
        else:
            return State.Invalid


    @type_check
    def fixup(self, text: str) -> str:
        '''
        Intermediate or valid input munged from the passed invalid input.

        Specifically, this function returns:

        * The first substring in this invalid input matching a floating point
          number in either decimal or scientific notation if this input contains
          such a substring. In this case, the returned string is valid.
        * The empty string otherwise. In this case, the returned string is
          merely intermediate.

        In either case, the returned string is guaranteed *not* to be invalid.

        Parameters
        ----------
        text : str
            Invalid input text to be munged.

        Returns
        ----------
        str
            Intermediate or valid input munged from this invalid input.
        '''

        return regexes.get_match_full_first_if_any(
            text=text, regex=self._float_regex) or ''
