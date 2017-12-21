#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:class:`QRadioButton`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Qt, Signal
from PySide2.QtWidgets import QButtonGroup, QRadioButton
from betse.util.io.log import logs
from betse.util.type import iterables
from betse.util.type.mapping import maputil
from betse.util.type.obj import objects
from betse.util.type.types import type_check, ClassOrNoneTypes, MappingType
from betsee.guiexceptions import BetseePySideRadioButtonException
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgeditscalar import (
    QBetseeSimConfEditEnumWidgetMixin)
from betsee.util.widget.abc.guiclipboardabc import (
    QBetseeClipboardScalarWidgetMixin)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfEnumRadioButtonGroup(
    QBetseeSimConfEditEnumWidgetMixin, QButtonGroup):
    '''
    Simulation configuration-specific radio button group widget, permitting
    high-level enumeration members backed by low-level raw strings in external
    simulation configuration files to be interactively edited.

    Attributes
    ----------
    _enum_member_to_radio_btn : MappingType
        Dictionary mapping from each radio button of this group to the
        corresponding member of the enumeration constraining this group.
    _radio_btn_to_enum_member : MappingType
        Dictionary mapping from each member of the enumeration constraining this
        group to the corresponding radio button of this group.

    See Also
    ----------
    :class:`QBetseeSimConfComboBox`
        Alternative simulation configuration-specific widget subclass similarly
        permitting high-level enumeration members to be interactively edited.
        While more cumbersome to initialize, that subclass is preferable from
        the user experience (UX) perspective for sufficiently large enumerations
        (e.g., containing ten or more members).
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._enum_member_to_radio_btn = None
        self._radio_btn_to_enum_member = None


    @type_check
    def init(
        self, enum_member_to_radio_btn: MappingType, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this widget.

        Parameters
        ----------
        enum_member_to_radio_btn : MappingType
            Dictionary mapping from each member of the enumeration encapsulated
            by the passed ``sim_conf_alias`` parameter to the radio button to be
            associated with that member.

        All remaining parameters are passed as is to the superclass method.

        Raises
        ----------
        BetseMappingException
            If this dictionary is *not* safely invertible (i.e., if any value of
            this dictionary is non-uniquely assigned to two or more keys).
        BetseePySideRadioButtonException
            If the number of members in this enumeration differs from the number
            of members mapped by (i.e., of keys in) this dictionary.
        '''

        # Initialize our superclass with all remaining parameters.
        super().init(*args, **kwargs)

        # If this dictionary duplicates any radio buttons, raise an exception.
        maputil.die_unless_values_unique(enum_member_to_radio_btn)

        # Classify this dictionary.
        self._enum_member_to_radio_btn = enum_member_to_radio_btn

        # Dictionary mapping from enumeration members to radio button indices.
        self._radio_btn_to_enum_member = iterables.invert_iterable_unique(
            self._item_index_to_enum_member)

        # Enumeration constraining this simulation configuration alias.
        enum_type = self._sim_conf_alias.data_desc.expr_alias_cls

        # If the number of members in this enumeration differs from the number
        # of members mapped by this dictionary, raise an exception.
        if len(enum_type) != len(enum_member_to_radio_btn):
            raise BetseePySideRadioButtonException(QCoreApplication.translate(
                'QBetseeSimConfEnumRadioButtonGroup',
                'Number of enumeration members {0} differs from '
                'number of mapped enumeration members {1}.'.format(
                    len(enum_type), len(enum_member_to_radio_btn))))

        # # Sequence mapping from radio button indices to enumeration members.
        # self._item_index_to_enum_member = tuple(enum_member_to_item_text.keys())
        #
        # # Dictionary mapping from enumeration members to radio button indices.
        # self._enum_member_to_item_index = iterables.invert_iterable_unique(
        #     self._item_index_to_enum_member)

        # For each radio button previously added to this button group...
        for radio_btn in self.buttons():
            # If this button is *NOT* a radio button, raise an exception.
            objects.die_unless_instance(obj=radio_btn, cls=QRadioButton)

            # If this button is *NOT* in this dictionary, raise an exception.
            if radio_btn not in self._radio_btn_to_enum_member:
                raise BetseePySideRadioButtonException(
                    QCoreApplication.translate(
                        'QBetseeSimConfEnumRadioButtonGroup',
                        'Radio button "{0}" not in button group "{1}"'.format(
                            radio_btn.objectName(), self.objectName())))

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:

        return QCoreApplication.translate(
            'QBetseeSimConfEnumRadioButtonGroup', 'changes to a radio button')


    @property
    def _finalize_widget_change_signal(self) -> Signal:

        # Signals defined by the "QRadioButton" class are intentionally ignored.
        # These low-level child widgets should *ONLY* ever be contained in a
        # higher-level "QButtonGroup" parent widget.
        #
        # The low-level QRadioButton.toggled() signal is emitted for the pair of
        # radio buttons in a group being enabled and disabled, thus generating
        # two emissions for each toggling of a radio button. In contrast, the
        # higher-level QButtonGroup.buttonClicked() signal is emitted exactly
        # once for each such toggling.
        #
        # Lastly, despite nomenclature suggesting this signal to apply *ONLY* to
        # interactive clicks, this signal is emitted on both interactive and
        # programmatic clicks *AND* keyboard shortcuts.
        return self.buttonClicked

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> QRadioButton:

        return self.checkedButton()


    @widget_value.setter
    @type_check
    def widget_value(self, widget_value: QRadioButton) -> None:

        # Select this radio button manually. Thanks to the mutual exclusivity of
        # radio buttons, doing so implicitly unselects all other buttons in this
        # group. For unknown reasons, the "QButtonGroup" widget is the only
        # scalar widget to provide no corresponding setCheckedButton() setter.
        widget_value.setChecked(True)


    def _reset_widget_value(self) -> None:

        # Reset this button group by arbitrarily selecting its first button.
        self.widget_value = iterables.get_item_first(self.buttons())


    def _get_alias_from_widget_value(self) -> object:

        # Currently selected radio button.
        radio_btn = self.widget_value

        # If this is *NOT* a previously registered button, raise an exception.
        # While this should *NEVER* be the case, should should never be a word.
        if radio_btn not in self._radio_btn_to_enum_member:
            raise BetseePySideRadioButtonException(QCoreApplication.translate(
                'QBetseeSimConfEnumRadioButtonGroup',
                'Radio button "{0}" unrecognized.'.format(
                    radio_btn.objectName())))

        # Return the enumeration member corresponding to this button.
        return self._radio_btn_to_enum_member[radio_btn]


    def _get_widget_from_alias_value(self) -> QRadioButton:

        # Current value of this simulation configuration alias.
        enum_member = self._sim_conf_alias.get()

        # If this is *NOT* a member of this enumeration, raise an exception.
        # While this should *NEVER* be the case, should should never be a word.
        if enum_member not in self._enum_member_to_radio_btn:
            raise BetseePySideRadioButtonException(QCoreApplication.translate(
                'QBetseeSimConfEnumRadioButtonGroup',
                'Enumeration member "{0}" unrecognized.'.format(
                    str(enum_member))))

        # Return the radio button corresponding to this member.
        return self._enum_member_to_radio_btn[enum_member]
