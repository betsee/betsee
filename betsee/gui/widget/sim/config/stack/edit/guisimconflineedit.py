#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QLineEdit`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal
from PySide2.QtWidgets import QLineEdit
#from betse.util.io.log import logs
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfLineEdit(QBetseeSimConfEditScalarWidgetMixin, QLineEdit):
    '''
    Simulation configuration-specific line edit widget, permitting single-line
    strings backed by external simulation configuration files to be
    interactively edited.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

    # ..................{ SUPERCLASS ~ setter                }..................
    def setText(self, text_new: str) -> None:

        # Defer to the superclass setter.
        super().setText(text_new)

        # If this configuration is currently open, set the current value of this
        # simulation configuration alias to this widget's current value.
        self._set_alias_to_widget_value_if_sim_conf_open()

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfLineEdit', 'edits to a text box')


    @property
    def _finalize_widget_edit_signal(self) -> Signal:
        return self.editingFinished

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> object:
        return self.text()


    @widget_value.setter
    def widget_value(self, widget_value: object) -> None:

        # If this value is *NOT* a string, coerce this value into a string.
        # Since effectively all scalar values are safely coercable into strings
        # (due to their implementation of the special __str__() method), this is
        # guaranteed to be safe and hence need *NOT* be checked.
        if not isinstance(widget_value, str):
            widget_value = str(widget_value)

        # Set this widget's displayed value to the passed value by calling the
        # setText() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        super().setText(widget_value)


    def _clear_widget_value(self) -> None:
        self.widget_value = ''

    # ..................{ MIXIN ~ clipboard                  }..................
    # No, thank *YOU*, QLineEdit superclass.

    @property
    def is_clipboardable(self) -> bool:
        return True

    def copy_selection_to_clipboard(self) -> None:
        self.copy()

    def cut_selection_to_clipboard(self) -> None:
        self.cut()

    def paste_clipboard_to_selection(self) -> None:
        self.paste()
