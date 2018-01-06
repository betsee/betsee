#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all **clipboardable widget** (i.e., widget
transparently supporting copying, cutting, and pasting into and from the
platform-specific system clipboard) subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt, QEvent
from PySide2.QtGui import QKeyEvent
from PySide2.QtWidgets import QApplication
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.type.obj import objects
# from betse.util.type.types import type_check

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeClipboardWidgetMixin(object):
    '''
    Abstract base class of all **clipboardable widget** (i.e., widget
    transparently supporting copying, cutting, and pasting into and from the
    platform-specific system clipboard) subclasses.

    Most subclasses of this class support only plaintext and hence integrate
    only with the clipboard's plaintext buffer.

    Design
    ----------
    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be subclassed *first* rather than *last* in subclasses.
    '''

    # ..................{ SUBCLASS ~ mandatory : method      }..................
    # Subclasses are required to implement the following methods.

    def copy_selection_to_clipboard(self) -> None:
        '''
        Copy this widget's **current selection** (i.e., currently selected
        subset of this widget's value(s)) to the system clipboard, silently
        replacing the prior contents if any.
        '''

        raise BetseMethodUnimplementedException()


    def cut_selection_to_clipboard(self) -> None:
        '''
        **Cut** (i.e., copy and then remove as a single atomic operation) the
        this widget's **current selection** (i.e., currently selected subset of
        this widget's value(s)) to the system clipboard, silently replacing the
        prior contents if any.
        '''

        raise BetseMethodUnimplementedException()


    def paste_clipboard_to_selection(self) -> None:
        '''
        Paste the contents of the system clipboard over this widget's **current
        selection** (i.e., currently selected subset of this widget's value(s)),
        silently replacing the prior selection if any.
        '''

        raise BetseMethodUnimplementedException()


class QBetseeClipboardScalarWidgetMixin(QBetseeClipboardWidgetMixin):
    '''
    Abstract base class of all **scalar clipboardable widget** (i.e., scalar
    :mod:`PySide2` widget transparently supporting copying, cutting, and pasting
    into and from the platform-specific system clipboard) subclasses.

    In this context, the term "scalar" encompasses all widget subclasses whose
    contents reduce to a single displayed value (e.g., integer, floating point
    number, string).

    Design
    ----------
    All subclasses must support either (in order of descending preference):

    #. Explicit clipboard integration via the ``copy``, ``cut``, or ``paste``
       methods, typically supported by textual scalar widgets (e.g.,
       :class:`QLineEdit`).
    #. Implicit clipboard integration via the analogous Ctrl-c, Ctrl-x, and
       Ctrl-v keyboard shortcus, typically supported by numeric scalar widgets
       (e.g., :class:`QSpinBox`).

    If the current subclass does *not* define the ``copy``, ``cut``, and
    ``paste`` methods, this base class assumes this subclass to support the
    standard clipboard keyboard shortcuts instead. If this subclass supports
    neither, this base class silently reduces to a noop.
    '''

    # ..................{ SUPERCLASS ~ mandatory : method    }..................
    def copy_selection_to_clipboard(self) -> None:

        # If this subclass provides explicit clipboard support, prefer that.
        if objects.is_method(self, 'copy'):
            self.copy()
        # Else, assume (without evidence, of course) that this subclass supports
        # the standard keyboard shortcuts. In this case, queue up a key event
        # submitting the appropriate keyboard shortcut to this widget.
        else:
            QApplication.postEvent(self, QKeyEvent(
                QEvent.KeyPress, Qt.Key_C, Qt.ControlModifier))


    def cut_selection_to_clipboard(self) -> None:

        if objects.is_method(self, 'cut'):
            self.cut()
        else:
            QApplication.postEvent(self, QKeyEvent(
                QEvent.KeyPress, Qt.Key_X, Qt.ControlModifier))


    def paste_clipboard_to_selection(self) -> None:

        if objects.is_method(self, 'paste'):
            self.paste()
        else:
            QApplication.postEvent(self, QKeyEvent(
                QEvent.KeyPress, Qt.Key_V, Qt.ControlModifier))
