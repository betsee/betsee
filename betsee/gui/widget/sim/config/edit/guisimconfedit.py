#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Simulation configuration-specific editable widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot
from PySide2.QtWidgets import (
    QLineEdit,
)
# from betse.util.io.log import logs
# from betse.util.type.types import type_check
from betsee.gui.widget.sim.config.edit.guisimconfeditabc import (
    QBetseeSimConfigEditWidgetMixin)
from betsee.util.widget.undo.psdundocmd import QBetseeLineEditUndoCommand

# ....................{ SUBCLASSES ~ text                  }....................
class QBetseeSimConfigLineEdit(QBetseeSimConfigEditWidgetMixin, QLineEdit):
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

        # Connect all relevant signals to slots.
        self.textChanged.connect(self._text_changed_undoable)
        self.editingFinished.connect(self._editing_finished_undoable)

    # ..................{ SLOTS                              }..................
    @Slot(str)
    def _text_changed_undoable(self, text_new: str) -> None:
        '''
        Slot signalled on each edit of the contents of this widget.

        This includes each:

        * Unfinalized interactive user edit *not* resulting in the
          :meth:`_editing_finished_undoable` method being signalled.
        * Finalized interactive user edit resulting in the
          :meth:`_editing_finished_undoable` method being signalled.
        * Finalized programmatic call to the :meth:`setText` method *not*
          resulting in the :meth:`_editing_finished_undoable` method being
          signalled.

        Parameters
        ----------
        text_new : str
            New contents of this widget. Since such contents are identical to
            those returned by the :class:`text` method, this parameter is
            equally redundant and useless.
        '''

        # If this change is the result of a finalized programmatic call to the
        # setText() method, cache this widget's new text by effectively emitting
        # the editingFinished() signal. Since actually emitting that signal in
        # this case could conceivably provoke bad things, the slot handling this
        # signal is called directly.
        if not self.isModified():
            self._editing_finished_undoable()
        # Else, this change is the result of an unfinalized (and hence
        # ignorable) interactive user edit. For efficiency, ignore this edit.
        #
        # Differentiating these two cases reduces to testing the isModified()
        # property. To quote the official "QLineEdit" documentation:
        #
        # "This property holds whether the line edit's contents has been
        #  modified by the user. The modified flag is never read by QLineEdit;
        #  it has a default value of false and is changed to true whenever the
        #  user changes the line edit's contents. Calling setText() resets the
        #  modified flag to false."


    @Slot()
    def _editing_finished_undoable(self) -> None:
        '''
        Slot signalled on each finalized interactive user (but *not*
        programmatic) edit of the contents of this widget.
        '''

        # Ensure that any subsequent signalling of the _text_changed_undoable()
        # slot by any finalized programmatic edit also triggers this slot.
        self.setModified(False)

        # If prior text for this widget has been cached, this edit is undoable.
        # In this case, push an undo command onto the undo stack permitting this
        # edit to be undone *BEFORE* updating the "_text_cached" variable.
        if self._text_cached is not None:
            self._undo_stack.push(QBetseeLineEditUndoCommand(
                widget=self, value_old=self._text_cached))

        # Cache this widget's new text in preparation for the next edit.
        self._text_cached = self.text()

        # Notify all connected slots that the currently open simulation
        # configuration has received new unsaved changes.
        self._enable_sim_conf_dirty()
