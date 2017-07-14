#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

# ....................{ IMPORTS                            }....................
from abc import ABCMeta  #, abstractmethod
from PySide2.QtCore import Slot
from PySide2.QtWidgets import (
    QLineEdit,
)
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.gui.widget.sim.config.guisimconf import QBetseeSimConfig

# ....................{ MIXINS                             }....................
class QBetseeSimConfigWidgetMixin(object, metaclass=ABCMeta):
    '''
    Abstract base class of all **editable simulation configuration widget**
    (i.e., widgets permitting one or more simulation configuration values stored
    in an external YAML file to be interactively edited) subclasses.

    Design
    ----------
    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be subclassed *first* rather than *last* in subclasses.

    Attributes
    ----------
    _sim_conf : QBetseeSimConfig
        High-level state of the currently open simulation configuration, which
        depends on the state of this low-level simulation configuration widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf = None


    @type_check
    def init(self, sim_conf: QBetseeSimConfig) -> bool:
        '''
        Initialize this widget against the passed state object.

        Parameters
        ----------
        sim_conf : QBetseeSimConfig
            High-level state of the currently open simulation configuration.
        '''

        # Classify all passed parameters. Since the main window rather than this
        # state object owns this widget, retaining a reference to this state
        # object introduces no circularity and hence is safe. (That's nice.)
        self._sim_conf = sim_conf

    # ..................{ ENABLERS                           }..................
    def _enable_sim_conf_dirty(self) -> None:
        '''
        Enable the dirty staate for the current simulation configuration.

        This method is intended to be called by subclass slots on completion of
        user edits to the contents of this widget. In response, this method
        notifies all connected slots that this simulation configuration has
        received new unsaved changes.
        '''

        self._sim_conf.set_dirty_signal.emit(True)

# ....................{ SUBCLASSES ~ text                  }....................
class QBetseeSimConfigLineEdit(QBetseeSimConfigWidgetMixin, QLineEdit):
    '''
    Simulation configuration line edit widget, permitting a simulation
    configuration string value stored in an external YAML file to be
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
    #FIXME: Correctly implement the following slots. What we'd like to do is as
    #follows:
    #
    #* In _editing_finished_undoable(), push a new
    #  "QBetseeLineEditUndoCommand" instance onto the global undo stack. This
    #  implies, of course, that this object has access to that stack -- which it
    #  currently doesn't. Obtaining access to that stack here may prove sadly
    #  non-trivial, mostly because this object is instantiated by Qt Creator
    #  promotion rather than in pure Python. We see no alternative but to:
    #  * Define a new public init() method of this class accepting the
    #    "QUndoStack" instance acted upon by subsequent slots: e.g.,
    #    def init(undo_stack: QUndoStack) -> None:
    #  * Search all child widgets of the simulation configuration stack widget
    #    for instances of this class. Actually, the substantially more efficient
    #    approach is to:
    #    * Require that all "QLineEdit" objects in this stack widget have names
    #      prefixed by some identifier -- say, "sim_conf_stack_page_line_".
    #    * Simply search the "QBetseeMainWindow" instance for all matching
    #      instance variables. This should be substantially faster than
    #      dynamically searching widgets with Qt-based recursion.
    #  * For each such instance, call that instance's init() method.
    #  * Note that the generality of such an init() method strongly suggests
    #    that a mixin providing this init() functionality should be defined.
    #    It's trivial; but it's boilerplate... and that's bad.
    #* That's only half the battle, however. _editing_finished_undoable() only
    #  responds to finalized interactive edits; programmatic edits produced by
    #  calls to the setText() method *ONLY* emit the textChanged() signal.
    #  However, all ignorable interim (i.e., non-finalized) interactive edits
    #  *ALSO* emit the same signal. We need some means of differentiating
    #  between the two. In the former case, "self._text_cached = text_new"
    #  should be assigned (but *NO* undo command should be added to the stack).
    #  In the latter case, nothing should be done. According to the
    #  documentation, these two cases may be distinguished by testing the
    #  isModified() property. Why? Because:
    #
    #  "This property holds whether the line edit's contents has been modified
    #   by the user. The modified flag is never read by QLineEdit; it has a
    #   default value of false and is changed to true whenever the user changes
    #   the line edit's contents. Calling setText() resets the modified flag to
    #   false."
    #
    #Hence, the code might resemble:

    #FIXME: Docstring us up.
    @Slot(str)
    def _text_changed_undoable(self, text_new: str) -> None:

        # If this change is the result of a finalized programmatic call to the
        # setText() method, record this widget's text *WITHOUT* pushing an undo
        # command onto the undo stack.
        if not self.isModified():
            self._text_cached = text_new
        # Else, this change is the result of an unfinalized (and hence
        # ignorable) interactive user edit.


    #FIXME: Docstring us up.
    @Slot()
    def _editing_finished_undoable(self) -> None:

        self._text_cached = self.text()

        #FIXME: Push an undo command onto the undo stack.

        # Notify all connected slots that the currently open simulation
        # configuration has received new unsaved changes.
        self._enable_sim_conf_dirty()
