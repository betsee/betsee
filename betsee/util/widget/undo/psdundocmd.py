#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

#FIXME: Add support for Qt's command pattern-based "QUndoStack". Specifically:
#
#* Design a new ""QBetseeSimConfigUndoCommandABC" base class. This is getting
#  cumbersome fast, so we probably want to:
#  * Create a new "betsee.gui.widget.sim.config.undo" subpackage.
#  * Shift this "guisimconfundo" submodule into this subpackage.
#  * Create a new "guisimconfundocmd" submodule in this subpackage, to which
#    this base class and all subclasses described below should be added.
#* Design a variety of "QUndoCommand" subclasses in this submodule. Ideally,
#  there should exist one such subclass for each type of editable form widget in
#  our "sim_conf_stack" widget (e.g., "QBetseeSimConfigUndoCommandLineEdit" for
#  "QLineEdit" widgets), undoing and redoing changes to such widgets. It's quite
#  likely that such subclasses will need to be specific to simulation
#  configurations, as their implementations will probably need to store the
#  current and new values of a data descriptor-style attribute of the
#  "betse.science.params.Parameters" class for subsequent application
#  restoration by an undo. Presumably, the name of this attribute, the desired
#  new value of this attribute, and this "Parameters" object will need to be
#  passed to the constructor of each such subclass.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt  #, Slot
from PySide2.QtWidgets import (
    QLineEdit,
    QUndoCommand,
    QWidget,
)
# from betse.util.io.log import logs
from betse.util.type.types import type_check

# ....................{ SUPERCLASSES                       }....................
class QBetseeWidgetUndoCommandABC(QUndoCommand):
    '''
    Abstract base class of all widget-specific undo command subclasses,
    encapsulating both the application and restoration of the contents of a
    specific type of widget.

    Attributes
    ----------
    _widget : QWidget
        Widget operated upon by this undo command.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, widget: QWidget, synopsis: str) -> None:
        '''
        Initialize this undo command.

        Parameters
        ----------
        widget : QWidget
            Widget operated upon by this undo command.
        synopsis : str
            Human-readable string synopsizing the operation performed by this
            undo command, preferably as a single translated sentence.
        '''

        # Initialize our superclass with the passed synopsis.
        super().__init__(synopsis)

        # Classify all remaining parameters.
        self._widget = widget

    # ..................{ SUPERCLASS                         }..................
    # Optional superclass methods permitted to be redefined by each subclass.

    #FIXME: PySide2 should probably provide a default implementation for this
    #method identical to that defined below. Consider submitting this upstream.
    def id(self) -> int:
        '''
        Integer uniquely identifying the concrete subclass implementing this
        abstract base class.

        Our pure-C++ :class:`QUndoCommand` superclass requires this integer to
        transparently support **command compression** (i.e., automatic merging
        of adjacent undo commands of the same type)..
        '''

        return id(type(self))


class QBetseeScalarWidgetUndoCommandABC(QBetseeWidgetUndoCommandABC):
    '''
    Abstract base class of all scalar widget-specific undo command subclasses,
    encapsulating both the application and restoration of the scalar contents
    (e.g., float, integer, string) of a specific type of widget.

    This base class provides additional functionality specific to scalar
    widgets, including automatic merging of adjacent undo commands associated
    with the same widget.

    Attributes
    ----------
    _value_new : object
        New value replacing the prior value of the scalar widget associated with
        this undo command.
    _value_old : object
        Prior value of the scalar widget associated with this undo command.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(
        self,
        value_old: object,
        value_new: object,
        *args, **kwargs
    ) -> None:
        '''
        Initialize this undo command.

        Parameters
        ----------
        value_new : object
            New value replacing the prior value of the scalar widget associated with
            this undo command.
        value_old : object
            Prior value of the scalar widget associated with this undo command.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Initialize our superclass with all remaining arguments.
        super().__init__(*args, **kwargs)

        # Classify all passed parameters.
        self._value_new = value_new
        self._value_old = value_old

    # ..................{ SUPERCLASS                         }..................
    # Optional superclass methods permitted to be redefined by each subclass.

    def mergeWith(self, prior_undo_command: QUndoCommand) -> bool:
        '''
        Attempt to merge this undo command with the passed undo command
        immediately preceding this undo command on the parent undo stack,
        returning ``True`` only if this method performed this merge.

        Specifically, this method returns:

        * ``True`` if this method successfully merged both the undo and redo
          operations applied by the prior undo command into those applied by
          this undo command, in which case the prior undo command is safely
          removable from the parent undo stack.
        * ``False`` otherwise, in which case both the prior undo command and
          this undo command *must* be preserved as is the parent undo stack.

        Parameters
        ----------
        prior_undo_command : QUndoCommand
            Undo command immediately preceding this undo command on the parent
            undo stack.

        Returns
        ----------
        bool
            ``True`` only if these undo commands were successfully merged.
        '''

        # If this prior undo command is either of a different type *OR*
        # associated with a different widget than this undo command, these
        # commands cannot be safely merged and failure is reported.
        if not (
            self.id() == prior_undo_command.id() and
            self._widget == prior_undo_command._widget
        ):
            return False

        # Else, these commands are safely mergeable. Do so by replacing the
        # prior value of this scalar widget stored with this undo command by the
        # prior value of this scalar widget stored with this prior undo command.
        self._value_old = prior_undo_command._value_old

        # Report success.
        return True

# ....................{ SUBCLASSES                         }....................
class QBetseeLineEditUndoCommand(QBetseeScalarWidgetUndoCommandABC):
    '''
    :class:`QLineEdit`-specific undo command, encapsulating both the application
    of new text contents and restoration of old text contents of the
    :class:`QLineEdit` widget associated with this command.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, widget: QLineEdit, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(
            widget=widget,
            synopsis='edits to a text box',
            value_old=self._widget.text(),
            *args, **kwargs
        )

    # ..................{ SUPERCLASS                         }..................
    # Abstract superclass methods required to be defined by each subclass.

    #FIXME: This focus attempt almost certainly fails across pages. Nonetheless,
    #let's give her a go, eh?

    def undo(self) -> None:

        # To avoid revalidating the previously validated prior text contents of
        # this widget, the QLineEdit.setText() rather than QLineEdit.insert()
        # method is called.
        self._widget.setText(self._value_old)
        self._widget.setFocus(Qt.OtherFocusReason)


    def redo(self) -> None:

        self._widget.setText(self._value_new)
        self._widget.setFocus(Qt.OtherFocusReason)
