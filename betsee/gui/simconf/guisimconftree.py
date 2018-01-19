#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based tree widget exposing all high-level features of a
simulation configuration.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication  #, Slot
from PySide2.QtWidgets import QMainWindow
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.stock.guitreewdg import QBetseeTreeWidget

# ....................{ CLASSES                            }....................
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
    '''

    # ..................{ INITIALIZERS                       }..................
    # def __init__(self, *args, **kwargs) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().__init__(*args, **kwargs)


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
        initialization** (i.e., initialization performed *after* this widget has
        been completely pre-populated with all initial tree items).

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

        # Initialize our superclass.
        super().init()

        # Log this initialization.
        logs.log_debug('Initializing top-level tree widget...')

        # Expand all items of this tree widget to arbitrary depth.
        self.expandAll()

        # Connect all relevant signals and slots of this tree and stack widget.
        self._init_connections(main_window)


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
