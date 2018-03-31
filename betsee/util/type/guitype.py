#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Core :mod:`PySide2`-specific **type** (i.e., class) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QAbstractEventDispatcher, QThread, QThreadPool
from PySide2.QtWidgets import QWidget
from betse.util.type.types import NoneType

# ....................{ TYPES                              }....................
QWidgetType = QWidget
'''
Root :mod:`PySide2`-based widget type.

This type is synonymous with the stock :class:`QWidget` class and is provided
merely as a caller convenience.
'''

# ....................{ TUPLES : none                      }....................
# Tuples of types containing at least the type of the singleton "None" object.

QAbstractEventDispatcherOrNoneTypes = (QAbstractEventDispatcher, NoneType)
'''
Tuple of both the :mod:`PySide2`-based event dispatcher type *and* the type of
the singleton ``None`` object.
'''


QThreadOrNoneTypes = (QThread, NoneType)
'''
Tuple of both the :mod:`PySide2`-based thread type *and* the type of the
singleton ``None`` object.
'''


QThreadPoolOrNoneTypes = (QThreadPool, NoneType)
'''
Tuple of both the :mod:`PySide2`-based thread pool type *and* the type of the
singleton ``None`` object.
'''


QWidgetOrNoneTypes = (QWidgetType, NoneType)
'''
Tuple of both the root :mod:`PySide2`-based widget type *and* the type of the
singleton ``None`` object.
'''
