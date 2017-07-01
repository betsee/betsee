#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-specific string facilities.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot
from PySide2.QtWidgets import (
    QMainWindow, QTreeWidget, QTreeWidgetItem)
from betse.util.type.types import type_check

# ....................{ CLASSES                            }....................
class QBetseeSimConfTreeWidget(QTreeWidget):
    '''
    :mod:`PySide2`-based tree widget exposing all high-level features of the
    current simulation configuration.

    This application-specific widget augments the stock :class:`QTreeWidget`
    with support for handling simulation configurations, including:

    * Integration with the corresponding :class:`QStackWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    Attributes
    ----------
    _sim_conf_stack : QStackWidget
        Simulation configuration stack widget associated with this tree widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.widget.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Initialize this tree widget against the passed parent main window.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Classify all widgets internally accessed by slots connected to below
        # *BEFORE* connecting these slots.
        self._sim_conf_stack = main_window.sim_conf_stack

        # When an item of this tree widget is clicked, switch to the associated
        # page of the simulation configuration stack widget (if any).
        self.itemClicked.connect(self._switch_sim_conf_stack_page)

    # ..................{ SLOTS                              }..................
    #FIXME: To dramatically simplify the implementation of this slot, the names
    #of all simulation configuration tree widget items and simulation
    #configuration stack widget pages must be synchronized in a one-to-one
    #manner. For example, the names corresponding to the "File Management"
    #configuration setting might resemble:
    #
    #* "sim_conf_tree_item_paths".
    #* "sim_conf_stack_page_paths".
    #
    #Given such synchronization:
    #
    #* A new "_sim_conf_tree_item_to_stack_page" dictionary attribute should be
    #  initialized by this widget's __init__() method to the empty dictionary.
    #* This widget's init() method should then define this dictionary by:
    #  * Dynamically retrieving all instance variables of the passed
    #    "main_window" widget whose names are prefixed by "sim_conf_tree_item_".
    #  * Dynamically retrieving all instance variables of the passed
    #    "main_window" widget whose names are prefixed by
    #    "sim_conf_stack_page_".
    #  * Note that, due to the presence of ignorable placeholder pages, an
    #    exception should be raised only if the lengths of the former list is
    #    less than that of the latter list.
    #  * For each "sim_conf_tree_item_"-prefixed variable:
    #    * Obtain the corresponding "sim_conf_stack_page_"-prefixed variable.
    #    * Map the former to the latter via this dictionary.
    #
    #This assumes, of course, that widgets are hashable by Python. They should
    #be, but you know what assumptions invariably make out of us. In any event,
    #given this dictionary, this slot's implementation then trivially reduces
    #to:
    #
    #    sim_conf_stack_page = _sim_conf_tree_item_to_stack_page.get(
    #        tree_time, None)
    #
    #    if sim_conf_stack_page is None:
    #        return
    #
    #    self._sim_conf_stack.setCurrentWidget(sim_conf_stack_page)
    #
    #Pretty sweet, no? We say, "Yes!"

    @Slot(QTreeWidgetItem, int)
    def _switch_sim_conf_stack_page(
        self, tree_item: QTreeWidgetItem, tree_item_column: int) -> None:
        '''
        Switch to the simulation configuration stack widget page associated with
        the passed tree widget item clicked by the end user.

        Parameters
        ----------
        tree_item : QTreeWidgetItem
            Current tree widget item clicked by the end user.
        tree_item_column : int
            Column of this item clicked by the end user.
        '''

        pass
