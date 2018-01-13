#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QLineEdit`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal
from PySide2.QtWidgets import QLineEdit
#from betse.util.io.log import logs
from betse.util.type.types import type_check, NoneType
from betsee.gui.simconf.stack.widget.guisimconfpushbtn import (
    QBetseeSimConfPushButtonABC)
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditscalar import (
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
    Simulation configuration-specific line edit widget, interactively editing
    single-line strings backed by external simulation configuration files.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def init(
        self,
        push_btn: (QBetseeSimConfPushButtonABC, NoneType) = None,
        *args, **kwargs
    ) -> None:
        '''
        Finalize the initialization of this widget, optionally associated with a
        simulation configuration-specific push button "buddy" widget.

        If non-``None``, this push button is typically situated to the right of
        this line edit. If this line edit edits a pathname, this push button
        typically displays the text "Browse..." and when clicked displays a path
        dialog to interactively select this pathname.

        Parameters
        ----------
        push_btn : (QBetseeSimConfPushButtonABC, NoneType)
            Simulation configuration-specific push button "buddy" widget
            associated with this widget. This push button is initialized by this
            method in a manner informing this push button of this association;
            hence, this push button must *not* be externally initialized.
            Defaults to ``None``, in which case this widget is assumed to be
            associated with no such push button.

        All remaining parameters are passed as is to the superclass
        :meth:`QBetseeSimConfEditScalarWidgetMixin.init` method.
        '''

        # Initialize our superclass with all remaining arguments.
        super().init(*args, **kwargs)

        # If this line edit is associated with a push button, inform the latter
        # of this association.
        if push_btn is not None:
            push_btn.init(sim_conf=self._sim_conf, line_edit=self)

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
