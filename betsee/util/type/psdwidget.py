#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
High-level :mod:`PySide2`-specific widget facilities universally applicable to
all (or at least most) widget types.
'''

# ....................{ IMPORTS                            }....................
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
