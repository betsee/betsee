#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget exposing all low-level settings associated
with each high-level feature of a simulation configuration.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication, Slot
from PySide2.QtWidgets import QMainWindow, QStackedWidget
from betse.util.io.log import logs
from betse.util.type.types import type_check
# from betsee.gui.widget.sim.config.edit.guisimconfeditabc import (
#     QBetseeWidgetEditMixinSimConfig)

# ....................{ CLASSES                            }....................
class QBetseeStackedWidgetSimConfig(QStackedWidget):
    '''
    :mod:`PySide2`-based tree widget exposing all low-level settings associated
    with each high-level feature of the current simulation configuration.

    This application-specific widget augments the stock :class:`QStackedWidget`
    with support for handling simulation configurations, including:

    * Integration with the corresponding :class:`QStackedWidget`, exposing all
      low-level configuration settings for the high-level simulation feature
      currently selected from this tree.

    See Also
    ----------
    QBetseeTreeWidgetSimConfig
        Corresponding :class:`QTreeWidget` instance, exposing all high-level
        features of the current simulation configuration which this
        :class:`QStackedWidget` instance then exposes the low-level settings of.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Initialize all instance variables for safety.
        # self._item_to_sim_conf_stack_page = {}


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

        # Iteratively initialize all widgets associated with each stacked page.
        self._init_page_path(main_window)

    # ..................{ INITIALIZERS ~ page : path         }..................
    @type_check
    def _init_page_path(self, main_window: QMainWindow) -> None:
        '''
        Initialize the "File Management" page of this stacked widget.
        '''

        # Initialize all line edit widgets of this page.
        main_window.sim_conf_path_seed_edit.init(
            sim_conf=main_window.sim_conf)

        # Connect each line edit widget of this page to the corresponding button
        # displaying a file selection dialog.
        main_window.sim_conf_path_seed_edit.init(
            sim_conf=main_window.sim_conf)

    # ..................{ INITIALIZERS ~ path                }..................
    # @type_check
    # def _init_page_widget(
    #     self, page_widget: QBetseeWidgetMixinSimConfigEdit) -> None:
    #     '''
    #     Initialize the passed editable widget, presumed to be contained by an
    #     arbitrary page of this stacked widget.
    #
    #     Parameters
    #     ----------
    #     page_widget : QBetseeWidgetMixinSimConfigEdit
    #         Editable widget to be initialized.
    #     '''
    #
    #     pass
