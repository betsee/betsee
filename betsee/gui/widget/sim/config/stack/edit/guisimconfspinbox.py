#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
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
from PySide2.QtWidgets import QDoubleSpinBox
#from betse.util.io.log import logs
from betse.util.type.numeric import floats
from betse.util.type.types import ClassOrNoneTypes
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimConfSpinBoxWidgetMixin(
    QBetseeSimConfEditScalarWidgetMixin):
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
    def _finalize_widget_edit_signal(self) -> Signal:
        return self.editingFinished

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfIntegerSpinBox(
    QBetseeSimConfSpinBoxWidgetMixin, QDoubleSpinBox):
    '''
    Simulation configuration-specific integer spin box widget, permitting
    integers backed by external simulation configuration files to be
    interactively edited.
    '''

    # ..................{ MIXIN                              }..................
    @property
    def _widget_type_strict(self) -> ClassOrNoneTypes:
        return int


    @QBetseeSimConfSpinBoxWidgetMixin.widget_value.setter
    def widget_value(self, widget_value: object) -> None:
        super().setValue(widget_value)


    def _clear_widget_value(self) -> None:
        self.widget_value = 0


class QBetseeSimConfDoubleSpinBox(
    QBetseeSimConfSpinBoxWidgetMixin, QDoubleSpinBox):
    '''
    Simulation configuration-specific floating point spin box widget, permitting
    floating point values backed by external simulation configuration files to
    be interactively edited.
    '''

    # ..................{ MIXIN                              }..................
    @property
    def _widget_type_strict(self) -> ClassOrNoneTypes:
        return float


    @QBetseeSimConfSpinBoxWidgetMixin.widget_value.setter
    def widget_value(self, widget_value: object) -> None:

        # Precision (i.e., significand length) of this floating point number.
        widget_value_precision = floats.get_precision(widget_value)

        # Set the precision of this widget's displayed value to the largest of:
        self.setDecimals(max(
            # A reasonable default precision.
            3,
            # The current precision of this widget's displayed value.
            self.decimals(),
            # The current precision of this alias' actual value, incremented by
            # one to permit this value to be decreased an additional place.
            widget_value_precision + 1,
        ))

        # Set this widget's displayed value to the passed value by calling the
        # setValue() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        super().setValue(widget_value)


    def _clear_widget_value(self) -> None:
        self.widget_value = 0.0
