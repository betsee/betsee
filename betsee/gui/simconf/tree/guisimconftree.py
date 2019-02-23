#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based tree widget exposing all high-level features of a
simulation configuration.
'''

#FIXME: Unconditionally set a suitable new SVG-based icon on all child tree
#items masquerading as dynamic list items (e.g., custom tissue profiles). A
#simple circular bullet point image might suffice.

#FIXME: Permit the "_action_sim_conf_tree_item_append" and
#"_action_sim_conf_tree_item_remove" operations to be undone. Doing so will
#probably prove non-trivial and has thus been deferred in favour of more
#low-hanging and/or mission-critical fruit.

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Slot
from PySide2.QtWidgets import QMainWindow, QTreeWidgetItem
from betse.lib.yaml.abc.yamllistabc import YamlList  #, YamlListItemNamedABC
from betse.util.io.log import logs
from betse.util.type.obj import objects
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideTreeWidgetException
from betsee.util.widget.stock.tree import guitreeitem
from betsee.util.widget.stock.tree.guitreewdg import QBetseeTreeWidget

# ....................{ SUBCLASSES                        }....................
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

    Attributes (Private)
    ----------
    _p : Parameters
        High-level simulation configuration encapsulating a low-level
        dictionary parsed from an even lower-level YAML-formatted file.

    Attributes (Private: Items: Dictionary)
    ----------
    _item_list_root_to_yaml_list : dict
        Dictionary mapping from each tree item masquerading as a dynamic list
        to the YAML-backed list subconfiguration of the currently open
        simulation configuration underlying that item. For simplicity, this
        dictionary remains defined as is even if no simulation configuration is
        open. See the :attr:`_items_list_root` set for further details.

    Attributes (Private: Items: Set)
    ----------
    _items_list_leaf : set
        Set of all tree items masquerading as **dynamic list items** (i.e.,
        child tree items that may be interactively added to *and* removed from
        the parent tree items of the :attr:`_items_list_root` set at runtime).
    _items_list_root : set
        Set of all tree items masquerading as **dynamic lists** (i.e., abstract
        containers permitting child tree items to be interactively added to
        *and* removed from the :attr:`_items_list_leaf` set at runtime).
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

        # Initialize instance variables with sane defaults.
        #
        # Note that nullifying these variables (i.e., initializing these
        # variables to "None") raises exceptions from slots called early in
        # application startup expecting these variables to be non-"None". This
        # includes the critical _select_tree_item() slot.
        self._item_list_root_to_yaml_list = {}
        self._items_list_leaf = set()
        self._items_list_root = set()

        # Nullify all remaining instance variables for safety.
        self._action_sim_conf_tree_item_append = None
        self._action_sim_conf_tree_item_remove = None
        self._item_list_root_tissue = None
        self._p = None


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

        # Classify all instance variables of this main window subsequently
        # required by this object.
        self._action_sim_conf_tree_item_append = (
            main_window.action_sim_conf_tree_item_append)
        self._action_sim_conf_tree_item_remove = (
            main_window.action_sim_conf_tree_item_remove)
        self._p = main_window.sim_conf.p

        # Define the set of all tree items masquerading as dynamic lists
        # *AFTER* classifying all instance variables of this main window.
        #
        # Note that, as this tree widget is empty at __init__() time, this
        # initialization is necessarily deferred until init() time.
        self._init_items_list_root()

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

        # Connect action signals to corresponding slots on this object.
        self._action_sim_conf_tree_item_append.triggered.connect(
            self._append_tree_item)
        self._action_sim_conf_tree_item_remove.triggered.connect(
            self._remove_tree_item)

        # Connect custom signals to corresponding slots on this object.
        main_window.sim_conf.set_filename_signal.connect(
            self._set_sim_conf_filename)

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

    # ..................{ INITIALIZERS ~ set                }..................
    def _init_items_list_root(self) -> None:
        '''
        Define the set of all tree items masquerading as dynamic lists (i.e.,
        :attr:`_items_list_root`) *and* references to these items (e.g.,
        :attr:`_item_list_root_tissue`).
        '''

        # Preserve references to all tree items masquerading as dynamic lists.
        self._item_list_root_tissue = self.get_item_from_text_path(
            'Space', 'Tissue')

        # Define the set of all such items.
        self._items_list_root = {
            self._item_list_root_tissue,
        }

        # Define the dictionary mapping all such items to YAML-backed lists.
        self._item_list_root_to_yaml_list = {
            self._item_list_root_tissue: self._p.tissue_profiles,
        }

    # ..................{ INITIALIZERS ~ set : leaf         }..................
    def _init_items_list_leaf(self) -> None:
        '''
        Append one child tree item masquerading as a dynamic list item to its
        parent tree item masquerading as a dynamic list for each YAML-backed
        simulation subconfiguration of this newly opened simulation
        configuration file
        '''

        # Log this slot.
        logs.log_debug('Prepopulating dynamic child tree items...')

        # Initialize the set of all such child tree items to the empty set.
        self._items_list_leaf = set()

        # For each tissue profile configured by this configuration, create and
        # append a new child tree item associated with this profile to the
        # existing parent tree item of such items.
        for tissue_profile in self._p.tissue_profiles:
            self._make_item_list_leaf(
                item_list_root=self._item_list_root_tissue,
                item_list_leaf_name=tissue_profile.name,
            )


    def _deinit_items_list_leaf(self) -> None:
        '''
        Remove all child tree items masquerading as dynamic list items.
        '''

        # Log this slot.
        logs.log_debug('Depopulating dynamic child tree items...')

        # Delete all child tree items masquerading as dynamic list items
        # from their parent tree items.
        guitreeitem.delete_child_items(self._item_list_root_tissue)

        # Reduce the set of all such child tree items to the empty set.
        self._items_list_leaf = set()

    # ..................{ MAKERS                            }..................
    @type_check
    def _make_item_list_leaf(
        self,
        item_list_root: QTreeWidgetItem,
        item_list_leaf_name: str,
    ) -> QTreeWidgetItem:
        '''
        Create and append a new child tree item masquerading as a dynamic list
        item to the existing list of child items maintained by the passed
        parent tree item masquerading as a dynamic list, returning this new
        child tree item.

        Parameters
        ----------
        item_list_root : QTreeWidgetItem
            Parent tree item masquerading as a dynamic list to append this new
            child tree item.
        item_list_leaf_name : str
            First-column text of the new child tree item to be created.

        Returns
        ----------
        QTreeWidgetItem
            New child tree item created by this method.

        See Also
        ----------
        :attr:`_items_list_leaf`
            Further details.
        '''

        # New child tree item masquerading as a dynamic list item of this
        # existing parent tree item, implicitly appended by this constructor as
        # the last child of this parent. Thanks, Qt API! You did something.
        item_list_leaf = QTreeWidgetItem(item_list_root)

        # 1-based index of this child item in this parent item's list.
        #
        # Note that, while the item_list_root.indexOfChild(item_list_leaf)
        # method could also be called here, doing so would yield the same
        # result with considerably worse time complexity. Hence, we don't.
        item_list_leaf_index = item_list_root.childCount()

        #FIXME: Ideally, this text would be HTML-formatted for improved
        #legibility: e.g., as '{}. <b>{}</b>' instead. For unknown
        #reasons, however, the Qt API provides no built-in means of
        #formatting items as anything other than plaintext. Note that
        #numerous StackOverflow questions and answers pertaining to
        #this issue exist, but that no simple "silver bullet" appears
        #to exist. PySide2-specific answers include:
        #    https://stackoverflow.com/a/5443112/2809027
        #    https://stackoverflow.com/a/38028318/2809027

        # Human-readable first-column text of this child item.
        item_list_leaf_text = '{}. {}'.format(
            item_list_leaf_index, item_list_leaf_name)

        # Set this child item's first-column text to this text.
        item_list_leaf.setText(0, item_list_leaf_text)

        # Add this child item to the set of all tree items masquerading
        # as dynamic list items *AFTER* successfully making this item.
        self._items_list_leaf.add(item_list_leaf)

        # Return this child item.
        return item_list_leaf

    # ..................{ SLOTS ~ sim conf                  }..................
    @Slot(str)
    def _set_sim_conf_filename(self, sim_conf_filename: str) -> None:
        '''
        Slot signalled on the opening of a new simulation configuration *and*
        closing of an open simulation configuration.

        Parameters
        ----------
        filename : str
            Either:

            * If the user opened a new simulation configuration file, the
              non-empty absolute filename of that file.
            * If the user closed an open simulation configuration file, the
              empty string.
        '''

        # If a simulation configuration is currently open, append one child
        # tree item masquerading as a dynamic list item to its parent tree item
        # masquerading as a dynamic list for each YAML-backed simulation
        # subconfiguration of this newly opened simulation configuration file.
        if sim_conf_filename:
            self._init_items_list_leaf()
        # Else, no simulation configuration is currently open. In this case,
        # remove all child tree items masquerading as dynamic list items.
        else:
            self._deinit_items_list_leaf()

    # ..................{ SLOTS ~ item                      }..................
    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def _select_tree_item(
        self, item_curr: QTreeWidgetItem, item_prev: QTreeWidgetItem) -> None:
        '''
        Slot signalled on the end user clicking the passed currently selected
        tree widget item *after* having clicked the passed previously selected
        tree widget item.

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
        # either:
        #
        # * The currently selected tree item if this item is a dynamic list.
        # * The parent tree item of the currently selected tree item if the
        #   latter is masquerading as a dynamic list item.
        #
        # Note that the union of these two sets is inefficiently recreated on
        # each invocation of this slot (which is clearly non-ideal), since the
        # maintenance of an instance variable preserving this union across all
        # modifications to these two sets incurs an even higher cost in both
        # inefficiency *AND* maintenance burden (which is much less non-ideal).
        # In short, do *NOT* attempt to institute the following anywhere:
        #     self._items_list = self._items_list_root | self._items_list_leaf
        #
        # We tried that already. The results were insane. Now, we are sane.
        self._action_sim_conf_tree_item_append.setEnabled(
            item_curr in self._items_list_root | self._items_list_leaf)

        # Permit users to remove this current tree item from its dynamic list
        # rooted at the parent tree item of this item only if the latter is
        # masquerading as a dynamic list item.
        #
        # While feasible, extending this operation to the entire dynamic list
        # (e.g., via a similar test as performed above) would obliterate an
        # entire list.
        self._action_sim_conf_tree_item_remove.setEnabled(
            item_curr in self._items_list_leaf)

    # ..................{ SLOTS ~ item : append             }..................
    #FIXME: Consider splitting up into more compartmentalized submethods.
    @Slot()
    def _append_tree_item(self) -> None:
        '''
        Slot signalled on the end user clicking the toolbar button associated
        with the :attr:`_action_sim_conf_tree_item_append` action, appending a
        new child item to the subtree of this tree widget rooted at the
        currently selected parent item.

        By design, the :meth:`_select_tree_item` slot guarantees this slot to
        be enabled only under the following conditions:

        * A tree item is currently selected.
        * The currently selected tree item is masquerading as either a:

          * **Dynamic list** (i.e., abstract container permitting child items
            to be interactively added to *and* removed from this parent item at
            runtime), in which case a new child item is appended to this parent
            item.
          * **Dynamic list item** (i.e., child item of such a container), in
            which case a new child item is appended to the parent item of this
            existing child item.

        In either case, this method (in order):

        #. Creates and appends a new YAML-backed simulation subconfiguration
           (e.g., another tissue profile) to the simulation subconfiguration
           associated with this parent item, initialized with sane defaults.
        #. Creates and appends a new child item as detailed above.
        #. Switches to the page widget of the top-level stack widget
           responsible for editing this new simulation subconfiguration.
        '''

        # Log the subsequent operation.
        logs.log_debug('Appending child tree item...')

        # Currently selected tree item.
        #
        # Note that this item is guaranteed to exist thanks to the contractual
        # guarantee established by the _select_tree_item() slot, implying this
        # getter is guaranteed to *NOT* raise exceptions.
        item_curr = self.get_item_current()

        # Parent tree item to append a new child tree item to. Specifically:
        item_list_root = None

        # If the currently selected tree item is masquerading as a dynamic
        # list, set the parent tree item to this item.
        if item_curr in self._items_list_root:
            item_list_root = item_curr
        # Else, the currently selected tree item is *NOT* masquerading as a
        # dynamic list. In this case...
        else:
            # If the currently selected tree item is *NOT* masquerading as a
            # dynamic list item, raise an exception.
            if item_curr not in self._items_list_leaf:
                raise BetseePySideTreeWidgetException(
                    QCoreApplication.translate(
                        'QBetseeSimConfTreeWidget',
                        'Tree item "{0}" not a '
                        'dynamic list or dynamic list item.'.format(
                            item_curr)))

            # Else, the currently selected tree item is masquerading as a
            # dynamic list item. In this case, set the parent tree item to the
            # parent of the currently selected tree item.
            item_list_root = guitreeitem.get_parent_item(item_curr)

        # First-column text of this parent tree item.
        item_list_root_name = item_list_root.text(0)

        # Log the subsequent operation.
        logs.log_debug(
            'Appending child list item to parent tree item "%s" YAML list...',
            item_list_root_name)

        # YAML-backed list subconfiguration underlying this dynamic list.
        yaml_list = self._item_list_root_to_yaml_list.get(
            item_list_root, None)

        # If this object is *NOT* a YAML-backed list subconfiguration and
        # hence does *NOT* define the append_default() method called below,
        # raise an exception.
        objects.die_unless_instance(obj=yaml_list, cls=YamlList)

        # YAML-backed list item subconfiguration created and appended to this
        # YAML-backed list subconfiguration. Note that, by the implementation
        # of each YamlListItemABC.make_default() method underlying this
        # creation, the name of this item is guaranteed to be unique across all
        # existing list items.
        yaml_list_item = yaml_list.append_default()

        #FIXME: *UGH.* There currently exists no uniform YAML API defining a
        #simple "name" property. Given that, here is what we're going to do:
        #
        #* In the "betse.lib.yaml.abc.yamllistabc" submodule:
        #  * Define a new "YamlListItemNamedABC" subclass.
        #  * Subclass the "YamlListItemTypedABC" subclass and others from that
        #    subclass.
        #* Import the "YamlListItemNamedABC" subclass above.
        #* Test for that subclass below.

        # If this object is *NOT* a YAML-backed typed list item
        # subconfiguration and hence does *NOT* define the "name" property
        # accessed below, raise an exception.
        # objects.die_unless_instance(
        #     obj=yaml_list_item, cls=YamlListItemTypedABC)

        # Log the subsequent operation.
        logs.log_debug(
            'Appending child list item to parent tree item "%s"...',
            item_list_root_name)

        # New child tree item masquerading as a dynamic list item of this
        # existing parent tree item, appended as the last such child of this
        # existing parent and associated with this subconfiguration.
        item_list_leaf = self._make_item_list_leaf(
            item_list_root=item_list_root,
            item_list_leaf_name=yaml_list_item.name,
        )

        # Programmatically select this new child tree item, implicitly
        # signalling the _select_tree_item() slot and hence switching to the
        # stack page associated with this item.
        self.setCurrentItem(item_list_leaf)

    # ..................{ SLOTS ~ item : remove             }..................
    #FIXME: Implement us up as documented below.
    @Slot()
    def _remove_tree_item(self) -> None:
        '''
        Slot signalled on the end user clicking the toolbar button associated
        with the :attr:`_action_sim_conf_tree_item_remove` action, removing an
        existing child item from the subtree of this tree widget rooted at the
        currently selected parent item.

        By design, the :meth:`_select_tree_item` slot guarantees this slot to
        be enabled only under the following conditions:

        * A tree item is currently selected.
        * The currently selected tree item is masquerading as a **dynamic list
          item** (i.e., child item of such a container), in which case that
          child item is removed from its parent item.

        In either case, this method (in order):

        #. Switches:

           * From the currently selected page widget of the top-level stack
             widget, previously responsible for editing this child item.
           * To either:

             * If this child item is *not* the first child item of its parent
               item and thus preceded by one or more siblings, the page widget
               associated with the child item preceding this child item.
             * Else, the page widget associated with the parent of this child
               item.
        #. Removes the existing YAML-backed simulation subconfiguration
           previously associated with this child item.
        #. Removes the existing child item as detailed above.
        '''

        # Currently selected tree item.
        #
        # Note that this item is guaranteed to exist thanks to the contractual
        # guarantee established by the _select_tree_item() slot, implying this
        # getter is guaranteed to *NOT* raise exceptions.
        item_curr = self.get_item_current()

        # Log this removal.
        logs.log_debug('Removing child tree item "%s"...', item_curr.text(0))
