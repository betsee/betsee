#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based tree widget exposing all high-level features of a
simulation configuration.
'''

#FIXME: Decouple the "QBetseeSimConfTreeWidget" from *ALL* hardcoded logic
#associating dynamic tree list items with corresponding stack widget pages and
#YAML-backed subconfigurations. Ideally, all such logic should be centralized
#into the specific "QBetseePagerItemizedMixin" subclass controlling all
#editable widgets for these subconfigurations (e.g.,
#"QBetseeSimConfPagerTissueCustom" for tissue profiles). To do so:
#
#* Define a new abstract QBetseePagerItemizedMixin.tree_parent_item_text_path()
#  property returning an iterable of strings providing the path to the
#  corresponding parent tree item (e.g., "('Space', 'Tissue')" for the
#  QBetseeSimConfPagerTissueCustom.tree_parent_item_text_path()
#  implementation).
#  * Alternately, it might be feasible to programmatically synthesize this path
#    from the object name of each such pager (e.g., converting
#    "sim_conf_stack_page_Space_Tissue_item" into "('Space', 'Tissue')").
#    Indeed, perhaps the latter approach, yes? Note, however, that the private
#    "QBetseeSimConfStackedWidget._stack_page_name_to_pager" dictionary
#    currently maintains the mapping required to perform this synthesis. We'd
#    probably want to at least publicize that dictionary for use elsewhere.
#  * On second thought, belay that. The former approach is explicit and hence
#    substantially more pragmatic. Perhaps more importantly, the latter
#    approach suffers a number of profound disadvantages in that the conversion
#    from human-readable tree item first-column text to machine-readable stack
#    widget object names does *NOT* losslessly generalize. In particular, while
#    the former may contain arbitrary characters (including punctuation and
#    Unicode characters), it's likely that the latter is confined to a proper
#    subset of the Unicode set -- possibly even to ASCII. Ergo, an explicit
#    mapping is substantially more general and hence superior. Let's go with
#    QBetseePagerItemizedMixin.tree_parent_item_text_path(), please.
#* Define a new abstract
#  "def QBetseePagerItemizedMixin.get_yaml_list(p: Parameters) -> YamlList"
#  method returning the YAML-backed subconfiguration managed by this pager.
#  Note that passing "p: Parameters" is probably unnecessary, as the pager can
#  simply preserve a reference to the desired "YamlList" in its init() method.
#  Ergo, this method may be safely reducible to a property resembling:
#    def QBetseePagerItemizedMixin.yaml_list(self) -> YamlList:
#  See the existing QBetseeSimConfPagerExportABC.yaml_list() property, please.
#* Refactor the QBetseePagerItemizedMixin.reinit() method to have a signature
#  resembling:
#    def reinit(self, main_window: QMainWindow, yaml_list_item: YamlABC) -> None:
#  That is, the reinit() method should be passed the actual YAML-backed list
#  item of interest rather than merely the index of that item. To do so,
#  existing callers of this method should instead:
#  * Obtain this list item from this index with  logic resembling:
#        yaml_list_item = sequences.get_index(
#            sequence=pager.yaml_list,
#            index=yaml_list_item_index)
#    Note use of the previously defined "QBetseePagerItemizedMixin.yaml_list"
#    property.
#  * Pass this "yaml_list_item" to this method.
#* Consider renaming the "QBetseePagerItemizedMixin" and
#  "QBetseePagerItemizedABC" classes to "QBetseePagerYamlListItemMixin" and
#  "QBetseePagerYamlListItemABC" for disambiguity. The previously defined
#  "QBetseePagerItemizedMixin.yaml_list" makes this fairly essential.
#* Refactor the QBetseeSimConfTreeWidget._init_items_list_root() and
#  QBetseeSimConfTreeWidget._init_items_list_leaf() methods to dynamically
#  leverage the properties defined above to programmatically perform the
#  equivalent logic in a non-hardcoded manner. Doing so sanely will probably
#  necessitate iterating over the items of the
#  "QBetseeSimConfStackedWidget._stack_page_name_to_pager" dictionary (which,
#  again, should probably be publicized) such that, for each such item, if that
#  item implements the "QBetseePagerItemizedMixin" interface, accessing the
#  properties defined above to perform the requisite logic.

#FIXME: Permit the "_action_sim_conf_tree_item_append" and
#"_action_sim_conf_tree_item_remove" operations to be triggered via a popup
#mena displayed when tree items supporting those operations are right-clicked.
#This should be largely trivial given that these operations have already been
#implemented but are currently only triggered by the "+" and "-" buttons.

#FIXME: Permit the "_action_sim_conf_tree_item_append" and
#"_action_sim_conf_tree_item_remove" operations to be undone. Doing so will
#probably prove non-trivial and has thus been deferred in favour of more
#low-hanging and/or mission-critical fruit.

#FIXME: Conditionally grey out the names (i.e., first-column text) of dynamic
#tree list items that are currently disabled. Specifically, if the YAML-backed
#list item subconfiguration underlying any such tree item is an instance of the
#"YamlBooledMixin" *AND* the current value of the "is_enabled" data descriptor
#of this subconfiguration is "False", the name of this tree item should be
#selectively greyed out. Implementing this properly will require connecting a
#the "checked" (...or something) signal of the checkbox widget of the pager
#controlling the corresponding stacked widget page with a new custom slot of
#this tree widget. (Everything has its price.)

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Slot
from PySide2.QtWidgets import QMainWindow, QTreeWidgetItem
from betse.lib.yaml.abc.yamllistabc import YamlList
from betse.lib.yaml.abc.yamlmixin import YamlNamedMixin
from betse.util.io.log import logs
from betse.util.type.iterable import sequences
from betse.util.type.iterable.mapping import mappings
from betse.util.type.obj import objects
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideTreeWidgetItemException  # BetseePySideTreeWidgetException,
from betsee.gui.data import guidataicon
from betsee.gui.simconf.stack.guisimconfstack import (
    QBetseeSimConfStackedWidget)
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
    _sim_conf : QBetseeSimConf
        High-level object controlling simulation configuration state.

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
        self._sim_conf = None


    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.window.guiwindow"
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
        self._sim_conf = main_window.sim_conf

        # Define all containers containing items of this tree widget *AFTER*
        # classifying requisite instance variables of this main window.
        #
        # Note that, as this tree widget is empty at __init__() time, this
        # initialization is necessarily deferred until init() time.
        self._init_items(main_window)

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

        # First item of this tree widget. Note that, by design, this item is
        # guaranteed to exist.
        tree_item_first = self.topLevelItem(0)

        # Select this item *AFTER* connecting all relevant signals and slots,
        # ensuring that the corresponding slot is called.
        self.setCurrentItem(tree_item_first)

    # ..................{ INITIALIZERS ~ items              }..................
    @type_check
    def _init_items(self, main_window: QMainWindow) -> None:
        '''
        Define *all* containers (including those both internal *and* external
        to this tree widget) containing items of this tree widget.

        Specifically, this method:

        * Removes all placeholder top-level placeholder items from this tree
          widget.
        * Finalizes the initialization of the simulation configuration-specific
          stack widget associated with this tree widget. Specifically, this
          stack widget is notified of all requisite mappings from each tree
          item of this tree widget to the corresponding child page widget of
          that stack widget.
        * Defines the set of all tree items masquerading as dynamic lists
          (i.e., :attr:`_items_list_root`).

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Remove all placeholder top-level placeholder items from this tree
        # *BEFORE* retrieving any items from this tree.
        self._init_items_top_todo()

        # Top-level tree items.
        item_export = self.get_item_with_text_path('Export')
        item_path   = self.get_item_with_text_path('Paths')
        item_space  = self.get_item_with_text_path('Space')
        item_time   = self.get_item_with_text_path('Time')

        # Export tree items.
        item_export_anim = guitreeitem.get_child_item_with_text_first(
            parent_item=item_export, child_text='Animation')
        item_export_csv = guitreeitem.get_child_item_with_text_first(
            parent_item=item_export, child_text='CSV')
        item_export_plot = guitreeitem.get_child_item_with_text_first(
            parent_item=item_export, child_text='Plot')

        # Animation export tree items.
        item_export_anim_cells = guitreeitem.get_child_item_with_text_first(
            parent_item=item_export_anim, child_text='Cell Cluster')

        # Plot export tree items.
        item_export_plot_cell = guitreeitem.get_child_item_with_text_first(
            parent_item=item_export_plot, child_text='Single Cell')
        item_export_plot_cells = guitreeitem.get_child_item_with_text_first(
            parent_item=item_export_plot, child_text='Cell Cluster')

        # Spatial tree items.
        item_space_ions = guitreeitem.get_child_item_with_text_first(
            parent_item=item_space, child_text='Ions')
        item_space_tissue = guitreeitem.get_child_item_with_text_first(
            parent_item=item_space, child_text='Tissue')

        # ................{ LIST                              }................
        # Define the set of all tree items masquerading as dynamic lists.

        # Simulation configuration, localized for simplicity.
        p = main_window.sim_conf.p

        # Dictionary mapping all such items to YAML-backed lists.
        self._item_list_root_to_yaml_list = {
            item_export_anim_cells: p.anim.anims_after_sim,
            item_export_csv:        p.csv.csvs_after_sim,
            item_export_plot_cell:  p.plot.plots_cell_after_sim,
            item_export_plot_cells: p.plot.plots_cells_after_sim,
            item_space_tissue:      p.tissue_profiles,
        }

        # Set of all such items.
        self._items_list_root = set(self._item_list_root_to_yaml_list.keys())

        # ................{ STACK                             }................
        # Finalizes the initialization of the simulation configuration-specific
        # stack widget associated with this tree widget. Specifically, this
        # stack widget is notified of all requisite mappings from each tree
        # item of this tree widget to the corresponding child page widget of
        # that stack widget.

        # Dictionary mapping each static tree item (i.e., item statically
        # defined via Qt (Creator|Designer) rather than dynamically defined at
        # application runtime) of this tree widget to the object name of the
        # corresponding child page widget of the top-level stack widget.
        item_static_to_stack_page_name = {
            item_export:            'sim_conf_stack_page_Export',
            item_export_anim:       'sim_conf_stack_page_Export_Anim',
            item_export_anim_cells: 'sim_conf_stack_page_Export_Anim_Cells',
            item_export_csv:        'sim_conf_stack_page_Export_CSV',
            item_export_plot:       'sim_conf_stack_page_Export_Plot',
            item_export_plot_cell:  'sim_conf_stack_page_Export_Plot_Cell',
            item_export_plot_cells: 'sim_conf_stack_page_Export_Plot_Cells',
            item_path:              'sim_conf_stack_page_Paths',
            item_space:             'sim_conf_stack_page_Space',
            item_space_ions:        'sim_conf_stack_page_Space_Ions',
            item_space_tissue:      'sim_conf_stack_page_Space_Tissue',
            item_time:              'sim_conf_stack_page_Time',
        }

        # Dictionary mapping each dynamic list tree item (i.e., item
        # masquerading as a list dynamically defined at application runtime
        # rather than statically defined via Qt (Creator|Designer)) of this
        # tree widget to the object name of the corresponding itemized page
        # widget (i.e., page configuring these items) of the top-level stack
        # widget.
        item_list_root_to_stack_page_name_list_leaf = {
            item_export_anim_cells: 'sim_conf_stack_page_Export_Anim_Cells_item',
            item_export_csv:        'sim_conf_stack_page_Export_CSV_item',
            item_export_plot_cell:  'sim_conf_stack_page_Export_Plot_Cell_item',
            item_export_plot_cells: 'sim_conf_stack_page_Export_Plot_Cells_item',
            item_space_tissue:      'sim_conf_stack_page_Space_Tissue_item',
        }

        # If any container containing dynamic list tree items defined above
        # does *NOT* contain the same such items as every other such container,
        # raise an exception. This is a rudimentary sanity test.
        mappings.die_unless_keys_equal(
            self._item_list_root_to_yaml_list,
            item_list_root_to_stack_page_name_list_leaf,
        )

        # Notify this stack widget of these mappings.
        main_window.sim_conf_stack.set_tree_item_to_stack_page(
            tree_item_static_to_stack_page_name=(
                item_static_to_stack_page_name),
            tree_item_list_root_to_stack_page_name_list_leaf=(
                item_list_root_to_stack_page_name_list_leaf),
        )


    def _init_items_top_todo(self) -> None:
        '''
        Remove all **placeholder top-level placeholder items** (i.e., items
        whose corresponding stacked page has yet to be implemented) from this
        tree widget.

        While extraneous, these items reside in the corresponding ``betsee.ui``
        file as a visual aid to streamline initial UI design.
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

    # ..................{ INITIALIZERS ~ items : leaf       }..................
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

        # For each parent tree item masquerading as a dynamic list and the
        # YAML-backed subconfiguration providing this dynamic list...
        for item_list_root, yaml_list in (
            self._item_list_root_to_yaml_list.items()):
            # If this parent already contains one or more children, raise an
            # exception. This method requires prior logic (e.g., the related
            # _deinit_items_list_leaf() method) to have deleted all prior
            # children if any from this parent.
            guitreeitem.die_if_parent_item(item_list_root)

            # For each existing YAML-backed list item of this dynamic list...
            for yaml_list_item in yaml_list:
                # Create and append a new child tree item associated with this
                # list item to this parent tree item.
                self._make_item_list_leaf(
                    item_list_root=item_list_root,
                    yaml_list_item=yaml_list_item)


    def _deinit_items_list_leaf(self) -> None:
        '''
        Remove all child tree items masquerading as dynamic list items.
        '''

        # Log this slot.
        logs.log_debug('Depopulating dynamic child tree items...')

        # For each parent tree item masquerading as a dynamic list and the
        # YAML-backed subconfiguration providing this dynamic list...
        for item_list_root in self._items_list_root:
            # Delete all child tree items masquerading as dynamic list items
            # from this parent tree item.
            guitreeitem.delete_child_items(item_list_root)

        # Reduce the set of all such child tree items to the empty set.
        self._items_list_leaf = set()

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

        # Unconditionally reset the contents of this tree back to their default
        # static state, regardless of whether the user is opening or closing a
        # simulation configuration file. Specifically:
        #
        # * Remove all child tree items masquerading as dynamic list items.
        self._deinit_items_list_leaf()

        # If the user opened a new simulation configuration file, append child
        # tree items masquerading as dynamic list items to their related parent
        # tree items masquerading as a dynamic lists.
        if sim_conf_filename:
            self._init_items_list_leaf()
        # Else, the user closed an open simulation configuration file. In this
        # case, no further work remains to be done.

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

    # ..................{ SLOTS ~ item : (append|remove)    }..................
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

        # Currently selected tree item, masquerading as either a dynamic list
        # *OR* dynamic list item.
        #
        # Note that this item is guaranteed to exist thanks to the contractual
        # guarantee established by the _select_tree_item() slot, implying this
        # getter is guaranteed to *NOT* raise exceptions.
        item_list = self.get_item_current()

        # Parent tree item to append a new child tree item to.
        item_list_root = self._get_item_list_root(item_list=item_list)

        # First-column text of this parent tree item.
        item_list_root_name = item_list_root.text(0)

        # Log the subsequent operation.
        logs.log_debug(
            'Appending child list item to parent tree item "%s" YAML list...',
            item_list_root_name)

        # YAML-backed list subconfiguration underlying this dynamic list.
        yaml_list = self._get_yaml_list_from_item_list(
            item_list=item_list_root)

        # YAML-backed list item subconfiguration created and appended to this
        # YAML-backed list subconfiguration. Note that, by the implementation
        # of each YamlListItemABC.make_default() method underlying this
        # creation, the name of this item is guaranteed to be unique across all
        # existing list items.
        yaml_list_item = yaml_list.append_default()

        # Log the subsequent operation.
        logs.log_debug(
            'Appending child list item to parent tree item "%s"...',
            item_list_root_name)

        # New child tree item masquerading as a dynamic list item of this
        # existing parent tree item, appended as the last such child of this
        # existing parent and associated with this subconfiguration.
        item_list_leaf = self._make_item_list_leaf(
            item_list_root=item_list_root, yaml_list_item=yaml_list_item)

        # Programmatically select this new child tree item, implicitly
        # signalling the _select_tree_item() slot and hence switching to the
        # stack page associated with this item.
        self.setCurrentItem(item_list_leaf)

        # Notify interested slots that the current simulation configuration is
        # now dirty (i.e., has unsaved changes) *AFTER* successfully appending
        # this child tree item.
        self._sim_conf.is_dirty = True


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

        # Log the subsequent operation.
        logs.log_debug('Removing child tree item...')

        # Currently selected tree item, masquerading as a dynamic list item.
        #
        # Note that this item is guaranteed to exist thanks to the contractual
        # guarantee established by the _select_tree_item() slot, implying this
        # getter is guaranteed to *NOT* raise exceptions here.
        item_list_leaf = self.get_item_current()

        # Parent tree item of this child tree item.
        item_list_root = guitreeitem.get_parent_item(item_list_leaf)

        # First-column text of this child tree item.
        item_list_leaf_name = item_list_leaf.text(0)

        # 0-based index of this child tree item in this parent tree item.
        item_list_leaf_index = item_list_root.indexOfChild(item_list_leaf)

        # Log this removal.
        logs.log_debug(
            'Removing child tree item %d "%s" from parent tree item "%s"...',
            item_list_leaf_index, item_list_leaf_name, item_list_root.text(0))

        # Tree item preceding this tree item.
        #
        # Note that this item is guaranteed to exist, implying this function
        # call is guaranteed to *NOT* raise an exception. Why? Because the
        # currently selected tree item is guaranteed to masquerade as a dynamic
        # list item by the implementation of the _select_tree_item() slot and
        # hence is guaranteed to be a child tree item of a parent tree item and
        # hence is guaranteed to *NOT* be a top-level tree item and hence is
        # guaranteed to be preceeded by at least one other item. (Gotcha.)
        item_preceding = guitreeitem.get_item_preceding(item_list_leaf)

        # Programmatically select this new child tree item, implicitly
        # signalling the _select_tree_item() slot and hence switching to the
        # stack page associated with this item.
        #
        # To avoid desynchronization issues (e.g., by briefly attempting to
        # display the prior contents of the current stack widget page since
        # invalidated by the removal of this item), do so *BEFORE* performing
        # any subsequent logic.
        self.setCurrentItem(item_preceding)

        # Log the subsequent operation.
        logs.log_debug(
            'Removing child list item %d "%s" YAML list item...',
            item_list_leaf_index, item_list_leaf_name)

        # YAML-backed list subconfiguration underlying this parent tree item.
        yaml_list = self._get_yaml_list_from_item_list(
            item_list=item_list_root)

        # If the 0-based index of this child tree item in this parent tree item
        # is *NOT* also a valid index of this list subconfiguration, raise an
        # exception. In theory, there should exist a one-to-one correlation
        # between the children of this parent and the list items of this list.
        sequences.die_unless_index(
            sequence=yaml_list, index=item_list_leaf_index)

        # YAML-backed list item subconfiguration underlying this child item.
        #
        # Note that this and the following functionality is strictly optional.
        # Technically, we *COULD* blindly delete this index from this list.
        # Practically, the blind leading the blind is a recipe for failure.
        yaml_list_item = yaml_list[item_list_leaf_index]

        # If this object is *NOT* a YAML-backed named configuration and hence
        # does *NOT* define the "name" property, raise an exception.
        objects.die_unless_instance(obj=yaml_list_item, cls=YamlNamedMixin)

        # If the first-column text of this child tree item is *NOT* the name of
        # this list item subconfiguration, raise an exception.
        if item_list_leaf_name != yaml_list_item.name:
            raise BetseePySideTreeWidgetItemException(
                QCoreApplication.translate(
                    'QBetseeSimConfTreeWidget',
                    'Child tree item "{0}" not backed by '
                    'YAML list item "{1}".'.format(
                        item_list_leaf_name, yaml_list_item.name)))

        # Remove this list item subconfiguration from this list
        # subconfiguration. Operator overloading for the preemptive win.
        del yaml_list[item_list_leaf_index]

        # Remove this child tree item from this parent tree item *AFTER*
        # successfully removing this list item subconfiguration from this list
        # subconfiguration -- a more fragile and hence error-prone operation.
        guitreeitem.delete_item(item_list_leaf)

        # Notify interested slots that the current simulation configuration is
        # now dirty (i.e., has unsaved changes) *AFTER* successfully removing
        # this child tree item.
        self._sim_conf.is_dirty = True

    # ..................{ MAKERS                            }..................
    @type_check
    def _make_item_list_leaf(
        self,
        item_list_root: QTreeWidgetItem,
        yaml_list_item: YamlNamedMixin,
    ) -> QTreeWidgetItem:
        '''
        Create and append a new child tree item masquerading as the passed
        YAML-backed dynamic list item to the existing sequence of child tree
        items maintained by the passed parent tree item masquerading as a
        dynamic list, returning this new child tree item.

        Parameters
        ----------
        item_list_root : QTreeWidgetItem
            Parent tree item masquerading as a dynamic list to append this new
            child tree item.
        yaml_list_item : YamlNamedMixin
            YAML-backed list item to be masqueraded by this new child tree
            item.

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

        # Set this child item's first-column icon to a bullet point.
        item_list_leaf.setIcon(0, guidataicon.get_icon_dot())

        # Set this child item's first-column text to the human-readable name of
        # this YAML-backed list item.
        item_list_leaf.setText(0, yaml_list_item.name)

        # Add this child item to the set of all tree items masquerading
        # as dynamic list items *AFTER* successfully making this item.
        self._items_list_leaf.add(item_list_leaf)

        # Return this child item.
        return item_list_leaf

    # ..................{ GETTERS                           }..................
    @type_check
    def _get_item_list_root(
        self, item_list: QTreeWidgetItem) -> QTreeWidgetItem:
        '''
        Tree item masquerading as a dynamic list for the passed tree item.

        Parameters
        ----------
        item_list : QTreeWidgetItem
            Tree item to return the tree item masquerading as a dynamic list.
            Specifically, this item *must* be either:

            * A parent tree item masquerading as a dynamic list.
            * A child tree item masquerading as a dynamic list item.

        Returns
        ----------
        QTreeWidgetItem
            Either:

            * If the passed tree item is a parent tree item masquerading as a
              dynamic list, this item as is.
            * if the passed tree item is a child tree item masquerading as a
              dynamic list item, the parent tree item of this child.

        Raises
        ----------
        BetseePySideTreeWidgetItemException
            If the passed tree item is neither a parent tree item masquerading
            as a dynamic list *nor* a child tree item masquerading as a dynamic
            list item (i.e., child of such a parent).
        '''

        # Parent tree item to be returned.
        item_list_root = None

        # If the passed item is masquerading as a dynamic list, this is the
        # parent tree item to return.
        if item_list in self._items_list_root:
            item_list_root = item_list
        # Else, the passed item is *NOT* masquerading as a dynamic list. In
        # this case...
        else:
            # If this item is *NOT* masquerading as a dynamic list item, raise
            # an exception.
            if item_list not in self._items_list_leaf:
                raise BetseePySideTreeWidgetItemException(
                    QCoreApplication.translate(
                        'QBetseeSimConfTreeWidget',
                        'Tree item "{0}" not a '
                        'dynamic list or dynamic list item.'.format(
                            item_list)))

            # Else, this item is masquerading as a dynamic list item. In this
            # case, the parent of this item is the parent tree item to return.
            item_list_root = guitreeitem.get_parent_item(item_list)

        # Return this parent tree item.
        return item_list_root


    @type_check
    def _get_yaml_list_from_item_list(
        self, item_list: QTreeWidgetItem) -> YamlList:
        '''
        YAML-backed list subconfiguration underlying the tree item masquerading
        as a dynamic list for the passed tree item.

        Parameters
        ----------
        item_list : QTreeWidgetItem
            Tree item to return the tree item masquerading as a dynamic list.
            Specifically, this item *must* be either:

            * A parent tree item masquerading as a dynamic list.
            * A child tree item masquerading as a dynamic list item.

        Returns
        ----------
        YamlList
            YAML-backed list subconfiguration underlying this dynamic list.

        Raises
        ----------
        BetseePySideTreeWidgetItemException
            If either:

            * The passed tree item is neither a:

              * Parent tree item masquerading as a dynamic list.
              * Child tree item masquerading as a dynamic list item.

            * No YAML-backed list subconfiguration underlies this dynamic list.
        '''

        # Parent tree item masquerading as a dynamic list of this tree item.
        item_list_root = self._get_item_list_root(item_list=item_list)

        # YAML-backed list subconfiguration underlying this parent tree item if
        # any *OR* "None" otherwise.
        yaml_list = self._item_list_root_to_yaml_list.get(
            item_list_root, None)

        # If no YAML-backed list subconfiguration underlies this parent tree
        # item, raise an exception.
        if yaml_list is None:
            raise BetseePySideTreeWidgetItemException(
                QCoreApplication.translate(
                    'QBetseeSimConfTreeWidget',
                    'Dynamic list tree item "{0}" '
                    'backed by no YAML list subconfiguration.'.format(
                        item_list)))

        # Return this YAML-backed list subconfiguration, implicitly validating
        # this object to actually be a subconfiguration.
        return yaml_list
