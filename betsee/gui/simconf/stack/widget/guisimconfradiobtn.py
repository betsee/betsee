#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QRadioButton`-based simulation configuration widget subclasses.
'''

#FIXME: Submit an upstream issue requesting that:
#
#* "QButtonGroup" widgets be promotable from within Qt (Creator|Designer).
#* "QButtonGroup" widgets be treated as customary widgets accessible from the
#  widgets toolkit pane (presumably filtered into the "Containers" section).
#  Doing so addresses existing UX concerns on how "QButtonGroup" widgets are
#  currently exposed to end users from within Qt (Creator|Designer) *AND*
#  presumably automatically resolves the prior concern of promotability.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal
from PySide2.QtWidgets import QButtonGroup, QRadioButton
# from betse.util.io.log import logs
from betse.util.type import iterables
from betse.util.type.obj import objects
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideRadioButtonException
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditenum import (
    QBetseeSimConfEditEnumWidgetMixin)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfEnumRadioButtonGroup(
    QBetseeSimConfEditEnumWidgetMixin, QButtonGroup):
    '''
    Simulation configuration-specific radio button group widget, permitting
    high-level enumeration members backed by low-level raw strings in external
    simulation configuration files to be interactively edited.

    Caveats
    ----------
    **Qt (Creator|Designer) provides no means of promoting :class:`QButtonGroup`
    widgets to instances of this subclass,** a longstanding deficiency with no
    short-term official solution. Instead, button groups *must* be manually
    "promoted" via the admittedly hackish
    :attr:`betsee.gui.guicache._PROMOTE_OBJ_NAME_TO_TYPE` dictionary.

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
    @type_check
    def init(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(*args, **kwargs)

        # For each radio button previously added to this button group...
        for radio_btn in self.buttons():
            # If this button is *NOT* a radio button, raise an exception.
            objects.die_unless_instance(obj=radio_btn, cls=QRadioButton)

            # If this button is *NOT* mapped to be the dictionary externally
            # passed to this method, raise an exception.
            if radio_btn not in self._widget_value_to_enum_member:
                raise BetseePySideRadioButtonException(
                    QCoreApplication.translate(
                        'QBetseeSimConfEnumRadioButtonGroup',
                        'Button group "{1}" radio button "{0}" not a '
                        'value of "enum_member_to_widget_value".'.format(
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
        # higher-level QButtonGroup.buttonClicked() signal returned here is
        # emitted only once for each such toggling.
        #
        # Lastly, despite nomenclature suggesting this signal to apply *ONLY* to
        # interactive clicks, Qt emits this signal on *ALL* available button
        # interactions (e.g., interactive clicks, programmatic clicks, keyboard
        # shortcut-driven clicks).
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
