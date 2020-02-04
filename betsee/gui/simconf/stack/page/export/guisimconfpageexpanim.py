#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Animation pager** (i.e., :mod:`PySide2`-based controller for stack widget
pages specific to animation exports) functionality.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from betse.science.pipe.export.pipeexpabc import SimPipeExportABC
from betse.science.pipe.export.pipeexpanim import SimPipeExportAnimCells
# from betse.util.io.log import logs
# from betse.util.type.types import type_check
from betsee.gui.simconf.stack.page.export.guisimconfpageexpabc import (
    QBetseeSimConfPagerExportABC)
from betsee.util.widget.abc.control.guictlpageabc import QBetseePagerABC

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfPagerAnim(QBetseePagerABC):
    '''
    **Animation exports simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of the
    stack widget page for *all* animation exports with corresponding settings
    of the current simulation configuration).
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


class QBetseeSimConfPagerAnimCells(QBetseePagerABC):
    '''
    **Cell cluster animation exports simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of the
    stack widget page for *all* cell cluster animation exports with
    corresponding settings of the current simulation configuration).
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


class QBetseeSimConfPagerAnimCellsExport(QBetseeSimConfPagerExportABC):
    '''
    **Cell cluster animation export pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the stack widget page for the
    currently selected cell cluster animation export with corresponding
    settings of a YAML-backed list item of the currently open simulation
    configuration).

    **This controller implements the well-known flyweight design pattern.**
    Specifically, this single controller is shared between the zero or more
    animation exports configured for this simulation and hence *cannot* be
    implicitly initialized at application startup. Instead, this controller is
    explicitly reinitialized in an on-the-fly manner immediately before this
    page is displayed to edit a single such export.
    '''

    # ..................{ SUPERCLASS ~ properties           }..................
    @property
    def _pipe_cls(self) -> SimPipeExportABC:
        return SimPipeExportAnimCells

    @property
    def _widget_name_prefix(self) -> str:
        return 'sim_conf_anim_cells_item_'

    @property
    def _yaml_list(self) -> str:
        return self._p.anim.anims_after_sim
