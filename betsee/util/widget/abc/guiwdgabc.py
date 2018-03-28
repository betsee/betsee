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
from betse.util.py import pyident
from betse.util.type.cls import classes
from betse.util.type.text import strs
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

        # Nullify all remaining instance variables for safety.
        self._is_initted = False

        # If this object has no name, default this object's name.
        if not self.obj_name:
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

    # ..................{ PROPERTIES                         }..................
    @property
    def obj_name(self) -> str:
        '''
        Qt-specific name of this object.

        This property getter is a convenience alias of the non-Pythonic
        :meth:`objectName` method.
        '''

        return self.objectName()


    @obj_name.setter
    @type_check
    def obj_name(self, obj_name: str) -> None:
        '''
        Set the Qt-specific name of this object to the passed string.

        This property setter is a convenience alias of the non-Pythonic
        :meth:`setObjectName` method.
        '''

        self.setObjectName(obj_name)

    # ..................{ SETTERS                            }..................
    def set_obj_name_from_class_name(self) -> None:
        '''
        Set the Qt-specific name of this object to the unqualified name of this
        subclass, altered to comply with object name standards (e.g., from
        ``QBetseeSimmerWorkerSeed`` to ``simmer_worker_seed``).

        Specifically, this function (in order):

        #. Obtains the unqualified name of this subclass.
        #. Removes any of the following prefixes from this name:

           * ``QBetsee``, the string prefixing the names of all
             application-specific :class:`QObject` subclasses.
           * ``Q``, the string prefixing the names of all
             application-agnostic :class:`QObject` subclasses.

        #. Converts this name from CamelCase to snake_case.
        #. Sets this object's name to this name.

        Design
        ----------
        This method is intentionally *not* called by the :meth:`__init__` method
        to set this object's name to a (seemingly) sane default. Why? Because
        numerous subclasses prefer to manually set this name. Unconditionally
        calling this method for every subclass would have the undesirable side
        effect of preventing this and other subclasses from detecting when the
        object name has yet to be set (e.g., via a comparison against the
        :data:`_OBJ_NAME_DEFAULT` default).
        '''

        # Subclass of this object.
        cls = type(self)

        # Unqualified CamelCase name of this subclass.
        cls_name = classes.get_name(cls)

        # Remove the application-specific class name prefix if found and then
        # remove the application-agnostic class name prefix if found, as the
        # latter is a substring of the former.
        cls_name = strs.remove_prefix_if_found(text=cls_name, prefix='QBetsee')
        cls_name = strs.remove_prefix_if_found(text=cls_name, prefix='Q')

        # Set this object's name to this CamelCase converted into snake_case.
        self.obj_name = pyident.convert_camelcase_to_snakecase(cls_name)

# ....................{ MIXINS ~ edit                      }....................
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
