#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Application-specific editable widget** (i.e., widget whose content is
interactively editable by end users and whose implementation is specific to
this application) hierarchy.
'''

#FIXME: Decorate this QBetseeEditWidgetMixin.init() method in such a way as to
#prohibit subclasses from overriding that method. See also:
#
#https://stackoverflow.com/questions/321024/making-functions-non-override-able
#https://stackoverflow.com/questions/3948873/prevent-function-overriding-in-python
#
#The ideal solution should define both:
#
#* A @method_final method decorator, noting the passed method to be final
#  (i.e., *NOT* overridable by subclasses).
#* A "MethodFinalMetaclass" metaclass, iteratively scanning the passed class
#  for erroneous attempts to override methods marked by @method_final.

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.util.widget"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QUndoStack
# from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
from betse.util.type.types import type_check, GeneratorType
# from betsee.guiexception import BetseePySideWidgetException
from betsee.util.widget.mixin.guiwdgmixin import QBetseeObjectMixin
from contextlib import contextmanager

# ....................{ MIXINS                            }....................
#FIXME: It would appear that we need to explicitly prevent subclass
#implementations of the init() method from implicitly pushing undo commands
#onto the undo stack. This hasn't been an issue in the past, as we previously
#only called this method *BEFORE* opening the first simulation configuration.
#Now, however, we frequently repeatedly call this method for editable widgets
#on stack pages associated with dynamic list items. Doing so sanely will
#probably prove non-trivial, but is nonetheless mandatory to preserve sanity:
#
#* Implement the related "FIXME:" comment preceding the
#  QBetseeSimConfEditWidgetMixin.set_filename() slot.
#
#Wowzers! Critical work, but non-trivial. Nonetheless, this is our path ahead.
class QBetseeEditWidgetMixin(QBetseeObjectMixin):
    '''
    Abstract mixin of most application-specific **editable widget** (i.e.,
    widget interactively editing one or more values in an undoable manner)
    subclasses.

    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be inherited *first* rather than *last* in subclasses.

    Attributes
    ----------
    is_undo_cmd_pushable : bool
        ``True`` only if undo commands are safely pushable from this widget
        onto the undo stack *or* ``False`` when either:

        * This widget's content is currently being programmatically populated.
        * A previous undo command is already being applied to this widget.

        In both cases, changes to this widget's content are program- rather
        than user-driven and hence are *NOT* safely undoable. If ``False``,
        widget subclass slots intending to push an undo commands onto the undo
        stack should instead (in order):

        #. Temporarily avoid doing so for the duration of the current slot
           call, as doing so *could* induce infinite recursion.
        #. Set ``self.is_undo_cmd_pushable = True`` to permit all subsequent
           slot calls to push undo commands onto the undo stack.
    _undo_stack : QUndoStack
        Undo stack to which this widget pushes undo commands if any *or*
        ``None`` otherwise.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Unset the undo stack to which this widget pushes undo commands, thus
        # classifying the "self._undo_stack" instance variable.
        self._unset_undo_stack()

    # ..................{ SUBCLASS                          }..................
    # Subclasses are required to implement these abstract methods, which would
    # ideally be decorated by the standard @abstractmethod decorator. Since
    # doing so conflicts with metaclass semantics, these methods are instead
    # defined as concrete methods raising exceptions here.

    #FIXME: Ideally, this method would:
    #
    #* Be decorated as @abstractmethod. Since this is merely a mixin, that's
    #  infeasible.
    #* Raise the BetseMethodUnimplementedException() exception. Doing so,
    #  however, would prevent subclasses from calling this method.
    #* Be decorated by a newly defined @abstractmethod_mixin decorator declared
    #  somewhere in the "betse.util.type.decorator" submodule. Since no such
    #  decorator currently exists, this too is currently infeasible. Ideally,
    #  this decorator would (in order):
    #  * Dynamically detect whether or not any subclass of this superclass
    #    implements this abstract method. (StackOverflow is our friend here.)
    #  * If not, raise BetseMethodUnimplementedException().
    def _init_safe(self, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this editable widget in a safe manner
        guaranteed *not* to induce infinite recursion in common edge cases.

        Unlike the :meth:`init` method, this method is intended to be
        overridden by subclasses.

        See Also
        ----------
        :meth:`init`
            Further details.
        '''

        pass

    # ..................{ INITIALIZERS                      }..................
    def init(self, is_reinitable: bool = False, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this editable widget.

        Parameters
        ----------
        The ``is_reinitable`` parameter is passed as is to the
        :meth:`QBetseeObjectMixin.init` method. All remaining parameters are
        passed as is to the :meth:`_init_safe` method.

        Caveats
        ----------
        **Subclasses should override the abstract :meth:`_init_safe` method
        rather than this concrete method.** While :meth:`_init_safe` is
        explicitly designed for that sole purpose, this method is instead
        explicitly designed to *not* be overridden. Why? Because only the
        former method is protected against infinite recursion in edge cases
        (e.g., setting the initial value of this widget, which recursively
        pushes undo commands onto the undo stack associated with this widget).

        See Also
        ----------
        :meth:`QBetseeObjectMixin.init`
            Further details.
        '''

        # Finalize the initialization of our superclass.
        super().init(is_reinitable=is_reinitable)

        # While temporarily ignoring attempts by subclass implementations to
        # push undo commands onto the undo stack associated with this widget,
        # finalize the initialization of our subclass.
        with ignoring_undo_cmds(widget=self):
            self._init_safe(*args, **kwargs)

    # ..................{ PRIVATE ~ testers                 }..................
    def _is_undo_stack_dirty(self) -> bool:
        '''
        ``True`` only if this widget is associated with an undo stack (i.e., if
        the :meth:`_set_undo_stack` method has been called more recently than
        the :meth:`_unset_undo_stack` method) *and* that undo stack is in the
        **dirty state** (i.e., contains at least one undo command to be
        subsequently undone).
        '''

        return self._undo_stack is not None and not self._undo_stack.isClean()

    # ..................{ PRIVATE ~ setters                 }..................
    @type_check
    def _set_undo_stack(self, undo_stack: QUndoStack) -> None:
        '''
        Set the undo stack to which this widget pushes undo commands,
        permitting the :meth:`_push_undo_cmd_if_safe` method to pushing undo
        commands from this widget onto this stack.
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

    # ..................{ PRIVATE ~ pushers                 }..................
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

        # If undo commands are safely pushable from this widget (e.g., due to
        # no prior undo command being applied to this widget), do so.
        if self.is_undo_cmd_pushable:
            self._undo_stack.push(undo_cmd)
        # Else, undo commands are *NOT* safely pushable from this widget. In
        # this case, pushing this command onto this stack could provoke
        # infinite recursion. Avoid doing so with a non-fatal warning.
        else:
            logs.log_debug(
                'Ignoring undo command "%s" push request from widget "%s" '
                '(e.g., due to widget initialization or '
                'application of another undo command).',
                undo_cmd.actionText(), self.obj_name)

# ....................{ CONTEXTS                          }....................
@contextmanager
@type_check
def ignoring_undo_cmds(widget: QBetseeEditWidgetMixin) -> GeneratorType:
    '''
    Context manager temporarily disabling the
    :attr:`QBetseeEditWidgetMixin.is_undo_cmd_pushable` boolean of the passed
    editable widget for the duration of this context, guaranteeably restoring
    this boolean to its prior state immediately *before* returning.

    This context manager prevents this widget from recursively pushing
    additional undo commands onto the undo stack at inopportune moments (e.g.,
    during (re)initialization or when already applying an undo command).
    Permitting such recursion induces infinite recursion, which is bad.

    Parameters
    -----------
    widget : QBetseeEditWidgetMixin
        Editable widget to be prevented from inducing infinite recursion.

    Returns
    -----------
    contextlib._GeneratorContextManager
        Context manager instrumenting this widget as described above.

    Yields
    -----------
    None
        Since this context manager yields no values, the ``with`` statement
        encapsulating this manager must *not* be suffixed by an ``as`` clause.
    '''

    # Prior state of this boolean, preserved to permit restoration.
    is_undo_cmd_pushable_prior = widget.is_undo_cmd_pushable

    # Attempt to...
    try:
        # Temporarily prevent this widget from pushing undo commands.
        widget.is_undo_cmd_pushable = False

        # Yield control to the body of the caller's "with" block.
        yield
    # Restore this boolean's state even if that block raised an exception.
    finally:
        widget.is_undo_cmd_pushable = is_undo_cmd_pushable_prior
