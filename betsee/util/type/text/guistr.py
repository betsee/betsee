#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level Qt-specific string handling functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt, QByteArray
# from betse.util.io.log import logs
# from betse.util.type import strs
from betse.util.type.text import mls
from betse.util.type.types import type_check

# ....................{ TESTERS                            }....................
@type_check
def is_rich(text: str) -> bool:
    '''
    ``True`` only if the passed text superficially appears to be HTML and thus
    satisfy Qt's definition of "rich text" rather than plaintext.

    Specifically:

    * If the :func:`Qt.mightBeRichText` function is available, this tester
      defers to that function.
    * Else, this tester falls back to the :func:`mls.is_ml` function.
    '''

    # Qt.mightBeRichText() function if this function exists or "None" otherwise.
    # Unfortunately, the shiboken2 Qt 5 bindings parser internally
    # leveraged by PySide2 occasionally fails to create valid bindings for a
    # variety of "PySide2.QtCore.Qt" functions -- including this function.
    mightBeRichText = getattr(Qt, 'mightBeRichText', None)

    # If this function exists, defer to this function as is.
    #
    # Else, this function does *NOT* exist. In this case, we defer to a
    # homegrown (albeit less reliable) solution detecting the existence of at
    # least one *ML (e.g., HTML) tag in this string.
    return mightBeRichText(text) if mightBeRichText else mls.is_ml(text)

# ....................{ DECODERS                           }....................
def decode_qbytearray_ascii(qbytearray: QByteArray) -> str:
    '''
    Decode the passed ASCII-encoded Qt-specific byte array into a Python string.
    '''

    # Python-specific byte array extracted from this Qt-specific byte array. If
    # the latter defines the more efficient constData() method, prefer that;
    # else, fall back to the less efficient data() method. For unknown reasons
    # (presumably relating to deficiencies in shiboken2-parsed PySide2
    # bindings), the data() method is *ALWAYS* defined but the constData()
    # method is only occasionally defined.
    byte_array = (
        qbytearray.constData() if hasattr(qbytearray, 'constData') else
        qbytearray.data())

    # Decode this Python byte array into a Python string.
    return str(byte_array, encoding='ascii')
