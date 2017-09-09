#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget exposing all low-level settings associated
with each high-level feature of a simulation configuration.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Slot
from PySide2.QtWidgets import QMainWindow, QStackedWidget, QTreeWidgetItem
from betse.science.parameters import Parameters
from betse.util.io.log import logs
from betse.util.type import strs
from betse.util.type.obj import objects
from betse.util.type.types import type_check
from betsee.guiexceptions import BetseePySideTreeWidgetException
from betsee.gui.widget.guinamespace import SIM_CONF_STACK_PAGE_NAME_PREFIX

# ....................{ CLASSES                            }....................
class QBetseeSimConfStackedWidget(QStackedWidget):
    '''
    :mod:`PySide2`-based stack widget exposing all low-level settings associated
    with each high-level feature of the current simulation configuration.

    This application-specific widget augments the stock :class:`QStackedWidget`
    with support for handling simulation configurations, including:

    * Integration with the corresponding :class:`QStackedWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    Parameters
    ----------
    _sim_conf : QBetseeSimConf
        High-level object encapsulating simulation configuration state.
    _sim_conf_tree_item_to_page : dict
        Dictionary mapping from each :class:`QTreeWidgetItem` in the
        :class:`QTreeWidget` associated with this stack widget to each page
        widget in the stack widget. This dictionary is principally used to
        ensure that clicking on each :class:`QTreeWidgetItem` displays the
        corresponding page widget.

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

        # Initialize all instance variables for safety.
        self._sim_conf_tree_item_to_page = None


    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.widget.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Initialize this stacked widget against the passed parent main window.

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
        logs.log_debug('Initializing top-level stacked widget...')

        # Classify all variables accessed by subsequent slot invocations. Since
        # these variables do *NOT* own or otherwise preserve references to this
        # object, this is guaranteed to avoid circularities.
        self._sim_conf = main_window.sim_conf

        # Integrate this stack widget with this window's top-level tree widget.
        self._init_tree_to_stack(main_window)

        # Iteratively initialize all widgets associated with each stacked page.
        self._init_page_path(main_window)
        self._init_page_space(main_window)
        self._init_page_time(main_window)

    # ..................{ INITIALIZERS ~ tree                }..................
    @type_check
    def _init_tree_to_stack(self, main_window: QMainWindow) -> None:
        '''
        Initialize the :attr:`_sim_conf_tree_item_to_page` dictionary to
        integrate the tree widget contained in the passed parent main window
        with this stack widget.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # Initialize this dictionary.
        self._sim_conf_tree_item_to_page = {}

        # Set of the text of each tree widget item for which no corresponding
        # stack widget page exists (e.g., due to this item acting as a
        # placeholder signifying a dynamically created list of child items).
        TREE_ITEMS_IGNORED_TEXT = {
            'Networks',  # Dynamically created list of child network items.
        }

        # Top-level tree widget associated with this stack widget.
        tree_widget = main_window.sim_conf_tree

        # Generator yielding 2-tuples of the name and value of each page of this
        # stack widget, matching all instance variables of this main window with
        # names prefixed by a unique substring.
        stack_pages = objects.iter_vars_custom_simple_prefixed(
            obj=main_window, prefix=SIM_CONF_STACK_PAGE_NAME_PREFIX)

        # Dictionary mapping the name to value of each such stack widget page,
        # permitting the iteration below to efficiently look such values up.
        stack_page_name_to_value = {
            stack_page_name: stack_page
            for stack_page_name, stack_page in stack_pages
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
        for tree_item_top_index in range(tree_widget.topLevelItemCount()):
            # Current top-level item of this tree widget.
            tree_item_top = tree_widget.topLevelItem(tree_item_top_index)

            # Text of this item in the first column.
            tree_item_top_text = tree_item_top.text(0)

            # If this text suggests this item to be ignorable, do so.
            if tree_item_top_text in TREE_ITEMS_IGNORED_TEXT:
                continue

            # Name of the corresponding stack widget page, synthesized from the
            # text of this tree widget item with all whitespace stripped. For
            # example, the tree widget item with text "File Management"
            # corresponds to the stack widget page with name
            # 'sim_conf_stack_page_FileManagement'.
            stack_page_name = (
                SIM_CONF_STACK_PAGE_NAME_PREFIX +
                strs.remove_whitespace(tree_item_top_text)
            )

            # Stack widget page associated with this tree widget item if any or
            # "None" otherwise.
            stack_page = stack_page_name_to_value.get(stack_page_name, None)

            # If no such page exists, raise an exception.
            if stack_page is None:
                raise BetseePySideTreeWidgetException(
                    title=QCoreApplication.translate(
                       'QBetseeSimConfTreeWidget', 'Stacked Page not Found'),
                    synopsis=QCoreApplication.translate(
                        'QBetseeSimConfTreeWidget',
                        'Simulation configuration stacked page '
                        '"{0}" not found.'.format(stack_page_name)))

            # Map this tree widget item to this stack widget page.
            self._sim_conf_tree_item_to_page[tree_item_top] = stack_page

    # ..................{ INITIALIZERS ~ page : path         }..................
    @type_check
    def _init_page_path(self, main_window: QMainWindow) -> None:
        '''
        Initialize the filesystem page of this stack widget.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all seed line edit widgets on this page.
        main_window.sim_conf_path_seed_pick_file_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.seed_pickle_basename,)

        # Initialize all initialization line edit widgets on this page.
        main_window.sim_conf_path_init_pick_dir_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_pickle_dirname,)
        main_window.sim_conf_path_init_pick_file_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_pickle_basename,)
        main_window.sim_conf_path_init_exp_dir_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_export_dirname,)

        # Initialize all initialization push button widgets on this page.
        main_window.sim_conf_path_init_pick_dir_btn.init(
            sim_conf=sim_conf,
            line_edit=main_window.sim_conf_path_init_pick_dir_line)
        main_window.sim_conf_path_init_exp_dir_btn.init(
            sim_conf=sim_conf,
            line_edit=main_window.sim_conf_path_init_exp_dir_line)

        # Initialize all simulation line edit widgets on this page.
        main_window.sim_conf_path_sim_pick_dir_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_pickle_dirname,)
        main_window.sim_conf_path_sim_pick_file_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_pickle_basename,)
        main_window.sim_conf_path_sim_exp_dir_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_export_dirname,)

        # Initialize all simulation push button widgets on this page.
        main_window.sim_conf_path_sim_pick_dir_btn.init(
            sim_conf=sim_conf,
            line_edit=main_window.sim_conf_path_sim_pick_dir_line)
        main_window.sim_conf_path_sim_exp_dir_btn.init(
            sim_conf=sim_conf,
            line_edit=main_window.sim_conf_path_sim_exp_dir_line)

    # ..................{ INITIALIZERS ~ page : space        }..................
    @type_check
    def _init_page_space(self, main_window: QMainWindow) -> None:
        '''
        Initialize the spatial page of this stack widget.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all environmental grid widgets on this page.
        main_window.sim_conf_space_env_grid_size.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.grid_size,)

    # ..................{ INITIALIZERS ~ page : time         }..................
    @type_check
    def _init_page_time(self, main_window: QMainWindow) -> None:
        '''
        Initialize the temporal page of this stack widget.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Parent :class:`QMainWindow` widget to initialize this widget with.
        '''

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all initialization spin box widgets on this page.
        main_window.sim_conf_time_init_total.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_total,)
        main_window.sim_conf_time_init_step.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_step,)
        main_window.sim_conf_time_init_sampling.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_sampling,)

        # Initialize all simulation spin box widgets on this page.
        main_window.sim_conf_time_sim_total.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_time_total,)
        main_window.sim_conf_time_sim_step.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_time_step,)
        main_window.sim_conf_time_sim_sampling.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_time_sampling,)

    # ..................{ SLOTS ~ public                     }..................
    # The following public slots are connected to from other widgets.

    @Slot(QTreeWidgetItem, QTreeWidgetItem)
    def switch_page_to_tree_item(
        self,
        tree_item_curr: QTreeWidgetItem,
        tree_item_prev: QTreeWidgetItem,
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
        stack_page = self._sim_conf_tree_item_to_page.get(tree_item_curr, None)

        # If no such page exists (e.g., due to this tree widget item being a
        # placeholder container for child items for which pages do exist),
        # silently ignore this item.
        if stack_page is None:
            return

        # Else, switch to this page.
        self.setCurrentWidget(stack_page)
