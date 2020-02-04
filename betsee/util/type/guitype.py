#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Core :mod:`PySide2`-specific **type** (i.e., class) functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import (
    QAbstractEventDispatcher,
    QThread,
    QThreadPool,
    QPoint,
    QSize,
    Slot,
)
from PySide2.QtWidgets import (
    QLabel,
    QProgressBar,
    QWidget,
    QTreeWidgetItem,
)
from betse.util.type.types import NoneType, NoneTypes
from betsee.util.widget.stock.guiprogressbar import QBetseeProgressBar

# ....................{ TYPES                             }....................
QWidgetType = QWidget
'''
Root :mod:`PySide2`-based widget type.

This type is synonymous with the stock :class:`QWidget` class and is provided
merely as a caller convenience.
'''

# ....................{ TUPLES                            }....................
#FIXME: Complete this tuple as needed. For brevity, this tuple currently
#contains *ONLY* those QVariant-coercible types required by this application.

# The contents of this tuple derive from the official documentation for the
# "QtCore::QVariant" class -- notably, the methods of that class whose names
# are prefixed by "to" (e.g., toBool(), toFloat(), toInt()).
#
# Strap in, folks. This is gonna be a verbose one.
QVariantTypes = (
    # Primitive Qt-agnostic types.
    bool, int, float, str,

    # Structured Qt-specific types.
    QPoint, QSize,
)
'''
Tuple of all types whose instances are guaranteed to be losslessly coercible to
and from a :class:`PySide2.QtCore.QVariant` instance, a low-level union
analogue for primitive types and structures in Qt.

Equivalently, this tuple describes the set of all types whose instances may be
safely written to and read from a :class:`PySide2.QtCore.QSettings`-based
backing store of application-wide settings.
'''

# ....................{ TUPLES ~ none                     }....................
# Tuples of types containing at least the type of the singleton "None" object.

QAbstractEventDispatcherOrNoneTypes = (QAbstractEventDispatcher, NoneType)
'''
Tuple of both the :mod:`PySide2`-based event dispatcher type *and* the type of
the singleton ``None`` object.
'''


QTreeWidgetItemOrNoneTypes = (QTreeWidgetItem, NoneType)
'''
Tuple of both the :mod:`PySide2`-based tree widget item type *and* the type of
the singleton ``None`` object.
'''


QVariantOrNoneTypes = QVariantTypes + NoneTypes
'''
Tuple of all types whose instances are guaranteed to be losslessly coercible to
and from a :class:`PySide2.QtCore.QVariant` instance *and* the type of
the singleton ``None`` object.

See Also
----------
:data:`QVariantTypes`
    Further details.
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
