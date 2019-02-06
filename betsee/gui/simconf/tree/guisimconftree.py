#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based tree widget exposing all high-level features of a
simulation configuration.
'''

#FIXME: Generalize the "QBetseeSimConfTreeWidget" subclass defined below to
#elegantly allow this subclass to contextually enable and disable the
#"action_sim_conf_tree_item_append" and "action_sim_conf_tree_item_remove"
#toolbar actions associated with this tree as follows:
#
#* Define a QBetseeTreeWidget.get_child_item() method returning the child tree
#  item with the passed parent tree item whose text in the first column matches
#  that of the passed string. This method should have signature resembling:
#      @type_check
#      def get_child_item(
#          self, parent_item: QTreeWidgetItem, child_text: str) -> QTreeWidgetItem:
#  Naturally, a human-readable exception should be raised if this parent
#  contains no such child.
#* Define the "_tree_list_items" set. At the moment, this set should *ONLY*
#  contain the tree item corresponding to the "Space/Tissue" tree item. Sadly,
#  obtaining nested items by the text contained in their first column (i.e.,
#  "Tissue", here) is rather fugly. While we could brute-force this query, it
#  might be preferable to create and call a new
#  QBetseeTreeWidget.get_item_from_text_path() method automating such querying
#  with signature resembling:
#      @type_check
#      def get_item_from_text_path(self, *text_path: str) -> QTreeWidgetItem:
#  In this case, that method would be called like so:
#      self._tree_list_items = {self.get_item_from_text_path('Space', 'Tissue')}
#  Sweet, right? That said, defining get_item_from_text_path() will probably
#  prove non-trivial. The body of that method will probably need to iteratively
#  (i.e., *NOT* recursively, which would probably be extreme overkill here and
#  invite stack exhaustion issues) call the self.get_child_item() method with a
#  "parent_item" parameter starting at the root item (i.e.,
#  self.invisibleRootItem()). Something resembling:
#
#      if not text_path:
#          raise SomeExceptionHere()
#
#      parent_item = self.invisibleRootItem()
#
#      for child_item_text in text_path:
#          parent_item = self.get_child_item(
#             parent_item=parent_item, child_text=child_item_text)
#
#      return parent_item
#
#  Surprisingly trivial, given the get_child_item() method.
#* Declare a new select_tree_item() slot resembling the existing
#  QBetseeSimConfStackedWidget.switch_page_to_tree_item() slot but residing
#  inside this subclass instead.
#* Connect the select_tree_item() slot to the "self.currentItemChanged" signal
#  in the _init_connections() method.
#* Define the the select_tree_item() slot as follows:
#  * Toggle the "action_sim_conf_tree_item_append" action as follows:
#    * If the passed "tree_item_curr" is in the "self._tree_list_items" set:
#      * Enable the "action_sim_conf_tree_item_append" action.
#    * Else:
#      * Disable the "action_sim_conf_tree_item_append" action.
#  * Toggle the "action_sim_conf_tree_item_remove" action as follows:
#    * If the passed "tree_item_curr" is the child of an item in the
#      "self._tree_list_items" set:
#      * Enable the "action_sim_conf_tree_item_remove" action.
#    * Else:
#      * Disable the "action_sim_conf_tree_item_remove" action.
#  Note that detecting whether the passed "tree_item_curr" is the child of an
#  item in the "self._tree_list_items" set should simply be implemented via a
#  brute-force search, for now. Efficiently implementing that search would
#  require maintaining a separate "self._tree_list_child_items" set. Well, we
#  suppose that wouldn't be terribly arduous, actually. Doing so would obviate
#  the need for brute-force searching, which would probably simplify the
#  resulting logic if anything. Very well: "self._tree_list_child_items" it is!
#* Given the above, consider renaming these sets for disambiguity:
#  * From "_tree_list_items" to "_items_list_root".
#  * From "_tree_list_child_items" to "_items_list_leaf".

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication  #, Slot
from PySide2.QtWidgets import QMainWindow
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.stock.tree import guitreeitem
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

    Attributes
    ----------
    _items_list_root : set
        Set of all tree items masquerading as **dynamic lists** (i.e., abstract
        containers enabling users to interactively add new *and* remove
        existing child tree items the :attr:`_items_list_leaf` set at runtime).
    _items_list_leaf : set
        Set of all tree items masquerading as **dynamic list items** (i.e.,
        child tree items that may be interactively added *and* removed at
        runtime from the parent tree items of the :attr:`_items_list_root`
        set).
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all instance variables for safety.
        self._items_list_root = None
        self._items_list_leaf = None


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

        # Sequence of all placeholder top-level placeholder items (i.e., items
        # whose corresponding stacked page has yet to be implemented) removed.
        # While extraneous, these items reside in the corresponding "betsee.ui"
        # file as a visual aid to streamline this transitional design phase.
        items_top_todo = []

        # For each top-level item of this tree widget...
        for item_top in self.iter_items_top():
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
            if items_top_todo or item_top.text(0) == '--[TODO]--':
                items_top_todo.append(item_top)

        # Remove these items *AFTER* finding these items. While removing these
        # items during the above iteration would be preferable, doing so would
        # invite iteration desynchronization issues. Be safe... not sorry.
        for item_top_todo in items_top_todo:
            # Log this removal.
            logs.log_debug(
                'Removing top-level placeholder tree widget item "%s"...',
                item_top_todo.text(0))

            # Remove this item. Ideally, we would call the
            # guitreewdg.remove_item() function here. Sadly, that function
            # requires "shiboken2" functionality unavailable under non-standard
            # (but common) PySide2 installations.
            self.takeTopLevelItem(self.indexOfTopLevelItem(item_top_todo))

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

        # When an item of this tree widget is clicked, switch to the associated
        # page of this simulation configuration stack widget (if any).
        self.currentItemChanged.connect(
            main_window.sim_conf_stack.switch_page_to_tree_item)

        # First item of this tree widget.
        tree_item_first = self.topLevelItem(0)

        # Select this item *AFTER* connecting all relevant signals and slots,
        # ensuring that the corresponding slot is called.
        self.setCurrentItem(tree_item_first)
