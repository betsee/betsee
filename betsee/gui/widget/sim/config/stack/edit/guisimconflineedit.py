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
from betse.util.type.types import type_check  #, ClassOrNoneTypes
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)
from betsee.util.widget.abc.guiclipboardabc import (
    QBetseeClipboardScalarWidgetMixin)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfLineEdit(
    QBetseeClipboardScalarWidgetMixin,
    QBetseeSimConfEditScalarWidgetMixin,
    QLineEdit,
):
    '''
    Simulation configuration-specific line edit widget, permitting single-line
    strings backed by external simulation configuration files to be
    interactively edited.
    '''

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
    def _finalize_widget_change_signal(self) -> Signal:
        return self.editingFinished

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> str:
        return self.text()


    @widget_value.setter
    @type_check
    def widget_value(self, widget_value: str) -> None:

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


    def _reset_widget_value(self) -> None:
        self.widget_value = ''
