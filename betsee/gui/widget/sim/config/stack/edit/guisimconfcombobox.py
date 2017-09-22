#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QComboBox`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal
from PySide2.QtWidgets import QComboBox
from betse.util.type.types import ClassOrNoneTypes, EnumType
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfEnumComboBox(
    QBetseeSimConfEditScalarWidgetMixin, QComboBox):
    '''
    Simulation configuration-specific combo box widget, permitting high-level
    enumeration members backed by low-level raw strings in external simulation
    configuration files to be interactively edited.

    To guarantee a one-to-one correspondence between the currently selected
    combo box item and the enumeration constraining these items, this combo box
    is non-editable (i.e., item text is *not* manually editable).

    Attributes
    ----------
    _item_index_to_enum_member : MappingType
        Dictionary mapping from each member of the enumeration provided by
        the passed ``sim_conf_alias`` parameter to the human-readable text
        of the combo box item describing that member. If this dictionary is
        *not* safely invertible (i.e., if any value of this dictionary is
        non-uniquely assigned to two or more keys), an exception is raised.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Disable editability, preventing users from manually editing item text.
        # (Though editability is technically disabled by our superclass by
        # default, this is sufficiently important to warrant disabling anyway.)
        self.setEditable(False)

    #FIXME: If do actually require dictionary reversibility, the simplest
    #solution would be to simply require callers pass specific
    #"OneToOneDict"-based dictionaries rather than "MappingType" instances.
    @type_check
    def init(
        self, enum_member_to_item_text: MappingType, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this widget.

        Parameters
        ----------
        enum_member_to_item_text : MappingType
            Dictionary mapping from each member of the enumeration provided by
            the passed ``sim_conf_alias`` parameter to the human-readable text
            of the combo box item describing that member. If this dictionary is
            *not* safely invertible (i.e., if any value of this dictionary is
            non-uniquely assigned to two or more keys), an exception is raised.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Initialize our superclass with all remaining parameters.
        super().init(*args, **kwargs)

        # Enumeration constraining this simulation configuration alias.
        enum_type = self._sim_conf_alias.data_desc.expr_enum_alias_type

        #FIXME: If the size of this dictionary differs from that of this
        #enumeration, raise an exception.

        #FIXME: Populate the contents of this combo box from this dictionary.

    # ..................{ SUPERCLASS ~ setter                }..................
    #FIXME: Blatantly wrong, obviously. No idea what superclass method should be
    #overridden here, at the moment.
    def setComboed(self, value_new: bool) -> None:

        # Defer to the superclass setter.
        super().setComboed(value_new)

        # If this configuration is currently open, set the current value of this
        # simulation configuration alias to this widget's current value.
        self._set_alias_to_widget_value_if_sim_conf_open()

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfComboBox', 'changes to a combo box')


    #FIXME: Actually, this should probably just be "currentIndexChanged" in this
    #case, no?
    @property
    def _finalize_widget_edit_signal(self) -> Signal:

        # All other modification signals exposed by our widget superclass (e.g.,
        # "QComboBox.currentIndexChanged") are subsumed by the following
        # general-purpose parent signal.
        return self.currentTextChanged


    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:
        return EnumType

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> object:
        return .


    #FIXME: Patch us up, please.
    @widget_value.setter
    def widget_value(self, widget_value: object) -> None:

        # Set this widget's displayed value to the passed value by calling the
        # setComboed() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        super().setComboed(widget_value)


    #FIXME: Arbitrarily select the first item in this combo box.
    def _clear_widget_value(self) -> None:
        self.widget_value =


    def _get_alias_from_widget_value(self) -> object:

        # Value displayed by this widget, coerced into a type expected by this
        # simulation configuration alias. Since both expect the same type of
        # enumeration members, the same value is safely usable in both contexts
        # *WITHOUT* requiring type coercion.
        #
        # The standard isinstance()-style test performed by our superclass
        # method fails to suffice for enumerations, requiring that we manually
        # reduce this method to a trivial getter. Specifically:
        #
        #     # This test *ALWAYS* evaluates to False, as "self.widget_value" is
        #     # an enumeration member and "self._sim_conf_alias_types" simply an
        #     # an enumeration. (Such is code life.)
        #     isinstance(self.widget_value, self._sim_conf_alias_type)
        return self.widget_value
