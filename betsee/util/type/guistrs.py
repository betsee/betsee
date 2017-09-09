#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level Qt-specific string handling functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt
# from betse.util.io.log import logs
# from betse.util.type import strs
from betse.util.type.text import mls
from betse.util.type.types import type_check

# ....................{ TESTERS                            }....................
@type_check
def is_rich(text: str) -> bool:
    '''
    Tooltip-specific event filter handling the passed Qt object and event.
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
