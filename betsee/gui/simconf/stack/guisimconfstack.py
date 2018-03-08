#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **stacked simulation configuration** (i.e., partitioning of the
simulation configuration into multiple pages, each displaying and editing all
settings associated with a single simulation feature  of the current such
configuration) facilities.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot  # QCoreApplication,
from PySide2.QtWidgets import QMainWindow, QStackedWidget, QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.type.obj import objects
from betse.util.type.text import strs
from betse.util.type.types import type_check
from betsee.gui.window.guinamespace import SIM_CONF_STACK_PAGE_NAME_PREFIX
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ CLASSES                            }....................
class QBetseeSimConfStackedWidget(QBetseeObjectMixin, QStackedWidget):
    '''
    :mod:`PySide2`-based stack widget containing multiple pages, each displaying
    and editing all settings associated with a single simulation feature (e.g.,
    ions, plots, tissue) of the current simulation configuration.

    This application-specific widget augments the stock :class:`QStackedWidget`
    with support for handling simulation configurations, including:

    * Integration with the corresponding :class:`QStackedWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    Caveats
    ----------
    Each child page widget of this stack widget should have a name prefixed by a
    substring uniquely identifying this widget to be a child page and the name
    of the parent page widget of this child page widget if any. Specifically:

    * If this child page widget is top-level (i.e., has no parent), this is the
      :attr:`SIM_CONF_STACK_PAGE_NAME_PREFIX` substring.
    * If this child page widget is *not* top-level (i.e., has a parent), this is
      the name of that parent page widget followed by a delimiting underscore.

    As a corrolary, this implies the names of all page widgets regardless of
    hierarchical nesting to be prefixed by the
    :attr:`SIM_CONF_STACK_PAGE_NAME_PREFIX` substring. No other widgets should
    have such names. Failure to comply may be met with an unutterable anguish.

    Parameters
    ----------
    _pagers : tuple
        Container of all high-level objects controlling the state of each stack
        widget page, preserved to prevent Python from erroneously garbage
        collecting these objects. Since these objects are *NOT* explicitly
        accessed after instantiation, this simplistic scheme suffices.
    _sim_conf : QBetseeSimConf
        High-level object controlling simulation configuration state.
    _tree_item_to_stack_page : dict
        Dictionary mapping from each :class:`QTreeWidgetItem` in the
        :class:`QTreeWidget` associated with this stack widget to each child
        page widget of this stack widget. This dictionary ensures that clicking
        on each :class:`QTreeWidgetItem` displays the corresponding page widget.

    See Also
    ----------
    QBetseeSimConfTreeWidget
        Corresponding :class:`QTreeWidget` instance, exposing all high-level
        features of the current simulation configuration which this
        :class:`QStackedWidget` instance then exposes the low-level settings of.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._pagers = None
        self._sim_conf = None
        self._tree_item_to_stack_page = None

        # Instantiate all pages of this stack widget.
        self._init_pagers()


    @type_check
    def _init_pagers(self) -> None:
        '''
        Instantiate each **page controller** (i.e., high-level
        :mod:`PySide2`-based object encapsulating the internal state of a page
        of this stack widget).
        '''

        # Defer method-specific imports for maintainability.
        from betsee.gui.simconf.stack.pager.guisimconfpagerion import (
            QBetseeSimConfIonStackedWidgetPager)
        from betsee.gui.simconf.stack.pager.guisimconfpagerpath import (
            QBetseeSimConfPathStackedWidgetPager)
        from betsee.gui.simconf.stack.pager.guisimconfpagerspace import (
            QBetseeSimConfSpaceStackedWidgetPager)
        from betsee.gui.simconf.stack.pager.guisimconfpagertime import (
            QBetseeSimConfTimeStackedWidgetPager)
        from betsee.gui.simconf.stack.pager.guisimconfpagertis import (
            QBetseeSimConfTissueDefaultStackedWidgetPager)

        # Tuple of all stack widget page controllers defined in arbitrary order.
        self._pagers = (
            QBetseeSimConfIonStackedWidgetPager(),
            QBetseeSimConfPathStackedWidgetPager(),
            QBetseeSimConfSpaceStackedWidgetPager(),
            QBetseeSimConfTimeStackedWidgetPager(),
            QBetseeSimConfTissueDefaultStackedWidgetPager(),
        )


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
        initialization** (i.e., initialization performed *after* the main window
        has been completely pre-populated with all initial child widgets).

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

        # Initialize each page of this stack widget.
        for pager in self._pagers:
            pager.init(main_window)

    # ..................{ INITIALIZERS ~ tree                }..................
    @type_check
    def _init_tree_to_stack(self, main_window: QMainWindow) -> None:
        '''
        Recursively map all tree widget items of the simulation
        configuration-specific tree widget in the passed parent main window to
        the corresponding child page widgets of this parent stack widget.

        Specifically, this method initializes the
        :attr:`_tree_item_to_stack_page` instance variable.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # Initialize this dictionary.
        self._tree_item_to_stack_page = {}

        # Top-level tree widget associated with this stack widget.
        tree_widget = main_window.sim_conf_tree

        # Generator iteratively yielding a 2-tuple of the name and value of each
        # child page of this stack widget, matching all instance variables of
        # this main window with names prefixed by an identifying substring.
        stack_pages = objects.iter_vars_custom_simple_prefixed(
            obj=main_window, prefix=SIM_CONF_STACK_PAGE_NAME_PREFIX)

        # Dictionary mapping the name to value of each such child page,
        # enabling iteration below to efficiently look these values up.
        stack_page_name_to_value = {
            stack_page_name: stack_page
            for stack_page_name, stack_page in stack_pages
        }

        # Recursion function intentionally defined as a closure to permit the
        # local variables defined above to be trivially and efficiently shared
        # between each recursive call of this function.
        @type_check
        def _map_tree_item_children_to_stack_pages(
            tree_item: QTreeWidgetItem,
            stack_page_name_prefix: str,
        ) -> None:
            '''
            Recursively map all child tree widget items of the passed parent
            tree widget item to the corresponding child page widgets of this
            parent stack widget.

            Parameters
            ----------
            tree_item : QTreeWidgetItem
                Parent tree widget item to recursively map all children of.
            stack_page_name_prefix : str
                Substring prefixing the names of all such child page widgets.
                If this parent tree widget item is:
                * The invisible placeholder root item, this is simply
                  :data:`SIM_CONF_STACK_PAGE_NAME_PREFIX`.
                * Any other item (including top-level, mid-level, and leaf
                  items) , this is the name of the child page widget
                  corresponding to this item suffixed by an underscore.
            '''

            # For the 0-based index of each child item of this parent item...
            #
            # Note that we intentionally iterate by tree widget items rather
            # than stack widget pages here. Why? Because iterating by the latter
            # would erroneously handle pages with no corresponding items, which
            # currently exist (e.g., temporary scratchpad purposes *NOT*
            # intended to be displayed to end users).
            for tree_item_child_index in range(tree_item.childCount()):
                # Current child item of this parent item.
                tree_item_child = tree_item.child(tree_item_child_index)

                # Text of this item in the first column.
                tree_item_child_text = tree_item_child.text(0)

                # Log this visitation.
                # logs.log_debug(
                #     'Visiting tree item "%s" child "%s"...',
                #     tree_item.text(), tree_item_child_text)

                # Name of the corresponding child page, synthesized from the
                # text of this child item as follows (in order):
                #
                # * Strip all whitespace from this child item's text (e.g., from
                #   "File Management" to "FileManagement").
                # * Prefix this child item's text by the identifying substring
                #   prefixing this child page's name (e.g., from
                #   "FileManagement" to 'sim_conf_stack_page_FileManagement').
                stack_page_name = (
                    stack_page_name_prefix +
                    strs.remove_whitespace(tree_item_child_text)
                )

                # Child page associated with this tree widget item if any or
                # "None" otherwise.
                stack_page = stack_page_name_to_value.get(stack_page_name, None)

                #FIXME: Convert to a fatal exception after finalizing this GUI.

                # If no such page exists...
                if stack_page is None:
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

                # Log this recursion.
                logs.log_debug(
                    'Mapping tree item "%s" to stacked page "%s"...',
                    tree_item_child_text, stack_page_name)

                # Map this child item to this child page.
                self._tree_item_to_stack_page[tree_item_child] = stack_page

                # If this child item itself contains child items, recursively
                # map all child items of this child item.
                #
                # Note that this test constitutes a negligible optimization but
                # is otherwise unnecessary. Performing this call for a child
                # item with no child items reduces to an inefficient noop. That
                # said, since the call stack is limited in Python, we prefer to
                # avoid exhausting the stack if we can do so. (So, we do so.)
                if tree_item_child.childCount():
                    _map_tree_item_children_to_stack_pages(
                        tree_item=tree_item_child,

                        # Require the names of all child pages of this child page to
                        # be prefixed by the name of this child page delimited by an
                        # underscore, a simple convention that saves sanity.
                        stack_page_name_prefix=stack_page_name + '_',
                    )

        # Recursively map all tree widget items of this tree widget.
        _map_tree_item_children_to_stack_pages(
            # Start at the invisible placeholder root item, provided by Qt for
            # exactly this recursive purpose.
            tree_item=tree_widget.invisibleRootItem(),

            # Substring prefixing the names of *ALL* stack page widgets.
            stack_page_name_prefix=SIM_CONF_STACK_PAGE_NAME_PREFIX,
        )

    # ..................{ SLOTS ~ public                     }..................
    # The following public slots are connected to from other widgets.

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def switch_page_to_tree_item(
        self,
        tree_item_curr: QTreeWidgetItem,
        tree_item_prev: QTreeWidgetItem,
    ) -> None:
        '''
        Switch to the child page widget of this stack widget associated with the
        passed tree widget item clicked by the end user.

        Parameters
        ----------
        tree_item_curr : QTreeWidgetItem
            Current tree widget item clicked by the end user.
        tree_item_prev : QTreeWidgetItem
            Previous tree widget item clicked by the end user.
        '''

        # Stack widget page associated with this tree widget item if any or
        # "None" otherwise.
        stack_page = self._tree_item_to_stack_page.get(tree_item_curr, None)

        #FIXME: Convert to a fatal exception after finalizing this GUI.

        # If no such page exists (e.g., due to this tree widget item being a
        # placeholder container for child items for which pages do exist)...
        if stack_page is None:
            # Log a non-fatal warning.
            logs.log_warning(
                'Simulation configuration-specific tree item "%s" '
                'associated with no stacked page.', tree_item_curr.text())

            # Ignore this attempt to switch the child page widget.
            return

        # Else, switch to this page.
        self.setCurrentWidget(stack_page)
