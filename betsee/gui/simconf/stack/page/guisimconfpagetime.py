#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Temporal simulation configuration pager** (i.e., :mod:`PySide2`-based
controller for stack widget pages specific to temporal settings) functionality.
'''

# ....................{ IMPORTS                           }....................
#from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlpageabc import (
    QBetseePagerABC)

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfPagerTime(QBetseePagerABC):
    '''
    **Temporal simulation configuration pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the temporal stack widget
    page with corresponding settings of the current simulation configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all initialization spin box widgets on this page.
        main_window.sim_conf_time_init_total.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_total)
        main_window.sim_conf_time_init_step.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_step)
        main_window.sim_conf_time_init_sampling.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_sampling)

        # Initialize all simulation spin box widgets on this page.
        main_window.sim_conf_time_sim_total.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_time_total)
        main_window.sim_conf_time_sim_step.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_time_step)
        main_window.sim_conf_time_sim_sampling.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.sim_time_sampling)
