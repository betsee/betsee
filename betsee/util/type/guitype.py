#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Core :mod:`PySide2`\ -specific **type** (i.e., class) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import QWidget
from betse.util.type.types import NoneType

# ....................{ TUPLES : none                      }....................
# Tuples of types containing at least the type of the singleton "None" object.

QWidgetOrNoneTypes = (QWidget, NoneType)
'''
Tuple of both the stock widget type *and* the type of the singleton ``None``
object.
'''
