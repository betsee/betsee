#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all widget-specific undo command subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import QUndoCommand
from betse.util.io.log import logs
from betse.util.type.types import type_check, GeneratorType
from contextlib import contextmanager

# ....................{ SUPERCLASSES                       }....................
class QBetseeWidgetUndoCommandABC(QUndoCommand):
    '''
    Abstract base class of all widget-specific undo command subclasses,
    encapsulating both the application and restoration of the contents of a
    specific type of widget.

    Attributes
    ----------
    _id : int
        Integer uniquely identifying the concrete subclass implementing this
        abstract base class of this undo command.
    _widget : QBetseeEditWidgetMixin
        Application-specific widget operated upon by this undo command.
    _synopsis : str
        Human-readable string synopsizing the operation performed by this
        undo command, preferably as a single translated sentence fragment.
        This string is identical to that returned by the :meth:`actionString`
        method, but is stored as an instance variable purely for readability.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(
        self,
        # Avoid circular import dependencies.
        widget: 'betsee.util.widget.abc.guiwdgabc.QBetseeEditWidgetMixin',
        synopsis: str,
    ) -> None:
        '''
        Initialize this undo command.

        Parameters
        ----------
        widget : QBetseeEditWidgetMixin
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
            self._synopsis, self._widget.obj_name)


    def redo(self) -> None:

        # Log this redo.
        logs.log_debug(
            'Redoing %s for widget "%s"...',
            self._synopsis, self._widget.obj_name)

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

    # ..................{ CONTEXTS                           }..................
    @contextmanager
    def _in_undo_cmd(self) -> GeneratorType:
        '''
        Context manager notifying the widget associated with this undo command
        that this undo command is now being applied to it for the duration of
        this context.

        This context manager enables and then guaranteeably disables the
        :attr:`QBetseeEditWidgetMixin.is_undo_cmd_pushable` boolean even when
        fatal exceptions are raised, preventing :attr:`QBetseeEditWidgetMixin`
        subclass slots from recursively pushing additional undo commands onto
        the undo stack when already applying an undo command. Why? Because doing
        so induces infinite recursion, which is bad.

        Returns
        -----------
        contextlib._GeneratorContextManager
            Context manager notifying this widget as described above.

        Yields
        -----------
        None
            Since this context manager yields no values, the caller's ``with``
            statement must be suffixed by *no* ``as`` clause.
        '''

        # Prior state of this boolean, preserved to permit restoration.
        is_undo_cmd_pushable_prior = self._widget.is_undo_cmd_pushable

        # Yield control to the body of the caller's "with" block.
        try:
            self._widget.is_undo_cmd_pushable = False
            yield
        # Restore this boolean's state even if that block raised an exception.
        finally:
            self._widget.is_undo_cmd_pushable = is_undo_cmd_pushable_prior

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
