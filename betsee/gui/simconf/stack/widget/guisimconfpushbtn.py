#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`QPushButton`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QLineEdit, QPushButton
from betse.util.path import pathnames
from betse.util.type.types import type_check
from betsee.gui.simconf.stack.widget.abc.guisimconfwdg import (
    QBetseeWidgetMixinSimConf)

# ....................{ SUBCLASSES ~ subdir                }....................
class QBetseeSimConfPushButtonSubDir(QBetseeWidgetMixinSimConf, QPushButton):
    '''
    :mod:`QPushButton`-based widget displaying a dialog on being clicked
    requesting the user select an existing subdirectory of an arbitrary parent
    directory *and* setting the contents of an associated :mod:`QLineEdit`-based
    "buddy" widget to the relative pathname of this subdirectory with respect to
    this parent directory.

    Attributes
    ----------
    _line_edit : QLineEdit
        Textual "buddy" widget associated with this button.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._line_edit = None


    @type_check
    def init(self, line_edit: QLineEdit, *args, **kwargs) -> None:
        '''
        Finalize this button's initialization.

        Parameters
        ----------
        line_edit : QLineEdit
            Textual "buddy" widget associated with this button.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Finalize the initialization of our superclass.
        super().init(*args, **kwargs)

        # Classify all passed parameters.
        self._line_edit = line_edit

        # Connect this button's click signal to a slot displaying this directory
        # dialog *AFTER* defining all instance variables accessed by this slot.
        self.clicked.connect(self._select_subdir)

    # ..................{ SLOTS                              }..................
    @Slot()
    def _select_subdir(self) -> None:
        '''
        Slot displaying a dialog requesting the user select an existing
        subdirectory of an arbitrary parent directory *and* setting the contents
        of an associated :mod:`QLineEdit`-based "buddy" widget to the relative
        pathname of this subdirectory with respect to this parent directory.

        This slot is connected to the :attr:`clicked` signal at widget
        finalization time, for safety.
        '''

        # Avoid circular import dependencies.
        from betsee.util.path import guidir

        # Absolute pathname of the directory containing the current simulation
        # configuration to request the user select a subdirectory of.
        parent_dirname = self._sim_conf.dirname

        # Absolute pathname of the currently configured subdirectory of this
        # parent directory to initially display in this dialog.
        current_dirname = pathnames.join(parent_dirname, self._line_edit.text())

        # Relative pathname of an existing subdirectory of this parent if this
        # dialog was not canceled *OR* "None" otherwise.
        subdirname = guidir.select_subdir(
            parent_dirname=parent_dirname, current_dirname=current_dirname)

        # If this dialog was *NOT* canceled...
        if subdirname is not None:
            # Set the contents of our buddy widget to this pathname.
            self._line_edit.setText(subdirname)
