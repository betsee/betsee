#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
High-level :mod:`PySide2`-specific widget facilities universally applicable to
all (or at least most) widget types.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.util.widget"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QKeySequenceEdit,
    QLineEdit,
    QListWidget,
    QSlider,
    QSpinBox,
    QPlainTextEdit,
    QTextEdit,
    QTimeEdit,
    QUndoStack,
)
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.type.guitypes import QWidgetOrNoneTypes

# ....................{ GLOBALS                            }....................
#FIXME: Map all possible editable widgets.
#FIXME: Actually, just excise this. We no longer require such generality.

FORM_WIDGET_TYPE_TO_SIGNALS_CHANGE = {
    # All other modification signals exposed by "QComboBox" (e.g.,
    # QComboBox.currentIndexChanged) are subsumed by the following
    # general-purpose parent signal.
    QComboBox: {'currentTextChanged',},

    # Button widgets.
    #
    # Note that the "QRadioButton" widget is intentionally omitted. Such
    # low-level widgets should *ONLY* ever be contained in a higher-level
    # "QButtonGroup" parent widget. The low-level QRadioButton.toggled() signal
    # is emitted for the pair of radio buttons in a group being enabled and
    # disabled, thus generating two emissions for each toggling of a radio
    # button. By compare, the higher-level QButtonGroup.buttonClicked() signal
    # is emitted exactly once for each such toggling. Despite nomenclature
    # suggesting this signal to apply *ONLY* to interactive clicks, this signal
    # is emitted on interactive and programmatic clicks and keyboard shortcuts.
    QCheckBox: {'toggled',}, # QCheckBox: {'stateChanged',},
    QButtonGroup: {'buttonClicked',},

    # Date and time widgets.
    QDateEdit:     {'dateTimeChanged',},
    QDateTimeEdit: {'dateTimeChanged',},
    QTimeEdit:     {'dateTimeChanged',},

    # Item widgets.
    QListWidget: {'currentItemChanged',},

    # Slider widgets.
    QDial:   {'valueChanged',},
    QSlider: {'valueChanged',},

    # Spin widgets.
    QDoubleSpinBox: {'valueChanged',},
    QSpinBox:       {'valueChanged',},

    # Textual widgets.
    QLineEdit:      {'textChanged',},
    QPlainTextEdit: {'textChanged',},
    QTextEdit:      {'textChanged',},

    # All other editable widgets.
    QKeySequenceEdit: {'keySequenceChanged',},
}
'''
Dictionary mapping from each editable widget subclass commonly added to form
containers to the set of names of all signals emitted by each widget of this
subclass when its contents (typically editable text or selectable item) changes.

Signals emitted by widgets when their superficial appearance unrelated to their
contents are intentionally omitted.

Design
----------
For lookup efficiency, each widget subclass mapped by this dictionary is
guaranteed to be concrete rather than abstract (e.g., :class:`QSlider` rather
than :class:`QAbstractSlider`).

Technically, each widget subclass currently emits exactly high-level signal on
content changes. For generality, this dictionary nonetheless maps each widget
subclass to a set of only the name of that signal rather than to that name
directly.
'''

# ....................{ GETTERS                            }....................
@type_check
def get_label(widget: QWidgetOrNoneTypes) -> str:
    '''
    Human-readable label synopsizing the passed widget if any.

    Parameters
    ----------
    widget : QWidgetOrNoneTypes
        Either:
        * :class`QWidget` instance to be synopsized.
        * ``None``, in which case the absence of such a widget is synopsized.

    Returns
    ----------
    str
        Human-readable label synopsizing this widget if any.
    '''

    return (
        'widget "{}"'.format(widget.objectName()) if widget is not None else
        'no widget')

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeWidgetMixin(object):
    '''
    Abstract base class of most application-specific widget subclasses.

    Design
    ----------
    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be subclassed *first* rather than *last* in subclasses.

    Attributes (Public)
    ----------
    object_name : str
        Qt-specific name of this widget, identical to the string returned by the
        :meth:`objectName` method at widget initialization time. This string is
        stored as an instance variable only for readability.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this application-specific widget.

        Parameters
        ----------
        All parameters are passed as is to the superclass this mixin is mixed
        into (e.g., :class:`QWidget` or a subclass thereof).

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
        self.object_name = 'N/A'

    # ..................{ SETTERS                            }..................
    def setObjectName(self, object_name: str) -> None:

        # Defer to the superclass setter.
        super().setObjectName(object_name)

        # Store this name as an instance variable for negligible efficiency.
        self.object_name = self.objectName()


class QBetseeEditWidgetMixin(QBetseeWidgetMixin):
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
        undo_cmd: 'betsee.util.widget.guiundocmd.QBetseeWidgetUndoCommandABC',
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
