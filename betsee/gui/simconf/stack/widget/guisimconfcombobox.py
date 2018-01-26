#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QComboBox`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal  #, Slot
from PySide2.QtWidgets import QComboBox
# from betse.util.io.log import logs
from betse.util.type import iterables
from betse.util.type.mapping import mappings
from betse.util.type.types import type_check, EnumClassType
from betsee.guiexception import BetseePySideComboBoxException
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditenum import (
    QBetseeSimConfEditEnumWidgetMixin)
from collections import OrderedDict

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfEnumComboBox(
    QBetseeSimConfEditEnumWidgetMixin, QComboBox):
    '''
    Simulation configuration-specific combo box widget, permitting high-level
    enumeration members backed by low-level raw strings in external simulation
    configuration files to be interactively edited.

    To guarantee a one-to-one correspondence between the currently selected
    combo box item and the enumeration constraining these items, this combo box
    is non-editable (i.e., item text is *not* manually editable).

    See Also
    ----------
    :class:`QBetseeSimConfEnumRadioButtonGroup`
        Alternative simulation configuration-specific widget subclass similarly
        permitting high-level enumeration members to be interactively edited.
        That subclass is both less cumbersome to initialize *and* preferable from
        the user experience (UX) perspective for sufficiently small enumerations
        (e.g., containing five or fewer members).
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Disable editability, preventing users from manually editing item text.
        # (Though editability is technically disabled by our superclass by
        # default, this is sufficiently important to warrant disabling anyway.)
        self.setEditable(False)


    @type_check
    def init(
        self, enum_member_to_item_text: OrderedDict, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this widget.

        Parameters
        ----------
        enum_member_to_item_text : OrderedDict
            Ordered dictionary mapping from each member of the enumeration
            encapsulated by the passed ``sim_conf_alias`` parameter to the
            human-readable text of the combo box item describing that member.
            The dictionary ordering of these enumeration members exactly defines
            the order in which the corresponding combo box items are listed.

        All remaining parameters are passed as is to the superclass method.

        Raises
        ----------
        BetseMappingException
            If this dictionary is *not* safely invertible (i.e., if any value of
            this dictionary is non-uniquely assigned to two or more keys).
        BetseePySideComboBoxException
            If the number of members in this enumeration differs from the number
            of members mapped by (i.e., of keys in) this dictionary.
        '''

        # Dictionary mapping from each enumeration member to the corresponding
        # mutually exclusive value displayed by this widget -- which, in this
        # case, is the 0-based index of that combo box item.
        enum_member_to_widget_value = {
            enum_member: item_index
            for item_index, enum_member in enumerate(
                enum_member_to_item_text.keys())
        }

        # Initialize our superclass with all such parameters.
        super().init(
            *args,
            enum_member_to_widget_value=enum_member_to_widget_value,
            **kwargs)

        # Sequence of the human-readable text of all combo box items.
        #
        # Since a view of ordered dictionary values is a valid sequence, the
        # QComboBox.addItems() method passed this sequence below should
        # technically accept this view *WITHOUT* requiring explicit coercion
        # into a tuple. It does not, raising the following exception on
        # attempting to do so:
        #
        #    TypeError: 'PySide2.QtWidgets.QComboBox.addItems' called with wrong argument types:
        #      PySide2.QtWidgets.QComboBox.addItems(ValuesView)
        #    Supported signatures:
        #      PySide2.QtWidgets.QComboBox.addItems(QStringList)
        #
        # Presumably, the underlying bindings generator (i.e., Shiboken2) only
        # implicitly coerces tuples and lists into "QStringList" instances.
        # Curiously, generic sequences appear to remain unsupported.
        items_text = tuple(enum_member_to_item_text.values())

        # Populate the contents of this combo box from this sequence.
        self.addItems(items_text)

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:

        return QCoreApplication.translate(
            'QBetseeSimConfEnumComboBox', 'changes to a combo box')


    @property
    def _finalize_widget_change_signal(self) -> Signal:

        return self.currentIndexChanged

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> int:

        return self.currentIndex()


    @widget_value.setter
    @type_check
    def widget_value(self, widget_value: int) -> None:

        # Set this widget's displayed value to the passed value by calling the
        # setCurrentIndex() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        super().setCurrentIndex(widget_value)


    def _reset_widget_value(self) -> None:

        # Reset this combo box by arbitrarily selecting its first item. Note
        # this is distinct from the clear() method defined by our superclass,
        # removing all existing items from this combo box. Calling that method
        # would be highly undesirable here.
        self.widget_value = 0
