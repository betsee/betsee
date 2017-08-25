#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QLineEdit`-based simulation configuration widget subclasses.
'''

#FIXME: Excellent. That said, all existing numeric line edits should ideally be
#refactored into numeric spinners. For expediency, perhaps we'll neglect
#implementing undo functionality in such spinners? We should at least define a
#new editable widget subclass for spinners, however. It'll ease the pain later.

#FIXME: Once complete, generalize the commonality shared between this and the
#"guisimconflineedit" submodule into a new
#"guisimconfwdgedit.QBetseeWidgetEditScalarSimConfMixin" superclass.

#FIXME: Improve the init() method to internally call the self.setMinimum()
#and/or self.setMaximum() methods with a range of permissible values specific to
#the current "self._sim_conf_alias" data descriptor. Although the expr_alias()
#function currently provides no means of explicitly defining this range, it
#*DOES* provide a means of passing a predicate callable which could actually be
#a callable class (i.e., class defining the __call__() special method)
#explicitly defining and exposing this range as public instance variables.
#Specifically, we might define the following predicate classes:
#
#    class PredicateUnaryABC(meta=ABC):
#        '''
#        **Unary predicate** (i.e., callable class whose :meth:`__call__`
#        special method accepts a single value to be tested and returns ``True``
#        only if this value satisfies this predicate).
#        '''
#
#        @abstractmethod
#        def __call__(self, value: object) -> bool:
#            pass
#
#
#    class PredicateUnaryRange(PredicateUnaryABC):
#
#        @type_check
#        def __init__(
#            self, min: NumericOrNoneTypes, max: NumericOrNoneTypes) -> None:
#            self.min = min
#            self.max = max
#
#        def __call__(self, value: object) -> bool:
#            return (
#               (self.min is None or value >= self.min) and
#               (self.max is None or value <= self.max)
#            )
#
#The expr_alias() function would then need to additionally expose the passed
#predicate (if any) by declaring a new instance variable "expr_alias_predicate"
#on the instance of the class returned by that function.
#
#Given that, the init() method could then internally call:
#
#    predicate = self._sim_conf_alias.data_desc.predicate
#
#    if isinstance(predicate, PredicateUnaryRange):
#        if predicate.min is not None:
#            self.setMinimum(predicate.min)
#        if predicate.max is not None:
#            self.setMinimum(predicate.max)
#
#It's *NOT* hard. It's mostly just tedious. But it *MUST* be done to prevent
#users from entering invalid numeric data. (Let us see this through, please.)

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QDoubleSpinBox
from betse.util.io.log import logs
from betse.util.type.numeric import floats
from betsee.guiexceptions import BetseePySideSpinBoxException
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgedit import (
    QBetseeWidgetEditMixinSimConf)
from betsee.util.widget.guiundocmd import QBetseeUndoCommandNumericSpinBox

