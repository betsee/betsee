#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
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
from betse.util.type.iterable.mapping import mappings
from betse.util.type.obj import objects, objtest
from betse.util.type.types import type_check, MappingType
from betsee.guiexception import BetseePySideStackedWidgetException
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

    Attributes
    ----------
    _sim_conf : QBetseeSimConf
        High-level object controlling simulation configuration state.

    Attributes (Container)
    ----------
    _pagers : tuple
        Container of all high-level objects controlling the state of each stack
        widget page, preserved to prevent Python from erroneously garbage
        collecting these objects. Since these objects are *not* explicitly
        accessed after instantiation, this simplistic scheme suffices.

    Attributes (Container: Dictionary)
    ----------
    _stack_page_name_to_page : dict
        Dictionary mapping from the object name of each page widget of this
        stack widget to that widget.
    _stack_page_name_to_pager : dict
        Dictionary mapping from the object name of each page widget of this
        stack widget to the **pager** (i.e., high-level object controlling the
        flow of application execution for a page widget) controlling that
        widget. This dictionary also serves as the principal **pager
        container** (i.e., container of all pager objects, preventing Python
        from erroneously garbage collecting these objects).
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
        corresponding **itemized page widget** (i.e., page configuring these
        tree items) of this stack widget.

    See Also
    ----------
    :class:`QBetseeSimConfTreeWidget`
        Corresponding :class:`QTreeWidget` instance, exposing all high-level
        features of the current simulation configuration which this
        :class:`QStackedWidget` instance then exposes the settings of.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf = None
        self._stack_page_name_to_page = None
        self._stack_page_name_to_pager = None
        self._tree_item_static_to_stack_page = None
        self._tree_item_list_root_to_stack_page_list_leaf = None


    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.window.guiwindow"
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

        # Defer method-specific imports for maintainability.
        from betsee.gui.simconf.stack.page.guisimconfpagepath import (
            QBetseeSimConfPagerPath)
        from betsee.gui.simconf.stack.page.guisimconfpagetime import (
            QBetseeSimConfPagerTime)
        from betsee.gui.simconf.stack.page.export.guisimconfpageexport import (
            QBetseeSimConfPagerExport)
        from betsee.gui.simconf.stack.page.export.guisimconfpageexpanim import (
            QBetseeSimConfPagerAnim,
            QBetseeSimConfPagerAnimCells,
            QBetseeSimConfPagerAnimCellsExport,
        )
        from betsee.gui.simconf.stack.page.export.guisimconfpageexpcsv import (
            QBetseeSimConfPagerCSV, QBetseeSimConfPagerCSVExport)
        from betsee.gui.simconf.stack.page.export.guisimconfpageexpplot import (
            QBetseeSimConfPagerPlot,
            QBetseeSimConfPagerPlotCell,
            QBetseeSimConfPagerPlotCellExport,
            QBetseeSimConfPagerPlotCells,
            QBetseeSimConfPagerPlotCellsExport,
        )
        from betsee.gui.simconf.stack.page.space.guisimconfpageion import (
            QBetseeSimConfPagerIon)
        from betsee.gui.simconf.stack.page.space.guisimconfpagespace import (
            QBetseeSimConfPagerSpace)
        from betsee.gui.simconf.stack.page.space.guisimconfpagetis import (
            QBetseeSimConfPagerTissueDefault,
            QBetseeSimConfPagerTissueCustom,
        )

        # Initialize our superclass with all passed parameters.
        super().init()

        # Log this initialization.
        logs.log_debug('Initializing top-level stacked widget...')

        # Classify all variables accessed by subsequent slot invocations. Since
        # these variables do *NOT* own or otherwise preserve references to this
        # object, this is guaranteed to avoid circularities.
        self._sim_conf = main_window.sim_conf

        # Dictionary mapping the object name of each stack page widget to the
        # pager controlling that page.
        self._stack_page_name_to_pager = {
            'sim_conf_stack_page_Export': (
                QBetseeSimConfPagerExport(self)),
            'sim_conf_stack_page_Export_Anim': (
                QBetseeSimConfPagerAnim(self)),
            'sim_conf_stack_page_Export_Anim_Cells': (
                QBetseeSimConfPagerAnimCells(self)),
            'sim_conf_stack_page_Export_Anim_Cells_item': (
                QBetseeSimConfPagerAnimCellsExport(self)),
            'sim_conf_stack_page_Export_CSV': (
                QBetseeSimConfPagerCSV(self)),
            'sim_conf_stack_page_Export_CSV_item': (
                QBetseeSimConfPagerCSVExport(self)),
            'sim_conf_stack_page_Export_Plot': (
                QBetseeSimConfPagerPlot(self)),
            'sim_conf_stack_page_Export_Plot_Cell': (
                QBetseeSimConfPagerPlotCell(self)),
            'sim_conf_stack_page_Export_Plot_Cell_item': (
                QBetseeSimConfPagerPlotCellExport(self)),
            'sim_conf_stack_page_Export_Plot_Cells': (
                QBetseeSimConfPagerPlotCells(self)),
            'sim_conf_stack_page_Export_Plot_Cells_item': (
                QBetseeSimConfPagerPlotCellsExport(self)),
            'sim_conf_stack_page_Paths': (
                QBetseeSimConfPagerPath(self)),
            'sim_conf_stack_page_Space': (
                QBetseeSimConfPagerSpace(self)),
            'sim_conf_stack_page_Space_Ions': (
                QBetseeSimConfPagerIon(self)),
            'sim_conf_stack_page_Space_Tissue': (
                QBetseeSimConfPagerTissueDefault(self)),
            'sim_conf_stack_page_Space_Tissue_item': (
                QBetseeSimConfPagerTissueCustom(self)),
            'sim_conf_stack_page_Time': (
                QBetseeSimConfPagerTime(self)),
        }

        # Dictionary mapping the object name of each stack page widget to that
        # widget.
        self._stack_page_name_to_page = {
            stack_page_name: main_window.get_widget(stack_page_name)
            for stack_page_name in self._stack_page_name_to_pager.keys()
        }

        # Initialize each pager controlling each page widget of this stack
        # widget *AFTER* finalizing all other initialization above.
        for stack_pager in self._stack_page_name_to_pager.values():
            stack_pager.init(main_window)

    # ..................{ SLOTS                             }..................
    # Public slots connected to from other widgets.

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
            objtest.die_unless_instance(
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

    # ..................{ SETTERS                           }..................
    @type_check
    def set_tree_item_to_stack_page(
        self,
        tree_item_static_to_stack_page_name: MappingType,
        tree_item_list_root_to_stack_page_name_list_leaf: MappingType,
    ) -> None:
        '''
        Establish all mappings required by this stack widget to seamlessly map
        from each tree item of the tree widget associated with this stack
        widget to the corresponding child page widget of this stack widget.

        Parameters
        ----------
        tree_item_static_to_stack_page_name : dict
            Dictionary mapping from each **static tree item** (i.e., item
            statically defined via Qt (Creator|Designer) rather than
            dynamically defined at application runtime) of the tree widget
            associated with this stack widget to the object name of the
            corresponding child page widget of this stack widget.
        tree_item_list_root_to_stack_page_name_list_leaf : dict
            Dictionary mapping from each **dynamic list tree item** (i.e., item
            masquerading as a list dynamically defined at application runtime
            rather than statically defined via Qt (Creator|Designer)) of the
            tree widget associated with this stack widget to the object name of
            the corresponding **itemized page widget** (i.e., page configuring
            these tree items) of this stack widget.
        '''


        # Convert each such dictionary to the corresponding dictionary with all
        # object names of stack widget pages converted to those actual pages.
        self._tree_item_static_to_stack_page = (
            self._convert_mapping_values_stack_page_name_to_page(
                tree_item_static_to_stack_page_name))
        self._tree_item_list_root_to_stack_page_list_leaf = (
            self._convert_mapping_values_stack_page_name_to_page(
                tree_item_list_root_to_stack_page_name_list_leaf))


    @type_check
    def _convert_mapping_values_stack_page_name_to_page(
        self, mapping: MappingType) -> MappingType:
        '''
        Dictionary mapping from arbitrary keys to stack widget pages converted
        from the passed dictionary mapping from arbitrary keys to object names
        of stack widget pages.

        Succinctly, this method creates and returns a new dictionary whose
        values are stack widget pages whose object names are the values of the
        passed dictionary.
        '''

        # Create and return a new dictionary mapping...
        return {
            # From this key to the stack widget page with this object name,
            # raising a human-readable exception if no such page exists...
            key: mappings.get_key_value(
                mapping=self._stack_page_name_to_page, key=stack_page_name)
            # For each arbitrary key and object name of a stack widget page in
            # the passed mapping.
            for key, stack_page_name in mapping.items()
        }
