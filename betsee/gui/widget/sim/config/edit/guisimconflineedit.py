#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QLineEdit`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QLineEdit
from betse.util.io.log import logs
# from betse.util.type.types import type_check
from betsee.gui.widget.sim.config.edit.guisimconfeditabc import (
    QBetseeWidgetMixinSimConfigEdit)
from betsee.util.widget.psdundocmd import (
    QBetseeUndoCommandLineEdit)  #, QBetseeUndoCommandNull)

# ....................{ SUBCLASSES ~ widget                }....................
class QBetseeLineEditSimConfig(QBetseeWidgetMixinSimConfigEdit, QLineEdit):
    '''
    Simulation configuration-specific line edit widget, permitting a simulation
    configuration string value backed by an external YAML file to be
    interactively edited.

    Attributes
    ----------
    _text_cached : str
        Text contents of this widget cached on the completion of the most recent
        user edit (i.e., :meth:`editingFinished` signal) and hence *not*
        necessarily reflecting the current state of this widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._text_cached = None



    def init(self, *args, **kwargs) -> bool:

        # Initialize our superclass with all passed parameters.
        super().init(*args, **kwargs)

        # Connect all relevant signals to slots *AFTER* initializing our
        # superclass. See the supercrass method for details.
        self.editingFinished.connect(self._editing_finished_undoable)

    # ..................{ SETTERS                            }..................
    def setText(self, text_new: str) -> None:

        # Defer to the superclass setter.
        super().setText(text_new)

        # Cache this widget's new text in preparation for the next edit.
        self._text_cached = self.text()

        # Notify all connected slots that the currently open simulation
        # configuration has received new unsaved changes. As this setter is
        # typically called *BEFORE* this widget has been initialized with a
        # simulation configuration, this notification is performed *ONLY* if
        # this widget is indeed fully initialized.
        self._enable_sim_conf_dirty_if_initted()

    # ..................{ SLOTS                              }..................
    @Slot()
    def _editing_finished_undoable(self) -> None:
        '''
        Slot signalled on each finalized interactive user (but *not*
        programmatic) edit of the contents of this widget.
        '''

        # Log this edit.
        logs.log_debug(
            'Finalizing edit of editable widget "%s"...', self.object_name)

        # If prior text for this widget has been cached, this edit is undoable.
        # In this case, push an undo command onto the undo stack permitting this
        # edit to be undone *BEFORE* updating the "_text_cached" variable.
        # elif self._text_cached is not None:
        if self._text_cached is not None:
            # self._undo_stack.push(QBetseeUndoCommandNull('wut'))
            self._undo_stack.push(QBetseeUndoCommandLineEdit(
                widget=self, value_old=self._text_cached))

        # Cache this widget's new text in preparation for the next edit.
        self._text_cached = self.text()

        # Notify all connected slots that the currently open simulation
        # configuration has received new unsaved changes.
        self._enable_sim_conf_dirty()