# ....................{ SUBCLASSES                         }....................
class QBetseeDoubleSpinBoxSimConf(
    QBetseeWidgetEditMixinSimConf, QDoubleSpinBox):
    '''
    Simulation configuration-specific floating point spin box widget, permitting
    a simulation configuration floating point value backed by an external YAML
    file to be interactively edited.

    Attributes
    ----------
    _value_prev : float
        Floating point value of this widget cached on the completion of the most
        recent user edit (i.e., :meth:`editingFinished` signal) and hence *not*
        necessarily reflecting the current state of this widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._value_prev = None

        # Enable so-called "acceleration," both increasing and decreasing the
        # rate at which the displayed number changes as a function of the
        # duration of time that the spon box GUI arrows are depressed.
        self.setAccelerated(True)

        # Align the displayed number against the right rather than left internal
        # edge of this spin box -- the typical default in most GUI frameworks.
        # (For unclear reasons, Qt defaults to right alignment.)
        self.setAlignment(Qt.AlignRight)

        # Disable so-called "keyboard tracking," reducing signal verbosity by
        # preventing the superclass from emitting valueChanged() signals on each
        # key entered by the user (e.g., on all three of the "3", "1", and "4"
        # keys entered by the user to enter the integer "314").
        #
        # Instead, the valueChanged() signal will *ONLY* be emitted when:
        #
        # * The return key is pressed.
        # * Keyboard focus is lost.
        # * Other spinbox functionality is activated (e.g., an up or down arrow
        #   key is pressed, the up or down graphical arrow is clicked).
        self.setKeyboardTracking(False)


    def init(self, *args, **kwargs) -> bool:

        # Initialize our superclass with all passed parameters.
        super().init(*args, **kwargs)

        # If this simulation configuration alias accepts values of either...
        if (
            # Multiple types but *NOT* floating point or...
            (self._sim_conf_alias_type is tuple and
             float not in self._sim_conf_alias_type) or
            # A single type that is *NOT* floating point...
            (self._sim_conf_alias_type is not tuple and
             not issubclass(self._sim_conf_alias_type, float))
        # ...then this spin box is incompatible with this alias. In this case,
        # an exception is raised.
        ):
            raise BetseePySideSpinBoxException(
                'Simulation configuration alias type(s) {!r} '
                'incompatible with {!r}.'.format(
                    self._sim_conf_alias_type, float))

        # Connect all relevant signals to slots *AFTER* initializing our
        # superclass. See the superclass method for details.
        self.editingFinished.connect(self._editing_finished_undoable)

    # ..................{ SETTERS                            }..................
    def setValue(self, value_new: str) -> None:

        # Defer to the superclass setter.
        super().setValue(value_new)

        # If this configuration is currently open, set the current value of this
        # simulation configuration alias to this widget's current value.
        if self._is_open:
            self._set_alias_to_widget_value()

        # Finalize this programmatic change of the contents of this widget.
        self._editing_finished_undoable()

    # ..................{ SLOTS                              }..................
    @Slot(str)
    def _set_filename(self, filename: str) -> None:

        # Call the superclass method first.
        super()._set_filename(filename)

        # If this configuration is currently open, set this widget's displayed
        # value to the current value of this simulation configuration alias.
        if filename:
            self._set_widget_value_to_alias()

        # Cache this widget's currently displayed value in preparation for the
        # next edit.
        self._value_prev = self.value()


    @Slot()
    def _editing_finished_undoable(self) -> None:
        '''
        Slot signalled on each finalized interactive user (but *not*
        programmatic) edit of the contents of this widget.
        '''

        # Log this edit.
        logs.log_debug(
            'Finalizing editable widget "%s" change...', self.object_name)

        # Value currently displayed by this widget's.
        value_curr = self.value()

        # If this widget's contents have changed: specifically, if...
        if (
            # Prior text has been cached for this widget.
            self._value_prev is not None and
            # This prior text differs from this current text.
            self._value_prev != value_curr
        ):
            # Push an undo command onto the stack (permitting this edit to be
            # undone) *BEFORE* updating the "_value_prev" variable.
            self._push_undo_cmd_if_safe(QBetseeUndoCommandNumericSpinBox(
                widget=self, value_old=self._value_prev))

            # Notify all connected slots that the currently open simulation
            # configuration has received new unsaved changes *AFTER* pushing an
            # undo command onto the stack. Why? Because this method detects
            # unsaved changes by deferring to the stack state.
            self._update_sim_conf_dirty()

        # Cache this widget's newly displayed value in preparation for the next
        # edit.
        self._value_prev = value_curr

    # ..................{ CONVERTERS                         }..................
    def _set_alias_to_widget_value(self) -> None:
        '''
        Set the current value of this widget's simulation configuration alias to
        this widget's displayed value if a simulation configuration is currently
        open *or* raise an exception otherwise.
        '''

        # If no simulation configuration is currently open, raise an exception.
        self._sim_conf.die_unless_open()

        # Displayed value of this widget.
        alias_value = self.value()

        # If this value is *NOT* of this type...
        if not isinstance(alias_value, self._sim_conf_alias_type):
            alias_type = self._sim_conf_alias_type

            #FIXME: Non-ideal, obviously. Sadly, no better ideas come to mind.

            # If this type is an tuple of such types (e.g., "NumericTypes")
            # rather than a single type, arbitrarily coerce this value into the
            # type selected by the first item of this tuple.
            if alias_type is tuple:
                alias_type = alias_type[0]

            # Coerce this value into this type.
            alias_value = alias_type(alias_value)

        # Set this alias' current value to this coerced value.
        self._sim_conf_alias.set(alias_value)


    def _set_widget_value_to_alias(self) -> None:
        '''
        Set this widget's displayed value to the current value of this widget's
        simulation configuration alias if a simulation configuration is
        currently open *or* raise an exception otherwise.
        '''

        # If no simulation configuration is currently open, raise an exception.
        self._sim_conf.die_unless_open()

        # Current value of this alias.
        widget_value = self._sim_conf_alias.get()

        #FIXME: Required for textual but *NOT* numeric content.

        # If this value is *NOT* a number, coerce this value into a number.
        # if not isinstance(widget_value, float):
        #     widget_value = float(widget_value)

        #FIXME: Required for numeric but *NOT* textual content.

        # Precision (i.e., significand length) of this floating point number.
        widget_value_precision = floats.get_precision(widget_value)

        # Set the precision of this widget's displayed value to the largest of:
        self.setDecimals(max(
            # A reasonable default precision.
            3,
            # The current precision of this widget's displayed value.
            self.decimals(),
            # The current precision of this alias' actual value.
            widget_value_precision,
        ))

        # Set this widget's displayed value to this alias' value by calling the
        # setValue() method of our superclass rather than this class,
        # avoiding triggering the interactive-only logic of the latter.
        super().setValue(widget_value)
