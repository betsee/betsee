#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Application-specific widget** (i.e., widget implementations specific to this
application) hierarchy.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.util.widget"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtCore import QCoreApplication
from betse.util.io.log import logs
from betse.util.py import pyident
from betse.util.type.cls import classes
from betse.util.type.text.string import strs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideWidgetException

# ....................{ GLOBALS                           }....................
_OBJ_NAME_DEFAULT = 'N/A'
'''
Default Qt object name for all :class:`QBetseeObjectMixin` instances.
'''

# ....................{ MIXINS                            }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeObjectMixin(object):
    '''
    Abstract mixin of most application-specific Qt object subclasses.

    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be inherited *first* rather than *last* in subclasses.

    Attributes (Private)
    ----------
    _is_initted : bool
        ``True`` only if this object's :meth:`init` method has been called.
    '''

    # ..................{ INITIALIZERS                      }..................
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
        method-resolution order (MRO), accidentally violating this constraint
        is guaranteed to raise non-human-readable exceptions at subclass
        instantiation time.

        Abstract base subclasses may trivially circumvent this constraint by
        defining abstract properties which concrete subclasses then define.
        When doing so, note that abstract methods should raise the
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


    @type_check
    def init(self, is_reinitable: bool = False, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this Qt object.

        This method is principally intended to simplify the implementation of
        subclasses overriding this method with subclass-specific finalization.

        Parameters
        ----------
        is_reinitable : bool
            ``True`` only if this method may be safely called multiple times.
            Specifically, if this boolean is:

            * ``True``, this object is assumed to be **static** (i.e.,
              initialized only once at application startup), in which case the
              second call to this method raises an exception.
            * ``False``, this object is assumed to be **dynamic** (i.e.,
              repeatedly reinitialized during application runtime), in which
              case *no* repeated calls to this method raise an exception.

            Defaults to ``False``.

        All remaining parameters are passed as is to the :meth:`init`
        implementations of all other superclasses and mixins participating in
        the current method resolution order (MRO).

        Raises
        ----------
        BetseePySideWidgetException
            If this method has already been called for this object, preventing
            objects from being erroneously refinalized.
        '''

        # If this object has a meaningful name, log this initialization; else,
        # the subclass is expected to log this initialization.
        if self.obj_name != _OBJ_NAME_DEFAULT:
            logs.log_debug('Initializing object "%s"...', self.obj_name)

        # If this method may *NOT* be safely called multiple times but this is
        # the second call to this method, raise an exception.
        if not is_reinitable:
            self.die_if_initted()

        # Record this object's initialization to now have been finalized.
        self._is_initted = True


    def init_if_needed(self, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this object if needed (i.e., if this
        object's initialization has *not* already been finalized by a call to
        the :meth:`init` method).

        This method safely wraps the :meth:`init` method, effectively
        squelching the exception raised by that method when this object's
        initialization has already been finalized.

        Parameters
        ----------
        All parameters are passed as is to the :meth:`init` method if called.
        '''

        # If this object's initialization has *NOT* been finalized, do so.
        if self._is_initted:
            self.init(*args, **kwargs)

    # ..................{ PROPERTIES ~ str : obj name       }..................
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

    # ..................{ EXCEPTIONS                        }..................
    def die_if_initted(self) -> None:
        '''
        Raise an exception if this object's initialization has already been
        finalized (i.e., this object's :meth:`init` method has already been
        externally called).

        Raises
        ----------
        BetseePySideWidgetException
            If this object's initialization has already been finalized.
        '''

        # If this object's initialization has already been finalized, raise an
        # exception
        if self._is_initted:
            raise BetseePySideWidgetException(QCoreApplication.translate(
                'QBetseeObjectMixin',
                'Object "{0}" already initialized.'.format(self.obj_name)))


    def die_unless_initted(self) -> None:
        '''
        Raise an exception unless this object's initialization has already been
        finalized (i.e., this object's :meth:`init` method has already been
        externally called).

        Equivalently, this method raises an exception if this object's
        initialization has yet to be finalized.

        Raises
        ----------
        BetseePySideWidgetException
            If this object's initialization has yet to be finalized.
        '''

        # If this object's initialization has yet to be finalized, raise an
        # exception
        if not self._is_initted:
            raise BetseePySideWidgetException(QCoreApplication.translate(
                'QBetseeObjectMixin',
                'Object "{0}" uninitialized.'.format(self.obj_name)))

    # ..................{ SETTERS                           }..................
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
        This method is intentionally *not* called by the :meth:`__init__`
        method to set this object's name to a seemingly sane default. Why?
        Because numerous subclasses prefer to manually set this name.
        Unconditionally calling this method for every subclass would have the
        undesirable side effect of preventing this and other subclasses from
        detecting when the object name has yet to be set (e.g., via a
        comparison against the :data:`_OBJ_NAME_DEFAULT` default).
        '''

        # Subclass of this object.
        cls = type(self)

        # Unqualified CamelCase name of this subclass.
        cls_name = classes.get_name_unqualified(cls)

        # Remove the application-specific class name prefix if found and then
        # remove the application-agnostic class name prefix if found, as the
        # latter is a substring of the former.
        cls_name = strs.remove_prefix_if_found(text=cls_name, prefix='QBetsee')
        cls_name = strs.remove_prefix_if_found(text=cls_name, prefix='Q')

        # Set this object's name to this CamelCase converted into snake_case.
        self.obj_name = pyident.convert_camelcase_to_snakecase(cls_name)
