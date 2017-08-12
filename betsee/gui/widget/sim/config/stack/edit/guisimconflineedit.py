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
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgedit import (
    QBetseeWidgetEditMixinSimConf)
from betsee.util.widget.guiundocmd import QBetseeUndoCommandLineEdit

# ....................{ SUBCLASSES ~ widget                }....................
class QBetseeLineEditSimConf(QBetseeWidgetEditMixinSimConf, QLineEdit):
    '''
    Simulation configuration-specific line edit widget, permitting a simulation
    configuration string value backed by an external YAML file to be
    interactively edited.

    Attributes
    ----------
    _text_prev : str
        Text contents of this widget cached on the completion of the most recent
        user edit (i.e., :meth:`editingFinished` signal) and hence *not*
        necessarily reflecting the current state of this widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._text_prev = None


    def init(self, *args, **kwargs) -> bool:

        # Initialize our superclass with all passed parameters.
        super().init(*args, **kwargs)

        # Connect all relevant signals to slots *AFTER* initializing our
        # superclass. See the superclass method for details.
        self.editingFinished.connect(self._editing_finished_undoable)

    # ..................{ SETTERS                            }..................
    def setText(self, text_new: str) -> None:

        # Defer to the superclass setter.
        super().setText(text_new)

        # Finalize this programmatic change of the contents of this widget.
        self._editing_finished_undoable()

    # ..................{ SLOTS                              }..................
    @Slot(str)
    def _set_filename(self, filename: str) -> None:

        # Call the superclass method first.
        super()._set_filename(filename)

        # Current value of this widget's simulation configuration alias if a
        # simulation configuration is currently open *OR* "None" otherwise.
        sim_conf_alias_value = None

        # If such a configuration is open...
        if filename:
            # Obtain this value from this configuration.
            sim_conf_alias_value = self._sim_conf_alias.get()

            # Set this widget's current text to this value by calling the setText()
            # method of our superclass rather than this class, preventing the
            # interactive-only logic of the latter from being triggered.
            super().setText(sim_conf_alias_value)

        # Cache this widget's current text in preparation for the next edit.
        self._text_prev = sim_conf_alias_value


    @Slot()
    def _editing_finished_undoable(self) -> None:
        '''
        Slot signalled on each finalized interactive user (but *not*
        programmatic) edit of the contents of this widget.
        '''

        # Log this edit.
        logs.log_debug(
            'Finalizing line edit "%s" change...', self.object_name)

        # Current text of this widget's contents.
        text_curr = self.text()

        # If this widget's contents have changed: specifically, if...
        if (
            # Prior text has been cached for this widget.
            self._text_prev is not None and
            # This prior text differs from this current text.
            self._text_prev != text_curr
        ):
            # Push an undo command onto the stack (permitting this edit to be
            # undone) *BEFORE* updating the "_text_prev" variable.
            self._push_undo_cmd_if_safe(QBetseeUndoCommandLineEdit(
                widget=self, value_old=self._text_prev))

            # Notify all connected slots that the currently open simulation
            # configuration has received new unsaved changes *AFTER* pushing an
            # undo command onto the stack. Why? Because this method detects
            # unsaved changes by deferring to the stack state.
            self._update_sim_conf_dirty()

        # Cache this widget's new text in preparation for the next edit.
        self._text_prev = text_curr
