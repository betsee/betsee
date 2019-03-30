#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **stacked simulation configuration** (i.e., partitioning of the
simulation configuration into multiple pages, each displaying and editing all
settings associated with a single simulation feature  of the current such
configuration) facilities.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Slot
from PySide2.QtWidgets import QMainWindow, QStackedWidget, QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.type.obj import objects, objiter
from betse.util.type.text.string import strs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideStackedWidgetException
from betsee.gui.window.guinamespace import (
    SIM_CONF_STACK_PAGE_ITEMIZED_NAME_SUFFIX,
    SIM_CONF_STACK_PAGE_NAME_PREFIX,
)
from betsee.util.app import guiappwindow
from betsee.util.widget.mixin.guiwdgmixin import QBetseeObjectMixin
from betsee.util.widget.abc.control.guictlpageabc import (
    QBetseePagerItemizedMixin)
from betsee.util.widget.stock.tree import guitreeitem

# ....................{ CLASSES                           }....................
class QBetseeSimConfStackedWidget(QBetseeObjectMixin, QStackedWidget):
    '''
    :mod:`PySide2`-based stack widget containing multiple pages, each
    displaying and editing all settings associated with a single simulation
    feature (e.g., ions, plots, tissue) of the current simulation
    configuration.

    This application-specific widget augments the stock :class:`QStackedWidget`
    with support for handling simulation configurations, including:

    * Integration with the corresponding :class:`QTreeWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    Caveats
    ----------
    The name of each child page widget of this stack widget must be prefixed by
    a prefix uniquely identifying that widget to be a child page widget of this
    stack widget *and* the name of the parent page widget of that child if any.
    Spepcifically:

    * If this child page widget is top-level (i.e., has no parent), that
      widget's name must be prefixed by the
      :attr:`SIM_CONF_STACK_PAGE_NAME_PREFIX` substring.
    * If this child page widget is *not* top-level (i.e., has a parent), that
      widget's name must be prefixed by the name of that parent page widget
      followed by a delimiting underscore.

    As a corrolary, this implies that the names of all page widgets regardless
    of hierarchical nesting are all prefixed by at least the same
    :attr:`SIM_CONF_STACK_PAGE_NAME_PREFIX` substring. No other widgets should
    have such names. Failure to comply may be met with an unutterable anguish.

    Parameters
    ----------
    _pagers : tuple
        Container of all high-level objects controlling the state of each stack
        widget page, preserved to prevent Python from erroneously garbage
        collecting these objects. Since these objects are *not* explicitly
        accessed after instantiation, this simplistic scheme suffices.
    _sim_conf : QBetseeSimConf
        High-level object controlling simulation configuration state.
    _stack_page_name_to_pager : dict
        Dictionary mapping from the name of each page widget of this stack
        widget to the **pager** (i.e., high-level object controlling the flow
        of application execution for a page widget) controlling that widget.
        While the principal role of this dictionary is that of a **pager
        container** (i.e., container of all pager objects, preventing Python
        from erroneously garbage collecting these objects), this dictionary's
        secondary role as a pager mapper is no less mission critical.
    _tree_item_static_to_stack_page : dict
        Dictionary mapping from each **static tree item** (i.e., item
        statically defined via Qt (Creator|Designer) rather than dynamically
        defined at application runtime) of the :class:`QTreeWidget` associated
        with this stack widget to the corresponding child page widget of this
        stack widget.
    _tree_item_list_root_to_stack_page_list_leaf : dict
        Dictionary mapping from each **dynamic list tree item** (i.e., item
        masquerading as a list dynamically defined at application runtime
        rather than statically defined via Qt (Creator|Designer)) of the
        :class:`QTreeWidget` associated with this stack widget to the
        corresponding **itemized page widget** (i.e., page configuring tree
        items masquerading as list items) of this stack widget.

    See Also
    ----------
    QBetseeSimConfTreeWidget
        Corresponding :class:`QTreeWidget` instance, exposing all high-level
        features of the current simulation configuration which this
        :class:`QStackedWidget` instance then exposes the settings of.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Defer method-specific imports for maintainability.
        from betsee.gui.simconf.stack.page.guisimconfpagepath import (
            QBetseeSimConfPagerPath)
        from betsee.gui.simconf.stack.page.guisimconfpagetime import (
            QBetseeSimConfPagerTime)
        from betsee.gui.simconf.stack.page.export.guisimconfpageexport import (
            QBetseeSimConfPagerExport)
        from betsee.gui.simconf.stack.page.export.guisimconfpagecsv import (
            QBetseeSimConfPagerCSV, QBetseeSimConfPagerCSVExport)
        from betsee.gui.simconf.stack.page.space.guisimconfpageion import (
            QBetseeSimConfPagerIon)
        from betsee.gui.simconf.stack.page.space.guisimconfpagespace import (
            QBetseeSimConfPagerSpace)
        from betsee.gui.simconf.stack.page.space.guisimconfpagetis import (
            QBetseeSimConfPagerTissueDefault,
            QBetseeSimConfPagerTissueCustom,
        )

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify instance variables with sane defaults.
        self._stack_page_name_to_pager = {
            'sim_conf_stack_page_Export': QBetseeSimConfPagerExport(),
            'sim_conf_stack_page_Export_CSV': QBetseeSimConfPagerCSV(),
            'sim_conf_stack_page_Export_CSV_item': (
                QBetseeSimConfPagerCSVExport()),
            'sim_conf_stack_page_Paths': QBetseeSimConfPagerPath(),
            'sim_conf_stack_page_Space': QBetseeSimConfPagerSpace(),
            'sim_conf_stack_page_Space_Ions': QBetseeSimConfPagerIon(),
            'sim_conf_stack_page_Space_Tissue': (
                QBetseeSimConfPagerTissueDefault()),
            'sim_conf_stack_page_Space_Tissue_item': (
                QBetseeSimConfPagerTissueCustom()),
            'sim_conf_stack_page_Time': QBetseeSimConfPagerTime(),
        }
        self._tree_item_static_to_stack_page = {}
        self._tree_item_list_root_to_stack_page_list_leaf = {}

        # Nullify all remaining instance variables for safety.
        self._sim_conf = None


    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.window.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Initialize this stacked widget against the passed parent main window.

        This method is principally intended to perform **post-population
        initialization** (i.e., initialization performed *after* the main
        window has been fully pre-populated with all initial child widgets).

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

        # Initialize our superclass with all passed parameters.
        super().init()

        # Log this initialization.
        logs.log_debug('Initializing top-level stacked widget...')

        # Classify all variables accessed by subsequent slot invocations. Since
        # these variables do *NOT* own or otherwise preserve references to this
        # object, this is guaranteed to avoid circularities.
        self._sim_conf = main_window.sim_conf

        # Integrate this stack widget with this window's top-level tree widget.
        self._init_tree_to_stack(main_window)

        # Initialize each pager controlling each page widget of this stack
        # widget *AFTER* finalizing all other initialization above.
        for pager in self._stack_page_name_to_pager.values():
            pager.init(main_window)

    # ..................{ INITIALIZERS ~ tree               }..................
    @type_check
    def _init_tree_to_stack(self, main_window: QMainWindow) -> None:
        '''
        Recursively map all tree widget items of the top-level tree widget of
        the passed parent main window to the corresponding child page widgets
        of this stack widget.

        Specifically, this method defines private instance variables of this
        stack widget whose values are dictionaries implementing these mappings
        (e.g., :attr:`_tree_item_static_to_stack_page`).

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # Generator iteratively yielding a 2-tuple of the name and value of
        # each child page of this stack widget, matching all instance variables
        # of this main window with names prefixed by an identifying substring.
        stack_pages = objiter.iter_vars_custom_simple_prefixed(
            obj=main_window, prefix=SIM_CONF_STACK_PAGE_NAME_PREFIX)

        # Dictionary mapping the name to value of each such child page,
        # enabling iteration below to efficiently look these values up.
        stack_page_name_to_value = {
            stack_page_name: stack_page
            for stack_page_name, stack_page in stack_pages
        }

        # Recursive function intentionally defined as a closure to permit the
        # local variables defined above to be trivially and efficiently shared
        # between each recursive call of this function.
        @type_check
        def _map_tree_item_children_to_stack_pages(
            parent_item: QTreeWidgetItem,
            stack_page_name_prefix: str,
        ) -> None:
            '''
            Recursively map all child tree widget items of the passed parent
            tree widget item to the corresponding child page widgets of this
            stack widget.

            Parameters
            ----------
            parent_item : QTreeWidgetItem
                Parent tree widget item to recursively map all children of.
            stack_page_name_prefix : str
                Substring prefixing the names of all such child page widgets.
                If this parent tree widget item is:

                * The invisible placeholder root item, this is simply
                  :data:`SIM_CONF_STACK_PAGE_NAME_PREFIX`.
                * Any other item (including top-level, mid-level, and leaf
                  items), this is the name of the child page widget
                  corresponding to this item suffixed by an underscore.
            '''

            # For each child tree item of this parent tree item...
            #
            # Note that we intentionally iterate by tree widget items rather
            # than stack widget pages here. Why? Because iterating by the
            # latter would erroneously handle pages with no corresponding
            # items, which currently exist (e.g., temporary scratchpad purposes
            # *NOT* intended to be displayed to end users).
            for child_item in guitreeitem.iter_child_items(parent_item):
                # First-column text of this child tree item.
                child_item_text = child_item.text(0)

                # Log this visitation.
                # logs.log_debug(
                #     'Visiting tree item "%s" child "%s"...',
                #     parent_item.text(), child_item_text)

                # Name of the corresponding stack page, synthesized from the
                # text of this child item as follows (in order):
                #
                # * Strip all whitespace from this child item's text (e.g.,
                #   from "File Management" to "FileManagement").
                # * Prefix this child item's text by the identifying substring
                #   prefixing this child page's name (e.g., from
                #   "FileManagement" to 'sim_conf_stack_page_FileManagement').
                stack_page_name = (
                    stack_page_name_prefix +
                    strs.remove_whitespace(child_item_text))

                # Name of the corresponding dynamic list item stack page (i.e.,
                # page configuring child tree items of the current tree item
                # masquerading as list items) if any.
                stack_page_list_leaf_name = (
                    stack_page_name +
                    SIM_CONF_STACK_PAGE_ITEMIZED_NAME_SUFFIX)

                # Stack page associated with this tree item if any *OR* "None"
                # otherwise.
                stack_page = stack_page_name_to_value.get(
                    stack_page_name, None)

                # Stack page associated with child tree items of this tree item
                # if any *OR* "None" otherwise.
                stack_page_list_leaf = stack_page_name_to_value.get(
                    stack_page_list_leaf_name, None)

                # If a stack page associated with child tree items of this tree
                # item exists...
                #
                # To reduce the likelihood of edge cases (e.g., stack
                # exhaustion from overly deep recursion), this logic is handled
                # before the subsequent logic inducing recursion.
                if stack_page_list_leaf is not None:
                    # Log this association.
                    logs.log_debug(
                        'Mapping tree item "%s" to stacked page "%s" '
                        'for list children...',
                        child_item_text, stack_page_list_leaf_name)

                    # Map this tree item to this stack page.
                    self._tree_item_list_root_to_stack_page_list_leaf[
                        child_item] = stack_page_list_leaf

                # If a stack page is associated with this tree item...
                if stack_page is not None:
                    # Log this association.
                    logs.log_debug(
                        'Mapping tree item "%s" to stacked page "%s"...',
                        child_item_text, stack_page_name)

                    # Map this child item to this child page.
                    self._tree_item_static_to_stack_page[child_item] = (
                        stack_page)

                    # If this child item itself contains child items,
                    # recursively map all child items of this child item.
                    #
                    # Note that this test constitutes a negligible optimization
                    # but is otherwise unnecessary. Performing this call for a
                    # child item with no child items reduces to an inefficient
                    # noop. That said, since the call stack is limited in
                    # Python, we prefer to avoid exhausting the stack if we can
                    # do so. (So, we do so.)
                    if guitreeitem.is_parent_item(child_item):
                        _map_tree_item_children_to_stack_pages(
                            parent_item=child_item,

                            # Require the names of all child pages of this
                            # child page to be prefixed by the name of this
                            # child page delimited by an underscore, a simple
                            # convention that saves sanity.
                            stack_page_name_prefix=stack_page_name + '_',
                        )
                #FIXME: Convert to a fatal exception after finalizing this GUI.
                # Else, no stack page is associated with this tree item. In
                # this case...
                else:
                    # Log a non-fatal warning.
                    logs.log_warning(
                        'Simulation configuration-specific stacked page '
                        '"%s" not found.', stack_page_name)

                    # Skip to the next tree widget item.
                    continue

                    # raise BetseePySideTreeWidgetException(
                    #     QCoreApplication.translate(
                    #         'QBetseeSimConfStackedWidget',
                    #         'Simulation configuration-specific stacked page '
                    #         '"{0}" not found.'.format(stack_page_name)))

        # Recursively map all tree widget items of this tree widget.
        _map_tree_item_children_to_stack_pages(
            # Start at the invisible placeholder root item, provided by Qt for
            # exactly this recursive purpose.
            parent_item=main_window.sim_conf_tree.invisibleRootItem(),

            # Substring prefixing the names of *ALL* stack page widgets.
            stack_page_name_prefix=SIM_CONF_STACK_PAGE_NAME_PREFIX,
        )

    # ..................{ SLOTS ~ public                    }..................
    # The following public slots are connected to from other widgets.

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def switch_page_to_tree_item(
        self,
        tree_item_curr: QTreeWidgetItem,
        tree_item_prev: QTreeWidgetItem,
    ) -> None:
        '''
        Switch to the child page widget of this stack widget associated with
        the passed current tree widget item recently clicked by the end user
        and passed previous tree widget item previously clicked by that user.

        Parameters
        ----------
        tree_item_curr : QTreeWidgetItem
            Current tree widget item clicked by the end user.
        tree_item_prev : QTreeWidgetItem
            Previous tree widget item clicked by the end user.

        Raises
        ----------
        BetseePySideStackedWidgetException
            If no such page exists (e.g., due to this tree widget item being a
            placeholder container for child items for which pages do exist).
        '''

        # Stack page associated with this tree item if this item is static *OR*
        # "None" otherwise.
        stack_page = self._tree_item_static_to_stack_page.get(
            tree_item_curr, None)

        # If no such page exists...
        if stack_page is None:
            # Currently selected tree item, renamed for clarity.
            tree_item_list_leaf = tree_item_curr

            # First-column text of this item, equivalent to this item's name.
            tree_item_list_leaf_name = tree_item_list_leaf.text(0)

            # Parent tree item of the currently selected tree item.
            #
            # Note that this function call is guaranteed *NOT* to raise an
            # exception. Why? Because this tree widget's invisible root node
            # cannot by definition be selected, implying this currently
            # selected tree item cannot be the invisible root node.
            tree_item_list_root = guitreeitem.get_parent_item(
                tree_item_list_leaf)

            # Stack page associated with this child tree item if this item is a
            # dynamic list item of this parent tree item *OR* "None" otherwise.
            stack_page = self._tree_item_list_root_to_stack_page_list_leaf.get(
                tree_item_list_root, None)

            # If no such page still exists, raise an exception.
            if stack_page is None:
                raise BetseePySideStackedWidgetException(
                    QCoreApplication.translate(
                        'QBetseeSimConfStackedWidget',
                        'Tree item "{0}" stacked page not found.'.format(
                            tree_item_list_leaf_name)))
            # Else, this page exists.

            # Name of this stack page.
            stack_page_name = stack_page.objectName()

            # Pager controlling this stack page if any *OR* "None" otherwise.
            stack_page_pager = self._stack_page_name_to_pager.get(
                stack_page_name, None)

            # Log the reinitialization of this pager.
            logs.log_debug(
                'Reinitializing '
                'tree item "%s" stacked page "%s" pager "%s"...',
                tree_item_list_leaf_name,
                stack_page_name,
                objects.get_class_name_unqualified(stack_page_pager),
            )

            # If no such pager exists, raise an exception.
            if stack_page_pager is None:
                raise BetseePySideStackedWidgetException(
                    QCoreApplication.translate(
                        'QBetseeSimConfStackedWidget',
                        'Stacked page "{0}" pager not found.'.format(
                            stack_page_name)))
            # Else, this pager exists.

            # If this pager is *NOT* itemized, raise an exception. Only
            # itemized pagers (i.e., instances of the general-purpose
            # "QBetseePagerItemizedMixin" mixin) are permitted to
            # control stack pages associated with list items; likewise, only
            # itemized pagers define the reinit() method called below.
            objects.die_unless_instance(
                obj=stack_page_pager, cls=QBetseePagerItemizedMixin)

            # 0-based index of the currently selected tree item in the dynamic
            # list of all children of the parent tree item of this item.
            tree_item_list_leaf_index = tree_item_list_root.indexOfChild(
                tree_item_list_leaf)

            # Reinitialize this page *BEFORE* switching to this page, as the
            # former synchronizes every editable widget on this page with the
            # current value of the corresponding setting in the currently open
            # simulation configuration.
            stack_page_pager.reinit(
                main_window=guiappwindow.get_main_window(),
                list_item_index=tree_item_list_leaf_index)

        # Switch to this page, which is now guaranteed to both exist *AND* have
        # been reinitialized (if needed).
        self.setCurrentWidget(stack_page)
