#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QComboBox`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Signal  #, Slot
from betse.util.io.log import logs
from betse.util.type.types import (
    type_check, ClassOrNoneTypes, SequenceTypes)
from betsee.guiexception import BetseePySideComboBoxException
from betsee.gui.simconf.stack.widget.mixin.guisimconfwdgeditenum import (
    QBetseeSimConfEditEnumWidgetMixin)
from betsee.gui.simconf.stack.widget.mixin.guisimconfwdgeditscalar import (
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
class QBetseeSimConfComboBoxSequence(QBetseeSimConfComboBoxABC):
    '''
    **Simulation configuration combo box widget** (i.e., :class:`QComboBox`
    widget transparently mapping from a sequence of all possible strings
    constraining exactly one setting of the current simulation configuration
    file to human-readable items of this combo box).

    Attributes
    ----------
    _item_index_min : int
        0-based index of the last combo box item at initialization time (i.e.,
        the time of the :meth:`_init_safe` call) with respect to negative indexing.
    _item_index_max : int
        0-based index of the last combo box item at initialization time (i.e.,
        the time of the :meth:`_init_safe` call) with respect to positive indexing.
    _item_text_to_index : MappingType
        Dictionary mapping from the text to 0-based index of each combo box
        item at initialization time (i.e., the time of the :meth:`_init_safe` call).
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._item_index_min = None
        self._item_index_max = None
        self._item_text_to_index = None

    # ..................{ SUPERCLASS                        }..................
    def addItems(self, items_text: SequenceTypes) -> None:
        '''
        Add **icon-less items** (i.e., plaintext combo box items with *no*
        corresponding icons) specified by the passed human-readable strings to
        this combo box after the index of this combo box defined by the
        :meth:`insertPolicy` property, defaulting to appending these items
        *after* any existing items of this combo box.

        Specifically, for each element of this sequence, this method adds a new
        combo box item whose human-readable text is that element.

        Parameters
        ----------
        items_text : SequenceTypes
            Sequence of the text of each item to be added to this combo box.

        Raises
        ----------
        BetseMappingException
            If this dictionary is *not* safely invertible (i.e., if any value
            of this dictionary is non-uniquely assigned to two or more keys).
        BetseePySideRadioButtonException
            If the number of members in this enumeration differs from the
            number of members mapped by (i.e., of keys in) this dictionary.
        '''

        # Defer to the superclass implementation first.
        super().addItems(items_text)

        # Log this initialization.
        logs.log_debug(
            'Populating sequential combo box "%s"...', self.obj_name)

        # Range of 0-based indices accepted by this combo box.
        self._item_index_min = -len(items_text)
        self._item_index_max =  len(items_text) - 1

        # Dictionary mapping from the text to 0-based index of each such item.
        self._item_text_to_index = {
            item_text: item_index
            for item_index, item_text in enumerate(items_text)
        }

    # ..................{ PROPERTIES                        }..................
    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:
        return str

    # ..................{ GETTERS                           }..................
    def _get_alias_from_widget_value(self) -> object:

        # If this combo box has yet to be prepopulated, raise an exception.
        self._die_unless_items_added()

        # 0-based index of the currently displayed item of this combo box.
        item_index = self.widget_value

        # If this index does *NOT* index the "items_iconless_text" sequence
        # previously passed to the _init_safe() method, raise an exception.
        #
        # This unlikely edge case can occur when external callers
        # programmatically modify the content or composition of combo box items
        # after the _init_safe() method has been called.
        if not (self._item_index_min <= item_index <= self._item_index_max):
            raise BetseePySideComboBoxException(QCoreApplication.translate(
                'QBetseeSimConfComboBoxSequence',
                'Combo box item index "{0}" invalid '
                '(i.e., not in [{1}, {2}]).'.format(
                    item_index, self._item_index_min, self._item_index_max)))

        # Return the human-readable text of this item. Since this method did
        # *NOT* raise an exception, this is guaranteed to be a valid value for
        # this simulation configuration alias.
        return self.itemText(item_index)


    def _get_widget_from_alias_value(self) -> object:

        # If this combo box has yet to be prepopulated, raise an exception.
        self._die_unless_items_added()

        # Current value of this simulation configuration alias. If this method
        # does *NOT* subsequnetly raise an exception, this is guaranteed to be
        # the human-readable text of the current combo box item.
        item_text = self._sim_conf_alias.get()

        # If this is *NOT* the text of any combo box item, raise an exception.
        #
        # This unlikely edge case can occur when external callers
        # programmatically modify the content or composition of combo box items
        # after the _init_safe() method has been called.
        if item_text not in self._item_text_to_index:
            raise BetseePySideComboBoxException(QCoreApplication.translate(
                'QBetseeSimConfComboBoxSequence',
                'Combo box item text "{0}" unrecognized.'.format(item_text)))

        # Return the 0-based index of this item in this combo box.
        return self._item_text_to_index[item_text]

# ....................{ SUBCLASSES ~ enum                 }....................
class QBetseeSimConfComboBoxEnum(
    QBetseeSimConfEditEnumWidgetMixin, QBetseeSimConfComboBoxABC):
    '''
    **Simulation configuration enumeration-backed combo box widget** (i.e.,
    :class:`QComboBox` widget transparently mapping from enumeration members
    defined by the current simulation configuration file to human-readable
    items of this combo box).
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def _init_safe(
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

        # Log this initialization.
        logs.log_debug(
            'Initializing enumerated combo box "%s"...', self.obj_name)

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
        super()._init_safe(
            *args,
            enum_member_to_widget_value=enum_member_to_widget_value,
            items_iconless_text=items_text,
            **kwargs)
