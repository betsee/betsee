#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
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
#      File "/home/leycec/py/betsee/betsee/gui/simconf/stack/widget/abc/guisimconfwdgeditscalar.py", line 314, in _set_alias_to_widget_value_if_safe
#        self._push_undo_cmd_if_safe(undo_cmd)
#      File "<string>", line 41, in func_type_checked
#      File "/home/leycec/py/betsee/betsee.util.widget.mixin.guiwdgmixin.py", line 380, in _push_undo_cmd_if_safe
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
#  * Alternately, define a similar (albeit simpler) decorator raising an
#    exception on *ANY* recursive call -- which might be exactly what we
#    require here. Consider both cases. Again, see this StackOverflow answer:
#    https://stackoverflow.com/a/7900380/2809027
#    Note that this implementation is probably quite inefficient, suggesting
#    that the prior StackOverflow answer might yield a more responsible base
#    implementation that we would then simplify to produce the desired result.
#* Decorate the QBetseeSimConfUndoStack.push() method by this decorator -- or
#  perhaps the proposed QBetseeSimConfUndoStack.push_undo_cmd_if_safe() method,
#  which is probably a safer bet. Decorating Qt methods is probably a recipe
#  for untimely disaster.

# ....................{ IMPORTS                           }....................
from PySide2.QtWidgets import QUndoCommand
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.mixin.guiwdgeditmixin import QBetseeEditWidgetMixin

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
    def __init__(self, widget: QBetseeEditWidgetMixin, synopsis: str) -> None:
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

    # ..................{ SUPERCLASS ~ abstract             }..................
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
        of adjacent undo commands of the same type).
        '''

        return self._id

# ....................{ PLACEHOLDERS                      }....................
class QBetseeUndoCommandNull(QUndoCommand):
    '''
    Placeholder undo command intended solely to simplify testing.
    '''

    # ..................{ SUPERCLASS                        }..................
    # Abstract superclass methods required to be defined by each subclass.

    def undo(self) -> None:

        # Log this undo.
        logs.log_debug('Undoing %s...', self.actionText())


    def redo(self) -> None:

        # Log this redo.
        logs.log_debug('Redoing %s...', self.actionText())
