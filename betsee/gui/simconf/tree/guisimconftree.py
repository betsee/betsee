#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based tree widget exposing all high-level features of a
simulation configuration.
'''

#FIXME: Prepopulate the "_item_list_root_tissue" parent tree item with child
#tree items whose names are the user-defined names of tissue profiles in the
#current simulation subconfiguration. This implies, naturally, that:
#
#* This parent item should have no child items when no simulation configuration
#  is currently open (e.g., at application startup).
#* When a simulation configuration is opened, this parent should be
#  prepopulated with such children. Doing so will require:
#  * Defining a new set_sim_conf_filenam() slot of this tree. See the
#    comparable main_window.set_sim_conf_filenam() slot for... pasting. The
#    body of this slot should iterate over the
#    "main_window.sim_conf.p.tissue_profiles" list, converting each such list
#    item into a comparable child tree item of this parent tree item.
#  * Connecting the "main_window.sim_conf.set_filename_signal" to this slot in
#    the _init_connections() method of this tree.
#
#Fairly trivial, thankfully. Let us accomplish greatness together.

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import Slot  # QCoreApplication,
from PySide2.QtWidgets import QMainWindow, QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.type.types import type_check
# from betsee.util.widget.stock.tree import guitreeitem
from betsee.util.widget.stock.tree.guitreewdg import QBetseeTreeWidget

# ....................{ CLASSES                           }....................
class QBetseeSimConfTreeWidget(QBetseeTreeWidget):
    '''
    :mod:`PySide2`-based tree widget exposing all high-level features of the
    current simulation configuration.

    This application-specific widget augments the stock :class:`QTreeWidget`
    with support for handling simulation configurations, including:

    * Auto-axpansion of all tree items by default.
    * Integration with the corresponding :class:`QStackedWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    Attributes (Private: Items)
    ----------
    _items_list_leaf : set
        Set of all tree items masquerading as **dynamic list items** (i.e.,
        child tree items that may be interactively added *and* removed at
        runtime from the parent tree items of the :attr:`_items_list_root`
        set).
    _items_list_root : set
        Set of all tree items masquerading as **dynamic lists** (i.e., abstract
        containers enabling users to interactively add new *and* remove
        existing child tree items the :attr:`_items_list_leaf` set at runtime).
    _item_list_root_tissue : QTreeWidgetItem
        Tree item masquerading as a dynamic list of **tissue profiles** (i.e.,
        simulation subconfigurations assigning a subset of the cell cluster the
        same user-defined initial conditions).

    Attributes (Private: Widgets)
    ----------
    _action_sim_conf_tree_item_append : QAction
        Alias of the
        :attr:`QBetseeMainWindow._action_sim_conf_tree_item_append` action.
    _action_sim_conf_tree_item_remove : QAction
        Alias of the
        :attr:`QBetseeMainWindow._action_sim_conf_tree_item_remove` action.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Initialize all instance variables to sane defaults.
        self._items_list_leaf = set()
        self._items_list_root = set()
        self._item_list_root_tissue = None
        self._action_sim_conf_tree_item_append = None
        self._action_sim_conf_tree_item_remove = None


    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.window.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Initialize this tree widget against the passed parent main window.

        This method is principally intended to perform **post-population
        initialization** (i.e., initialization performed *after* this widget
        has been completely pre-populated with all initial tree items).

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window
        may be retained, however.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Initialize our superclass.
        super().init()

        # Log this initialization.
        logs.log_debug('Initializing top-level tree widget...')

        # Define the set of all tree items masquerading as dynamic lists. Since
        # this tree is empty at __init__() time, this definition is necessarily
        # deferred until init() time.
        self._item_list_root_tissue = self.get_item_from_text_path(
            'Space', 'Tissue')
        self._items_list_root.add(self._item_list_root_tissue)

        # Initialize all widgets pertaining to the state of this simulation
        # configuration *BEFORE* connecting all relevant signals and slots
        # typically expecting these widgets to be initialized.
        self._init_widgets(main_window)
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QMainWindow) -> None:
        '''
        Create all widgets owned directly by this tree widget *and* initialize
        all other widgets (not necessarily owned by this tree widget) whose
        internal state pertains to the high-level state of this tree widget.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Classify all instance variables of this main window subsequently
        # required by this object.
        self._action_sim_conf_tree_item_append = (
            main_window.action_sim_conf_tree_item_append)
        self._action_sim_conf_tree_item_remove = (
            main_window.action_sim_conf_tree_item_remove)

        # Sequence of all placeholder top-level placeholder items (i.e., items
        # whose corresponding stacked page has yet to be implemented) removed.
        # While extraneous, these items reside in the corresponding "betsee.ui"
        # file as a visual aid to streamline this transitional design phase.
        top_items_todo = []

        # For each top-level item of this tree widget...
        for top_item in self.iter_top_items():
            # If either:
            #
            # * One or more top-level placeholder items have been previously
            #   visited by this iteration, *ALL* top-level items from this item
            #   onward may be safely assumed to also be placeholder items.
            # * No top-level placeholder items have been visited yet *AND* this
            #   item's text implies this item to be the first such placeholder.
            #
            # Then this is a top-level placeholder item. In either case, append
            # this item to this sequence.
            if top_items_todo or top_item.text(0) == '--[TODO]--':
                top_items_todo.append(top_item)

        # Remove these items *AFTER* finding these items. While removing these
        # items during the above iteration would be preferable, doing so would
        # invite iteration desynchronization issues. Be safe... not sorry.
        for top_item_todo in top_items_todo:
            # Log this removal.
            logs.log_debug(
                'Removing top-level placeholder tree widget item "%s"...',
                top_item_todo.text(0))

            # Remove this item. Ideally, we would call the
            # guitreewdg.remove_item() function here. Sadly, that function
            # requires "shiboken2" functionality unavailable under non-standard
            # (but common) PySide2 installations.
            self.takeTopLevelItem(self.indexOfTopLevelItem(top_item_todo))

        # Expand all items of this tree widget to arbitrary depth *AFTER*
        # removing extraneous items above.
        self.expandAll()


    def _init_connections(self, main_window: QMainWindow) -> None:
        '''
        Connect all relevant signals and slots of this tree widget and the
        corresponding simulation configuration stack widget.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # When an item of this tree widget is clicked:
        #
        # * Perform simulation-specific logic implemented by this subclass.
        # * Switch to the associated page of this simulation configuration
        #   stack widget (if any).
        self.currentItemChanged.connect(self._select_tree_item)
        self.currentItemChanged.connect(
            main_window.sim_conf_stack.switch_page_to_tree_item)

        # First item of this tree widget.
        tree_item_first = self.topLevelItem(0)

        # Select this item *AFTER* connecting all relevant signals and slots,
        # ensuring that the corresponding slot is called.
        self.setCurrentItem(tree_item_first)

    # ..................{ SLOTS                             }..................
    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _select_tree_item(
        self, item_curr: QTreeWidgetItem, item_prev: QTreeWidgetItem) -> None:
        '''
        Perform simulation-specific logic when the end user clicks the passed
        currently selected tree widget item *after* having clicked the passed
        previously selected tree widget item.

        Specifically, this slot (in arbitrary order):

        * Enables the dynamic list append action (i.e.,
          :attr:`_action_sim_conf_tree_item_append`) *only* if this current
          item is masquerading as a dynamic list.
        * Enables the dynamic list removal action (i.e.,
          :attr:`_action_sim_conf_tree_item_remove`) *only* if this current
          item is masquerading as a dynamic list item.

        Parameters
        ----------
        item_curr : QTreeWidgetItem
            Current tree widget item clicked by the end user.
        item_prev : QTreeWidgetItem
            Previous tree widget item clicked by the end user.
        '''

        # Permit users to append new tree items to the dynamic list rooted at
        # this current tree item only if the latter is a dynamic list.
        self._action_sim_conf_tree_item_append.setEnabled(
            item_curr in self._items_list_root)

        # Permit users to remove this current tree item from its dynamic list
        # rooted at the parent tree item of this item only if the latter is a
        # dynamic list item.
        self._action_sim_conf_tree_item_remove.setEnabled(
            item_curr in self._items_list_leaf)
