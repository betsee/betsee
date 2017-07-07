#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based tree widget exposing all high-level features of the
current simulation configuration.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Slot
from PySide2.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.type import strs
from betse.util.type.obj import objects
from betse.util.type.types import type_check
from betsee.exceptions import BetseePySideTreeWidgetException

# ....................{ CLASSES                            }....................
class QBetseeSimConfTreeWidget(QTreeWidget):
    '''
    :mod:`PySide2`-based tree widget exposing all high-level features of the
    current simulation configuration.

    This application-specific widget augments the stock :class:`QTreeWidget`
    with support for handling simulation configurations, including:

    * Integration with the corresponding :class:`QStackedWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    Attributes
    ----------
    _item_to_sim_conf_stack_page : dict
        Dictionary mapping from each :class:`QTreeWidgetItem` in this tree
        widget to each page widget in the :class:`QStackedWidget` associated
        with this tree widget. This dictionary is principally used to ensure
        that clicking on each :class:`QTreeWidgetItem` displays the
        corresponding page widget.
    _sim_conf_stack : QStackedWidget
        Simulation configuration stack widget associated with this tree widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Initialize all instance variables for safety.
        self._item_to_sim_conf_stack_page = {}


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

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window may
        be retained, however.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Log this initialization.
        logs.log_debug('Integrating top-level tree and stack widgets...')

        # Integrate this tree widget with this window's top-level stack widget.
        self._init_sim_conf_stack(main_window)

        # Connect all relevant signals and slots of this tree and stack widget
        # *AFTER* integrating these widgets, as required by these slots.
        self._init_connections()


    @type_check
    def _init_sim_conf_stack(self, main_window: QMainWindow) -> None:
        '''
        Integrate this tree widget with the top-level :class:`QStackedWidget`
        contained in the passed parent main window.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Set of the text of each tree widget item for which no corresponding
        # stack widget page exists (e.g., due to this item acting as a
        # placeholder signifying a dynamically created list of child items).
        ITEMS_IGNORED_TEXT = {
            'Networks',  # Dynamically created list of child network items.
        }

        # Substring prefixing the names of all pages of this stack widget.
        SIM_CONF_STACK_PAGE_NAME_PREFIX = 'sim_conf_stack_page_'

        # Classify all widgets internally accessed by slots connected to below
        # *BEFORE* connecting these slots.
        self._sim_conf_stack = main_window.sim_conf_stack

        # Generator yielding 2-tuples of the name and value of each page of this
        # stack widget parsed as all instance variables of this main window
        # whose names are prefixed by a uniquely identifying string.
        sim_conf_stack_pages = objects.iter_vars_custom_simple_matching(
            obj=main_window, predicate=lambda var_name, var_value: (
                var_name.startswith(SIM_CONF_STACK_PAGE_NAME_PREFIX)))

        # Dictionary mapping the name to value of each such stack widget page,
        # permitting the iteration below to efficiently look such values up.
        sim_conf_stack_page_name_to_value = {
            sim_conf_stack_page_name: sim_conf_stack_page
            for sim_conf_stack_page_name, sim_conf_stack_page in (
                sim_conf_stack_pages)
        }

        #FIXME: Generalize to support arbitrarily nested tree widget items,
        #ideally via simple recursion. To do so, note the existing
        #QTreeWidgetItem::childCount() and QTreeWidgetItem::child() methods,
        #which such recursion will necessarily call to iterate over child items.

        # For the 0-based index of each top-level item of this tree widget...
        #
        # Note that we intentionally iterate by tree widget items rather than
        # stack widget pages here. Why? Because iterating instead by the latter
        # would erroneously handle stack widget pages with no corresponding
        # tree widget items, which currently exist (e.g., for temporary
        # scratchpad purposes *NOT* intended to be displayed to end users).
        # for sim_conf_tree_item_name, sim_conf_tree_item in sim_conf_tree_items:
        for top_item_index in range(self.topLevelItemCount()):
            # Current top-level item of this tree widget.
            top_item = self.topLevelItem(top_item_index)

            # Text of this item in the first column.
            top_item_text = top_item.text(0)

            # If this text suggests this item to be ignorable, do so.
            if top_item_text in ITEMS_IGNORED_TEXT:
                continue

            # Name of the corresponding stack widget page, synthesized from the
            # text of this tree widget item with all whitespace stripped. For
            # example, the tree widget item with text "File Management"
            # corresponds to the stack widget page with name
            # 'sim_conf_stack_page_FileManagement'.
            sim_conf_stack_page_name = (
                SIM_CONF_STACK_PAGE_NAME_PREFIX +
                strs.remove_whitespace(top_item_text)
            )

            # Stack widget page associated with this tree widget item if any or
            # "None" otherwise.
            sim_conf_stack_page = sim_conf_stack_page_name_to_value.get(
                sim_conf_stack_page_name, None)

            # If no such page exists, raise an exception.
            if sim_conf_stack_page is None:
                raise BetseePySideTreeWidgetException(
                    title=QCoreApplication.translate(
                       'QBetseeSimConfTreeWidget', 'Stacked Page not Found'),
                    synopsis=QCoreApplication.translate(
                        'QBetseeSimConfTreeWidget',
                        'Simulation configuration stacked page '
                        '"{0}" not found.'.format(sim_conf_stack_page_name)))

            # Map this tree widget item to this stack widget page.
            self._item_to_sim_conf_stack_page[top_item] = sim_conf_stack_page


    def _init_connections(self) -> None:
        '''
        Connect all relevant signals and slots of this tree widget and the
        corresponding simulation configuration stack widget.
        '''

        # When an item of this tree widget is clicked, switch to the associated
        # page of this simulation configuration stack widget (if any).
        self.currentItemChanged.connect(self._switch_sim_conf_stack_page)

        # First item of this tree widget.
        tree_item_first = self.topLevelItem(0)

        # Select this item *AFTER* connecting all relevant signals and slots,
        # ensuring that the corresponding slot is called.
        self.setCurrentItem(tree_item_first)

    # ..................{ SLOTS                              }..................
    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _switch_sim_conf_stack_page(
        self,
        tree_item_curr: QTreeWidgetItem,
        tree_item_prev: QTreeWidgetItem
    ) -> None:
        '''
        Switch to the simulation configuration stack widget page associated with
        the passed tree widget item clicked by the end user.

        Parameters
        ----------
        tree_item_curr : QTreeWidgetItem
            Current tree widget item clicked by the end user.
        tree_item_prev : QTreeWidgetItem
            Previous tree widget item clicked by the end user.
        '''

        # Stack widget page associated with this tree widget item if any or
        # "None" otherwise.
        sim_conf_stack_page = self._item_to_sim_conf_stack_page.get(
            tree_item_curr, None)

        # If no such page exists (e.g., due to this tree widget item being a
        # placeholder container for child items for which pages do exist),
        # silently ignore this item.
        if sim_conf_stack_page is None:
            return

        # Else, display this page.
        self._sim_conf_stack.setCurrentWidget(sim_conf_stack_page)
