#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QCheckBox`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal
from PySide2.QtWidgets import QCheckBox
from betse.util.type.types import ClassOrNoneTypes
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfCheckBox(QBetseeSimConfEditScalarWidgetMixin, QCheckBox):
    '''
    Simulation configuration-specific check box widget, permitting booleans
    backed by external simulation configuration files to be interactively
    edited.
    '''

    # ..................{ SUPERCLASS ~ setter                }..................
    def setChecked(self, value_new: bool) -> None:

        # Defer to the superclass setter.
        super().setChecked(value_new)

        # If this configuration is currently open, set the current value of this
        # simulation configuration alias to this widget's current value.
        self._set_alias_to_widget_value_if_sim_conf_open()

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfSpinBoxWidgetMixin', 'edits to a check box')


    @property
    def _finalize_widget_edit_signal(self) -> Signal:
        return self.toggled


    @property
    def _widget_type_strict(self) -> ClassOrNoneTypes:
        return bool

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> object:
        return self.isChecked()


    @widget_value.setter
    def widget_value(self, widget_value: object) -> None:

        # Set this widget's displayed value to the passed value by calling the
        # setChecked() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        super().setChecked(widget_value)

    # ..................{ MIXIN                              }..................
    def _clear_widget_value(self) -> None:
        self.widget_value = False