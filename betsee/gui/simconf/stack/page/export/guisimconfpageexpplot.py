#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Plot pager** (i.e., :mod:`PySide2`-based controller for stack widget pages
specific to plot exports) functionality.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from betse.science.pipe.export.pipeexpabc import SimPipeExportABC
from betse.science.pipe.export.plot.pipeexpplotcell import (
    SimPipeExportPlotCell)
from betse.science.pipe.export.plot.pipeexpplotcells import (
    SimPipeExportPlotCells)
# from betse.util.io.log import logs
# from betse.util.type.types import type_check
from betsee.gui.simconf.stack.page.export.guisimconfpageexpabc import (
    QBetseeSimConfPagerExportABC)
from betsee.util.widget.abc.control.guictlpageabc import QBetseePagerABC

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfPagerPlot(QBetseePagerABC):
    '''
    **Plot exports simulation configuration pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the stack widget page for
    *all* plot exports with corresponding settings of the current simulation
    configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    #FIXME: Initialize all widgets (if any) on this page.
    # @type_check
    # def init(self, main_window: QMainWindow) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().init(main_window)
    #
    #     # Simulation configuration state object.
    #     sim_conf = main_window.sim_conf
    #
    #     # Initialize all widgets on this page.
    #     main_window.sim_conf_time_init_total.init(
    #         sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_total)

# ....................{ SUBCLASSES ~ cell                 }....................
class QBetseeSimConfPagerPlotCell(QBetseePagerABC):
    '''
    **Single cell plot exports simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of the
    stack widget page for *all* single cell plot exports with corresponding
    settings of the current simulation configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    #FIXME: Initialize all widgets (if any) on this page.
    # @type_check
    # def init(self, main_window: QMainWindow) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().init(main_window)
    #
    #     # Simulation configuration state object.
    #     sim_conf = main_window.sim_conf
    #
    #     # Initialize all widgets on this page.
    #     main_window.sim_conf_time_init_total.init(
    #         sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_total)


class QBetseeSimConfPagerPlotCellExport(QBetseeSimConfPagerExportABC):
    '''
    **Single cell plot export pager** (i.e., :mod:`PySide2`-based controller
    connecting all editable widgets of the stack widget page for the currently
    selected single cell plot export with corresponding settings of a
    YAML-backed list item of the currently open simulation configuration).

    **This controller implements the well-known flyweight design pattern.**
    Specifically, this single controller is shared between the zero or more
    plot exports configured for this simulation and hence *cannot* be
    implicitly initialized at application startup. Instead, this controller is
    explicitly reinitialized in an on-the-fly manner immediately before this
    page is displayed to edit a single such export.
    '''

    # ..................{ SUPERCLASS ~ properties           }..................
    @property
    def _pipe_cls(self) -> SimPipeExportABC:
        return SimPipeExportPlotCell

    @property
    def _widget_name_prefix(self) -> str:
        return 'sim_conf_plot_cell_item_'

    @property
    def _yaml_list(self) -> str:
        return self._p.plot.plots_cell_after_sim

# ....................{ SUBCLASSES ~ cells                }....................
class QBetseeSimConfPagerPlotCells(QBetseePagerABC):
    '''
    **Cell cluster plot exports simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of the
    stack widget page for *all* cell cluster plot exports with corresponding
    settings of the current simulation configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    #FIXME: Initialize all widgets (if any) on this page.
    # @type_check
    # def init(self, main_window: QMainWindow) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().init(main_window)
    #
    #     # Simulation configuration state object.
    #     sim_conf = main_window.sim_conf
    #
    #     # Initialize all widgets on this page.
    #     main_window.sim_conf_time_init_total.init(
    #         sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_total)


class QBetseeSimConfPagerPlotCellsExport(QBetseeSimConfPagerExportABC):
    '''
    **Cell cluster plot export pager** (i.e., :mod:`PySide2`-based controller
    connecting all editable widgets of the stack widget page for the currently
    selected cell cluster plot export with corresponding settings of a
    YAML-backed list item of the currently open simulation configuration).

    **This controller implements the well-known flyweight design pattern.**
    Specifically, this single controller is shared between the zero or more
    plot exports configured for this simulation and hence *cannot* be
    implicitly initialized at application startup. Instead, this controller is
    explicitly reinitialized in an on-the-fly manner immediately before this
    page is displayed to edit a single such export.
    '''

    # ..................{ SUPERCLASS ~ properties           }..................
    @property
    def _pipe_cls(self) -> SimPipeExportABC:
        return SimPipeExportPlotCells

    @property
    def _widget_name_prefix(self) -> str:
        return 'sim_conf_plot_cells_item_'

    @property
    def _yaml_list(self) -> str:
        return self._p.plot.plots_cells_after_sim
