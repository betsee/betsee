#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of most application-specific widget subclasses.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.util.widget"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtWidgets import QUndoStack
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideEditWidgetException

# ....................{ GLOBALS                            }....................
_OBJ_NAME_DEFAULT = 'N/A'
'''
Default Qt object name for all :class:`QBetseeObjectMixin` instances.
'''

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeObjectMixin(object):
    '''
    Abstract base class of most application-specific Qt object subclasses.

    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be inherited *first* rather than *last* in subclasses.

    Attributes (Public)
    ----------
    obj_name : str
        Qt-specific name of this object, identical to the string returned by the
        :meth:`objectName` method at widget initialization time. This string is
        stored as an instance variable only for readability.

    Attributes (Private)
    ----------
    _is_initted : bool
        ``True`` only if this object's :meth:`init` method has been called.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this application-specific Qt object.

        Parameters
        ----------
        All parameters are passed as is to the superclass this mixin is mixed
        into (e.g., :class:`QObject` or a subclass thereof).

        Caveats
        ----------
        **Subclasses overriding this method should not attempt to accept
        subclass-specific parameters.** Due to the semantics of Python's
        method-resolution order (MRO), accidentally violating this constraint is
        guaranteed to raise non-human-readable exceptions at subclass
        instantiation time.

        Abstract base subclasses may trivially circumvent this constraint by
        defining abstract properties which concrete subclasses then define. When
        doing so, note that abstract methods should raise the
        :class:`BetseMethodUnimplementedException` exception rather than be
        decorated by the usual :meth:`abstractmethod` decorator -- which is
        *not* safely applicable to subclasses of this class.

        For example:

            >>> from betse.exceptions import BetseMethodUnimplementedException
            >>> @property
            ... def muh_subclass_property(self) -> MuhValueType:
            ...     raise BetseMethodUnimplementedException()
        '''

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        #FIXME: Rename to "obj_name".

        # Nullify all remaining instance variables for safety.
        self._is_initted = False
        self.obj_name = _OBJ_NAME_DEFAULT


    def init(self) -> None:
        '''
        Finalize the initialization of this Qt object.

        This method is principally intended to simplify the implementation of
        subclasses overriding this method with subclass-specific finalization.

        Raises
        ----------
        BetseePySideEditWidgetException
            If this method has already been called for this object, preventing
            objects from being erroneously refinalized.
        '''

        # If this object has a meaningful name, log this initialization; else,
        # the subclass is expected to log this initialization.
        if self.obj_name != _OBJ_NAME_DEFAULT:
            logs.log_debug('Initializing object "%s"...', self.obj_name)

        # If this object's initialization has already been finalized, raise an
        # exception.
        if self._is_initted:
            raise BetseePySideEditWidgetException(
                'Object "{}" already initialized.'.format(self.obj_name))

        # Record this object's initialization to now have been finalized.
        self._is_initted = True


    def init_if_needed(self, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this object if needed (i.e., if this
        object's initialization has *not* already been finalized by a call to
        the :meth:`init` method).

        This method safely wraps the :meth:`init` method, effectively squelching
        the exception raised by that method when this object's initialization
        has already been finalized.

        Parameters
        ----------
        All parameters are passed as is to the :meth:`init` method if called.
        '''

        # If this object's initialization has *NOT* been finalized, do so.
        if self._is_initted:
            self.init(*args, **kwargs)

    # ..................{ PROPERTIES ~ read-only             }..................
    @property
    def is_initted(self) -> bool:
        '''
        ``True`` only if this object's :meth:`init` method has been called.
        '''

        return self._is_initted

    # ..................{ SETTERS                            }..................
    def setObjectName(self, obj_name: str) -> None:

        # Defer to the superclass setter.
        super().setObjectName(obj_name)

        # Store this name as an instance variable for negligible efficiency.
        self.obj_name = self.objectName()


class QBetseeEditWidgetMixin(QBetseeObjectMixin):
    '''
    Abstract base class of most application-specific **editable widget** (i.e.,
    widget interactively editing one or more values in an undoable manner)
    subclasses.

    Attributes
    ----------
    is_undo_cmd_pushable : bool
        ``True`` only if undo commands are safely pushable from this widget onto
        the undo stack *or* ``False`` when either:
        * This widget's content is currently being programmatically populated.
        * A previous undo command is already being applied to this widget.
        In both cases, changes to this widget's content are program- rather than
        user-driven and hence are *NOT* safely undoable. If ``False``, widget
        subclass slots intending to push an undo commands onto the undo stack
        should instead (in order):
        * Temporarily avoid doing so for the duration of the current slot call,
          as doing so *could* induce infinite recursion.
        * Set ``self.is_undo_cmd_pushable = False`` to permit all subsequent
          slot calls to push undo commands onto the undo stack.
    _undo_stack : QUndoStack
        Undo stack to which this widget pushes undo commands if any *or*
        ``None`` otherwise.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Unset the undo stack to which this widget pushes undo commands.
        self._unset_undo_stack()

    # ..................{ UNDO STACK ~ set                   }..................
    @type_check
    def _set_undo_stack(self, undo_stack: QUndoStack) -> None:
        '''
        Set the undo stack to which this widget pushes undo commands, permitting
        the :meth:`_push_undo_cmd_if_safe` method to pushing undo commands from
        this widget onto this stack.
        '''

        # Classify all passed parameters.
        self._undo_stack = undo_stack

        # Undo commands are now safely pushable from this widget.
        self.is_undo_cmd_pushable = True


    def _unset_undo_stack(self) -> None:
        '''
        Unset the undo stack to which this widget pushes undo commands,
        preventing the :meth:`_push_undo_cmd_if_safe` method from pushing undo
        commands from this widget.
        '''

        # Classify all passed parameters.
        self._undo_stack = None

        # Undo commands are now safely pushable from this widget.
        self.is_undo_cmd_pushable = False

    # ..................{ UNDO STACK ~ other                 }..................
    def _is_undo_stack_dirty(self) -> bool:
        '''
        ``True`` only if the undo stack associated with this widget is in the
        **dirty state** (i.e., contains at least one undo command to be undone).
        '''

        return not self._undo_stack.isClean()


    @type_check
    def _push_undo_cmd_if_safe(
        self,
        # To avoid circular imports, this type is validated dynamically.
        undo_cmd: (
            'betsee.util.widget.abc.guiundocmdabc.QBetseeWidgetUndoCommandABC'),
    ) -> None:
        '''
        Push the passed widget-specific undo command onto the undo stack
        associated with this widget.

        Parameters
        ----------
        undo_cmd : QBetseeWidgetUndoCommandABC
            Widget-specific undo command to be pushed onto this stack.
        '''

        # If undo commands are *NOT* safely pushable (e.g., due to a prior undo
        # command currently being applied to this widget), silently noop.
        # Pushing this undo command unsafely could provoke infinite recursion.
        if not self.is_undo_cmd_pushable:
            return

        # Else, no such command is being applied. Since pushing this undo
        # command onto the stack is thus safe, do so.
        self._sim_conf.undo_stack.push(undo_cmd)
