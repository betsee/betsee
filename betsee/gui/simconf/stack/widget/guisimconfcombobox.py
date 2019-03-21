#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QComboBox`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Signal  #, Slot
# from betse.util.io.log import logs
# from betse.util.type.iterable import iterables
from betse.util.type.types import type_check  #, EnumClassType
# from betsee.guiexception import BetseePySideComboBoxException
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditenum import (
    QBetseeSimConfEditEnumWidgetMixin)
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)
from betsee.util.widget.stock.guicombobox import QBetseeComboBox
from collections import OrderedDict

# ....................{ SUBCLASSES ~ sequence             }....................
class QBetseeSimConfComboBoxABC(
    QBetseeSimConfEditScalarWidgetMixin, QBetseeComboBox):
    '''
    Abstract base class of all **simulation configuration combo box widget**
    (i.e., :class:`QComboBox` widget transparently mapping from arbitrary
    objects defined by the currently open simulation configuration file to
    human-readable items of this combo box) subclasses.
    '''

    # ..................{ MIXIN ~ property : read-only      }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfComboBoxEnum', 'changes to a combo box')


    @property
    def _finalize_widget_change_signal(self) -> Signal:
        return self.currentIndexChanged

    # ..................{ MIXIN ~ property : value          }..................
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

# ....................{ SUBCLASSES ~ sequence             }....................
#FIXME: Implement this subclass. See the "QBetseeSimConfEditEnumWidgetMixin"
#superclass for relevant inspiration. We'll probably want to implement a
#similar approach, including:
#
#* A new "_item_text_to_widget_value" dictionary.
#* A new "_widget_value_to_item_text" *LIST*. Note the "*LIST*" here and that
#  this is *NOT* strictly required, as the same mapping is trivially defined by
#  the QComboBox.itemText() method.
class QBetseeSimConfComboBoxSequence(QBetseeSimConfComboBoxABC):
    '''
    **Simulation configuration combo box widget** (i.e., :class:`QComboBox`
    widget transparently mapping to human-readable items of this combo box from
    strings defined by the currently open simulation configuration file
    residing in a sequence of all possible such strings).
    '''

    pass

# ....................{ SUBCLASSES ~ enum                 }....................
class QBetseeSimConfComboBoxEnum(
    QBetseeSimConfEditEnumWidgetMixin, QBetseeSimConfComboBoxABC):
    '''
    **Simulation configuration enumeration-backed combo box widget** (i.e.,
    :class:`QComboBox` widget transparently mapping to human-readable items of
    this combo box from enumeration members defined by the currently open
    simulation configuration file).
    '''

    # ..................{ INITIALIZERS                      }..................
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
            The dictionary ordering of these enumeration members exactly
            defines the order in which the corresponding combo box items are
            listed.

        All remaining parameters are passed as is to the superclass method.

        Raises
        ----------
        BetseMappingException
            If this dictionary is *not* safely invertible (i.e., if any value
            of this dictionary is non-uniquely assigned to two or more keys).
        BetseePySideComboBoxException
            If the number of members in this enumeration differs from the
            number of members mapped by (i.e., of keys in) this dictionary.
        '''

        # Dictionary mapping from each enumeration member to the corresponding
        # mutually exclusive value displayed by this widget -- which, in this
        # case, is the 0-based index of that combo box item.
        enum_member_to_widget_value = {
            enum_member: item_index
            for item_index, enum_member in enumerate(
                enum_member_to_item_text.keys())
        }

        # Sequence of the human-readable text of all combo box items.
        #
        # Ideally, any view of ordered dictionary values would be a valid
        # sequence implementing the "collections.abc.Sequence" interface.
        # Inexplicably, this is *NOT* the case. Since the subsequently called
        # QBetseeComboBox.add_items_iconless() method requires a valid
        # sequence, we have no choice but to force this to be the case.
        items_text = tuple(enum_member_to_item_text.values())

        # Finalize the initialization of all superclasses of this subclass.
        super().init(
            *args,
            enum_member_to_widget_value=enum_member_to_widget_value,
            items_iconless_text=items_text,
            **kwargs)
