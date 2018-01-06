#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QAbstractSpinBox` widget subclasses.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import Signal, Slot
from PySide2.QtGui import QValidator
from PySide2.QtWidgets import QDoubleSpinBox
from betse.util.type.numeric import floats
from betse.util.type.text import regexes
from betse.util.type.types import type_check

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

    Attributes
    ----------
    _validator : QBetseeDoubleValidator
        Application-specific validator validating floating point numbers in both
        decimal and scientific notation.

    See Also
    ----------
    https://jdreaver.com/posts/2014-07-28-scientific-notation-spin-box-pyside.html
        Blog post partially inspiring this implementation.
    '''

    # ..................{ CONSTANTS                          }..................
    SINGLE_STEP_DEFAULT = 1.0
    '''
    Default Qt value for the :meth:`singleStep` property.

    Testing the current value of the :meth:`singleStep` property against this
    default permits subclasses to determine whether a widget-specific value for
    this property has been specified or not.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Connect the text appending signal to the corresponding slot.
        self._validator = QBetseeDoubleValidator()

        # Prevent Qt from constraining displayed floating point numbers to an
        # arbitrary maximum of 99.99, an insane default with no correspondence
        # to actual reality.
        #
        # By contrast, we silently permit Qt to retains its default behaviour of
        # constraining displayed floating point numbers to a minimum of 0, a
        # sane default given the inability of most measurable physical
        # quantities to "go negative."
        #
        # Note that overriding the default maximum here still permits callers to
        # override this with a widget- or subclass-specific maximum. Hence, this
        # override has *NO* unintended or harmful side effects.
        self.setMaximum(floats.FLOAT_MAX)

    # ..................{ VALIDATORS                         }..................
    # See the "QBetseeDoubleValidator" class for commentary.

    def validate(self, text: str, char_index: int) -> QValidator.State:
        return self._validator.validate(text, char_index)

    def fixup(self, text: str) -> str:
        return self._validator.fixup(text)

    # ..................{ VALIDATORS                         }..................
    def valueFromText(self, text: str) -> float:
        '''
        Floating point number converted from the passed human-readable string.
        '''

        return float(text)


    def textFromValue(self, number: float) -> str:
        '''
        Human-readable string converted from the passed floating point number.
        '''

        # For readability, a high-level utility function wrapping the low-level
        # "{:g}" format specifier is preferred.
        return floats.to_str(number)

# ....................{ SUBCLASSES ~ validator             }....................
class QBetseeDoubleValidator(QValidator):
    '''
    Validator enabling the :mod:`QBetseeDoubleSpinBox` widget to input and
    display floating point numbers in both decimal and scientific notation.

    This application-specific widget augments the stock
    :class:`QDoubleValidator` validator with additional support for scientific
    notation.

    Attributes
    ----------
    _float_regex : RegexCompiledType
        Compiled regular expression matching a floating point number.

    See Also
    ----------
    https://jdreaver.com/posts/2014-07-28-scientific-notation-spin-box-pyside.html
        Blog post partially inspiring this implementation.
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
    def validate(self, text: str, char_index: int) -> QValidator.State:
        '''
        Validate the passed input text at the passed character index of this
        text to be a valid floating point number or not.

        Specifically, this method returns:

        * :attr:`State.Acceptable` if this text is guaranteed to be an valid
          floating point number.
        * :attr:`State.Intermediate` if this text is currently an invalid
          floating point number but could conceivably be transformed into a
          valid floating point number by subsequent input of one or more
          printable characters.
        * :attr:`State.Invalid` if this text is guaranteed to be an invalid
          floating point number regardless of subsequently input printable
          characters.

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
            return QValidator.State.Acceptable
        # Else, this text is *NOT* a valid floating point number.
        #
        # If this text is either the empty string *OR* the character
        # preceding the current character in this text is a permissible
        # non-digit in either decimal or scientific notation, this text could
        # conceivably be transformed into a valid floating point number by
        # subsequent entry of one or more printable characters.
        elif text == '' or text[char_index-1] in self._CHARS_NONDIGIT:
            return QValidator.State.Intermediate
        # Else, this text is definitively an invalid floating point number.
        else:
            return QValidator.State.Invalid


    @type_check
    def fixup(self, text: str) -> str:
        '''
        Input guaranteed to be in either the :attr:`State.Intermediate` or
        :attr:`State.Valid` states, sanitized from the passed input guaranteed
        to be in the :attr:`State.Invalid` state.

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
