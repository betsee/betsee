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
)
# from betse.util.type.types import type_check

# ....................{ GLOBALS                            }....................
#FIXME: Map all possible editable widgets.
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
    QCheckBox: {'stateChanged',},
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

# ....................{ MIXINS                             }....................
#FIXME: Is the "is_in_undo_command" boolean still of value? If not, excise.

# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeWidgetMixin(object):
    '''
    Abstract base class of all **editable widget** (i.e., widget permitting one
    or more simulation configuration values stored in an external YAML file to
    be interactively edited) subclasses.

    Design
    ----------
    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be subclassed *first* rather than *last* in subclasses.

    Attributes
    ----------
    is_in_undo_command : bool
        ``True`` only if an undo command is now being externally applied to this
        widget, in which case widget subclass slots intending to push an undo
        commands onto the undo stack should instead (in order):
        * Temporarily avoid doing so for the duration of the current slot call,
          as doing so *could* induce infinite recursion.
        * Set ``self.is_in_undo_command = False`` to permit all subsequent slot
          calls to push undo commands onto the undo stack.
        To allow external callers (e.g., :class:`QBetseeUndoCommandABC`) to
        access this attribute, this attribute is public rather than private.
    object_name : str
        Qt-specific name of this widget, identical to the string returned by the
        :meth:`objectName` method at widget initialization time. This string is
        stored as an instance variable only for readability. To allow external
        callers (e.g., :class:`QBetseeUndoCommandABC`) to access this attribute,
        this attribute is public rather than private.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self.is_in_undo_command = False
        self.object_name = 'N/A'

    # ..................{ SETTERS                            }..................
    def setObjectName(self, object_name: str) -> None:

        # Defer to the superclass setter.
        super().setObjectName(object_name)

        # Store this name as an instance variable for negligible efficiency.
        self.object_name = self.objectName()
