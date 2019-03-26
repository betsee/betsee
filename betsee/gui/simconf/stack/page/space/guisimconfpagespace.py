#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Spatial simulation configuration pager** (i.e., :mod:`PySide2`-based
controller for stack widget pages specific to spatial settings) functionality.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
from betse.science.enum.enumconf import CellLatticeType
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlpageabc import (
    QBetseePagerABC)

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfPagerSpace(QBetseePagerABC):
    '''
    **Spatial simulation configuration pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the spatial stack widget page
    with corresponding settings of the current simulation configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all intracellular widgets on this page.
        main_window.sim_conf_space_intra_cell_radius.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.cell_radius)
        main_window.sim_conf_space_intra_lattice_disorder.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.cell_lattice_disorder)
        main_window.sim_conf_space_intra_lattice_type.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.cell_lattice_type,
            enum_member_to_widget_value={
                CellLatticeType.HEX: (
                    main_window.sim_conf_space_intra_lattice_hex),
                CellLatticeType.SQUARE: (
                    main_window.sim_conf_space_intra_lattice_square),
            },
        )

        # Initialize all extracellular widgets on this page.
        main_window.sim_conf_space_extra_grid_size.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.grid_size)
        main_window.sim_conf_space_extra_is_ecm.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.is_ecm)
        main_window.sim_conf_space_extra_world_len.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.world_len)
