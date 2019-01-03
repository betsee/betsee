#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Core :mod:`PySide2`-specific **type** (i.e., class) functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import (
    QAbstractEventDispatcher,
    QThread,
    QThreadPool,
    Slot,
)
from PySide2.QtWidgets import (
    QLabel,
    QProgressBar,
    QWidget,
)
from betse.util.type.types import NoneType
from betsee.util.widget.stock.guiprogressbar import QBetseeProgressBar

# ....................{ TYPES                             }....................
QWidgetType = QWidget
'''
Root :mod:`PySide2`-based widget type.

This type is synonymous with the stock :class:`QWidget` class and is provided
merely as a caller convenience.
'''

# ....................{ TUPLES ~ none                     }....................
# Tuples of types containing at least the type of the singleton "None" object.

QAbstractEventDispatcherOrNoneTypes = (QAbstractEventDispatcher, NoneType)
'''
Tuple of both the :mod:`PySide2`-based event dispatcher type *and* the type of
the singleton ``None`` object.
'''


SlotOrNoneTypes = (Slot, NoneType)
'''
Tuple of both the :mod:`PySide2`-based slot type *and* the type of the
singleton ``None`` object.
'''

# ....................{ TUPLES ~ none : thread            }....................
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

# ....................{ TUPLES ~ none : widget            }....................
QLabelOrNoneTypes = (QLabel, NoneType)
'''
Tuple of both the :mod:`Label` widget type *and* the type of the singleton
``None`` object.
'''


QProgressBarOrNoneTypes = (QProgressBar, NoneType)
'''
Tuple of both the :mod:`QProgressBar` widget type *and* the type of the
singleton ``None`` object.
'''


QWidgetOrNoneTypes = (QWidgetType, NoneType)
'''
Tuple of both the root :mod:`PySide2`-based widget type *and* the type of the
singleton ``None`` object.
'''

# ....................{ TUPLES ~ none : widget : betsee   }....................
QBetseeProgressBarOrNoneTypes = (QBetseeProgressBar, NoneType)
'''
Tuple of both the :mod:`QBetseeProgressBar` widget type *and* the type of the
singleton ``None`` object.
'''
