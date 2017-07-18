#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all widget-specific undo command subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import (
    QLineEdit, QUndoCommand)
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.psdwdg import QBetseeWidgetMixin

# ....................{ SUPERCLASSES                       }....................
class QBetseeUndoCommandWidgetABC(QUndoCommand):
    '''
    Abstract base class of all widget-specific undo command subclasses,
    encapsulating both the application and restoration of the contents of a
    specific type of widget.

    Attributes
    ----------
    _id : int
        Integer uniquely identifying the concrete subclass implementing this
        abstract base class of this undo command.
    _widget : QBetseeWidgetMixin
        Application-specific widget operated upon by this undo command.
    _synopsis : str
        Human-readable string synopsizing the operation performed by this
        undo command, preferably as a single translated sentence fragment.
        This string is identical to that returned by the :meth:`actionString`
        method, but is stored as an instance variable purely for readability.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, widget: QBetseeWidgetMixin, synopsis: str) -> None:
        '''
        Initialize this undo command.

        Parameters
        ----------
        widget : QBetseeWidgetMixin
            Application-specific widget operated upon by this undo command.
        synopsis : str
            Human-readable string synopsizing the operation performed by this
            undo command, preferably as a single translated sentence fragment.
        '''

        # Initialize our superclass with the passed synopsis.
        super().__init__(synopsis)

        # Classify all parameters.
        self._synopsis = synopsis
        self._widget = widget

        # Integer uniquely identifying this concrete subclass.
        self._id = id(type(self))

    # ..................{ SUPERCLASS ~ mandatory             }..................
    # Abstract superclass methods required to be defined by each subclass.

    def undo(self) -> None:

        # Log this undo.
        logs.log_debug(
            'Undoing %s for widget "%s"...',
            self._synopsis, self._widget.object_name)

        # Notify this widget that an undo command is now being applied to it.
        self._widget.is_in_undo_command = True


    def redo(self) -> None:

        # Log this redo.
        logs.log_debug(
            'Redoing %s for widget "%s"...',
            self._synopsis, self._widget.object_name)

        # Notify this widget that an undo command is now being applied to it.
        self._widget.is_in_undo_command = True

    # ..................{ SUPERCLASS ~ optional              }..................
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

        return self._id


class QBetseeUndoCommandScalarWidgetABC(QBetseeUndoCommandWidgetABC):
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
            New value replacing the prior value of the scalar widget associated
            with this undo command.
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
class QBetseeUndoCommandLineEdit(QBetseeUndoCommandScalarWidgetABC):
    '''
    :class:`QLineEdit`-specific undo command, encapsulating both the application
    of new text contents and restoration of old text contents of the
    :class:`QLineEdit` widget associated with this command.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, widget: QLineEdit, value_old: str) -> None:
        '''
        Initialize this undo command.

        Parameters
        ----------
        widget: QLineEdit
            Scalar widget associated with this undo command.
        value_old : str
            Prior value of this scalar widget.
        '''

        # Initialize our superclass with all passed arguments.
        super().__init__(
            widget=widget,
            value_old=value_old,
            value_new=widget.text(),
            synopsis='edits to a text box',
        )

    # ..................{ SUPERCLASS                         }..................
    # Abstract superclass methods required to be defined by each subclass.

    #FIXME: This focus attempt almost certainly fails across pages. If this is
    #the case, a sane general-purpose solution would be to iteratively search
    #up from the parent of this widget to the eventual page of the
    #"QStackedWidget" object containing this widget and then switch to that.

    def undo(self) -> None:

        # Defer to our superclass first.
        super().undo()

        # Undo the prior edit.
        #
        # To avoid revalidating the previously validated prior text contents of
        # this widget, the QLineEdit.setText() rather than QLineEdit.insert()
        # method is called.
        self._widget.setText(self._value_old)
        # self._widget.setFocus(Qt.OtherFocusReason)


    def redo(self) -> None:

        # Defer to our superclass first.
        super().redo()

        # Redo the prior edit.
        self._widget.setText(self._value_new)
        # self._widget.setFocus(Qt.OtherFocusReason)

# ....................{ PLACEHOLDERS                       }....................
class QBetseeUndoCommandNull(QUndoCommand):
    '''
    Placeholder undo command intended solely to simplify testing.
    '''

    # ..................{ SUPERCLASS ~ mandatory             }..................
    # Abstract superclass methods required to be defined by each subclass.

    def undo(self) -> None:

        # Log this undo.
        logs.log_debug('Undoing %s...', self.actionText())


    def redo(self) -> None:

        # Log this redo.
        logs.log_debug('Redoing %s...', self.actionText())
