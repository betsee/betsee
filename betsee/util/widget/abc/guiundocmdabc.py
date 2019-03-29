#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all widget-specific undo command subclasses.
'''

#FIXME: Refactor either this or a related submodule to implicitly detect
#attempts to recursively call the
#betsee.gui.simconf.guisimconfundo.QBetseeSimConfUndoStack.push() method.
#Failing to do so currently results in naive widget implementations accidently
#inducing infinite recursion and hence raising runtime exceptions resembling:
#
#    [betsee] /home/leycec/py/betsee/betsee/gui/simconf/guisimconfundo.py:255: RuntimeWarning: libshiboken: Overflow: Value 94166704266232 exceeds limits of type  [signed] "i" (4bytes).
#      super().push(undo_command)
#
#    [betsee] Exiting prematurely due to fatal error:
#
#    OverflowError
#
#    Traceback (most recent call last):
#      File "/home/leycec/py/betsee/betsee/gui/simconf/stack/widget/abc/guisimconfwdgeditscalar.py", line 314, in _set_alias_to_widget_value_if_sim_conf_open
#        self._push_undo_cmd_if_safe(undo_cmd)
#      File "<string>", line 41, in func_type_checked
#      File "/home/leycec/py/betsee/betsee/util/widget/abc/guiwdgabc.py", line 380, in _push_undo_cmd_if_safe
#        self._sim_conf.undo_stack.push(undo_cmd)
#      File "/home/leycec/py/betsee/betsee/gui/simconf/guisimconfundo.py", line 255, in push
#        super().push(undo_command)
#
#To resolve this issue in the most elegant and hence simple manner, consider:
#
#* Define a new @die_if_called_recursively_with_params_same() decorator in the
#  "betse.util.type.decorator.decorators" submodule, raising an exception on
#  the first recursive call to the decorated callable which is passed the same
#  parameters (thus permitting only recursive calls to this callable passed
#  differing parameters). See the following brilliant StackOverflow definition
#  of such a decorator, which is surprisingly elegant:
#      https://stackoverflow.com/a/15955706/2809027
#* Decorate the QBetseeSimConfUndoStack.push() method by this decorator.

# ....................{ IMPORTS                           }....................
from PySide2.QtWidgets import QUndoCommand
from betse.util.io.log import logs
from betse.util.type.types import type_check, GeneratorType
from contextlib import contextmanager

# ....................{ SUPERCLASSES                      }....................
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

    # ..................{ INITIALIZERS                      }..................
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

    # ..................{ SUPERCLASS ~ mandatory            }..................
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

    # ..................{ SUPERCLASS ~ optional             }..................
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

    # ..................{ CONTEXTS                          }..................
    @contextmanager
    def _in_undo_cmd(self) -> GeneratorType:
        '''
        Context manager notifying the widget associated with this undo command
        that this undo command is now being applied to it for the duration of
        this context.

        This context manager temporarily disables and then guaranteeably
        restores the :attr:`QBetseeEditWidgetMixin.is_undo_cmd_pushable`
        boolean (even in the event of fatal exceptions), preventing
        :attr:`QBetseeEditWidgetMixin` methods from recursively pushing
        additional undo commands onto the undo stack when already applying an
        undo command. Why? Because doing so induces infinite recursion, which
        is bad.

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

# ....................{ PLACEHOLDERS                      }....................
class QBetseeUndoCommandNull(QUndoCommand):
    '''
    Placeholder undo command intended solely to simplify testing.
    '''

    # ..................{ SUPERCLASS ~ mandatory            }..................
    # Abstract superclass methods required to be defined by each subclass.

    def undo(self) -> None:

        # Log this undo.
        logs.log_debug('Undoing %s...', self.actionText())


    def redo(self) -> None:

        # Log this redo.
        logs.log_debug('Redoing %s...', self.actionText())
