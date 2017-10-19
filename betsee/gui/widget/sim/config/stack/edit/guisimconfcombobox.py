#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QComboBox`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal  #, Slot
from PySide2.QtWidgets import QComboBox
# from betse.util.io.log import logs
from betse.util.type import iterables
from betse.util.type.mapping import maputil
from betse.util.type.types import type_check, ClassOrNoneTypes, EnumClassType
from betsee.guiexceptions import BetseePySideComboBoxException
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)
from collections import OrderedDict

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
    _enum_member_to_item_index : MappingType
        Dictionary mapping from each member of the enumeration constraining this
        combo box to the 0-based index of the corresponding combo box item.
    _item_index_to_enum_member : SequenceTypes
        Sequence of all enumeration members, efficiently mapping from the
        0-based index of each combo box item to the corresponding member of the
        enumeration constraining this combo box.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._enum_member_to_item_index = None
        self._item_index_to_enum_member = None

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
            the order in which the corresponding combo box items are listed. If
            this dictionary is *not* safely invertible (i.e., if any value of
            this dictionary is non-uniquely assigned to two or more keys), an
            exception is raised.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Initialize our superclass with all remaining parameters.
        super().init(*args, **kwargs)

        # If this dictionary duplicates any combo box items, raise an exception.
        maputil.die_unless_values_unique(enum_member_to_item_text)

        # Enumeration constraining this simulation configuration alias.
        enum_type = self._sim_conf_alias.data_desc.expr_alias_cls

        # If the number of members in this enumeration differs from the number
        # of members mapped by this dictionary, raise an exception.
        if len(enum_type) != len(enum_member_to_item_text):
            raise BetseePySideComboBoxException(QCoreApplication.translate(
                'QBetseeSimConfEnumComboBox',
                'Number of enumeration members {0} differs from '
                'number of mapped enumeration members {1}.'.format(
                    len(enum_type), len(enum_member_to_item_text))))

        # Sequence of the human-readable text of all combo box items.
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

        # Sequence mapping from combo box item indices to enumeration members.
        self._item_index_to_enum_member = tuple(enum_member_to_item_text.keys())

        # Dictionary mapping from enumeration members to combo box item indices.
        self._enum_member_to_item_index = iterables.invert_iterable_unique(
            self._item_index_to_enum_member)

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfComboBox', 'changes to a combo box')


    @property
    def _finalize_widget_change_signal(self) -> Signal:
        return self.currentIndexChanged


    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:

        # Enumeration types are subclasses of this superclass and instances of
        # the "EnumType" type. Since the superclass
        # _die_if_sim_conf_alias_type_invalid() method validates types with
        # issubclass() rather than isinstance(), the former type is returned.
        return EnumClassType

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

        # "Reset" the combo box by arbitrarily selecting its first item. Note
        # this is distinct from the clear() method defined by our superclass,
        # removing all existing items from this combo box. Calling that method
        # would be highly undesirable here.
        self.widget_value = 0


    def _get_alias_from_widget_value(self) -> object:

        # 0-based index of the current combo box item.
        item_index = self.widget_value

        # If this index exceeds the length of the internal sequence mapping from
        # such indices, raise an exception. While this should *NEVER* be the
        # case, explicit sanity validation is the stuff of legend.
        if item_index >= len(self._item_index_to_enum_member):
            raise BetseePySideComboBoxException(QCoreApplication.translate(
                'QBetseeSimConfEnumComboBox',
                'Item index {0} invalid '
                '(i.e., not in the range [0, {1}]).'.format(
                    item_index, len(self._item_index_to_enum_member) - 1)))

        # Return the enumeration member corresponding to this item.
        return self._item_index_to_enum_member[item_index]


    def _get_widget_from_alias_value(self) -> object:

        # Current value of this simulation configuration alias.
        enum_member = self._sim_conf_alias.get()

        # If this is *NOT* a member of this enumeration, raise an exception.
        # While this should *NEVER* be the case, should should never be a word.
        if enum_member not in self._enum_member_to_item_index:
            raise BetseePySideComboBoxException(QCoreApplication.translate(
                'QBetseeSimConfEnumComboBox',
                'Enumeration member "{0}" unrecognized.'.format(
                    str(enum_member))))

        # Return the 0-based index of the combo box item corresponding to this
        # enumeration member.
        return self._enum_member_to_item_index[enum_member]
