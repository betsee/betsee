#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QAbstractSpinBox`-based simulation configuration widget subclasses.
'''

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
from PySide2.QtCore import QCoreApplication, Qt, Signal
from PySide2.QtWidgets import QSpinBox
# from betse.util.io.log import logs
from betse.util.type.numeric import floats
from betse.util.type.types import type_check, ClassOrNoneTypes
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)
from betsee.util.widget.abc.guiclipboardabc import (
    QBetseeClipboardScalarWidgetMixin)
from betsee.util.widget.stock.guispinbox import QBetseeDoubleSpinBox

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimConfSpinBoxWidgetMixin(
    QBetseeClipboardScalarWidgetMixin, QBetseeSimConfEditScalarWidgetMixin):
    '''
    Abstract base class of all simulation configuration-specific subclasses,
    permitting numeric values (i.e., integers, floating point values) backed by
    external simulation configuration files to be interactively edited.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

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

    # ..................{ SUPERCLASS ~ setter                }..................
    def setValue(self, value_new: str) -> None:

        # logs.log_debug('In QBetseeSimConfSpinBoxWidgetMixin.setValue()...')

        # Defer to the superclass setter.
        super().setValue(value_new)

        # If this configuration is currently open, set the current value of this
        # simulation configuration alias to this widget's current value.
        self._set_alias_to_widget_value_if_sim_conf_open()

    # ..................{ MIXIN ~ property                   }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfSpinBoxWidgetMixin', 'edits to a spin box')


    @property
    def widget_value(self) -> object:
        return self.value()


    @property
    def _finalize_widget_change_signal(self) -> Signal:
        return self.editingFinished

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfIntSpinBox(
    QBetseeSimConfSpinBoxWidgetMixin, QSpinBox):
    '''
    Simulation configuration-specific integer spin box widget, permitting
    integers backed by external simulation configuration files to be
    interactively edited.
    '''

    # ..................{ MIXIN                              }..................
    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:
        return int


    @QBetseeSimConfSpinBoxWidgetMixin.widget_value.setter
    @type_check
    def widget_value(self, widget_value: int) -> None:

        # logs.log_debug('In QBetseeSimConfIntSpinBox.widget_value()...')

        # Set this widget's displayed value to the passed value by calling the
        # setValue() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        QSpinBox.setValue(self, widget_value)


    def _reset_widget_value(self) -> None:
        self.widget_value = 0


class QBetseeSimConfDoubleSpinBox(
    QBetseeSimConfSpinBoxWidgetMixin, QBetseeDoubleSpinBox):
    '''
    Simulation configuration-specific floating point spin box widget, permitting
    floating point numbers backed by external simulation configuration files to
    be interactively edited.
    '''

    # ..................{ MIXIN                              }..................
    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:
        return float


    # This method is typically called *ONLY* once on loading the current
    # simulation configuration, enabling this widget to reinitialize itself in a
    # manner dependent upon the current value of the associated alias.
    def _get_widget_from_alias_value(self) -> object:

        # Initial value of the floating point number returned by the simulation
        # configuration alias associated with this widget.
        widget_value = super()._get_widget_from_alias_value()

        # Base-10 precision (i.e., significand length) of this initial value.
        widget_value_precision = floats.get_base_10_precision(widget_value)

        # If this widget defers to the default single step (i.e., fractional
        # value by which to increment and decrement this widget's displayed
        # value on each push of this widget's up and down arrows) for
        # "QDoubleSpinBox" widgets...
        if self.singleStep() == self.SINGLE_STEP_DEFAULT:
            # Base-10 exponent of this initial value.
            widget_value_exponent = floats.get_base_10_exponent(widget_value)

            # Override the default single step with a widget-specific single
            # step incrementing and decrementing by a fraction of this initial
            # value. Specifically, a single step of a quarter of this initial
            # value's order of magnitude is set.
            #
            # For example, given initial values of:
            #
            # * "0.009", a single step of "0.00025" will be set.
            # * "1.729", a single step of "0.25" will be set.
            single_step_new = 2.5 * 10**(widget_value_exponent - 1)
            self.setSingleStep(single_step_new)
        # Else, this widget has a non-default single step (typically specified
        # at Qt Creator time). In this case, preserve this single step as is.

        # Refine this precision to the largest of:
        widget_value_precision = max(
            # This alias' precision, incremented by one to permit the end user
            # to interactively decrease this number an additional decimal place.
            widget_value_precision + 1,
            # A reasonable default precision.
            3,
        )

        # Set the precision of this widget's displayed value to this precision.
        # logs.log_debug(
        #     'Setting "%s" precision given %s to %d...',
        #     self.obj_name, widget_value, widget_value_precision)
        self.setDecimals(widget_value_precision)

        # Return this value.
        return widget_value


    @QBetseeSimConfSpinBoxWidgetMixin.widget_value.setter
    @type_check
    def widget_value(self, widget_value: float) -> None:

        # logs.log_debug('In QBetseeSimConfDoubleSpinBox.widget_value()...')

        # Set this widget's displayed value to the passed value by calling the
        # setValue() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        QBetseeDoubleSpinBox.setValue(self, widget_value)


    def _reset_widget_value(self) -> None:
        self.widget_value = 0.0
