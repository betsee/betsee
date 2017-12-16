#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to spatial settings.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
from betse.science.config.confenum import CellLatticeType
# from betse.util.io.log import logs
from betse.util.type.mapping.mapcls import OrderedArgsDict
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfSpaceStackedWidgetPager(QBetseeControllerABC):
    '''
    :mod:`PySide2`-based stack widget page controller, connecting all editable
    widgets of the spatial page with the corresponding low-level settings of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all intracellular widgets on this page.
        main_window.sim_conf_space_intra_cell_radius.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.cell_radius)
        main_window.sim_conf_space_intra_lattice_disorder.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.cell_lattice_disorder)

        #FIXME: Refactor this from a QComboBox into a QRadioButtonGroup widget.
        #The former should typically *ONLY* be leveraged where required for a
        #large (typically dynamically constructed) list; the latter are
        #otherwise preferable for most general purposes.
        # main_window.sim_conf_space_intra_lattice_type.init(
        #     sim_conf=sim_conf,
        #     sim_conf_alias=Parameters.cell_lattice_type,
        #     enum_member_to_item_text=OrderedArgsDict(
        #         CellLatticeType.HEXAGONAL, QCoreApplication.translate(
        #             'QBetseeSimConfStackedWidget', 'Hexagonal'),
        #         CellLatticeType.SQUARE, QCoreApplication.translate(
        #             'QBetseeSimConfStackedWidget', 'Square'),
        #     ),
        # )

        # Initialize all extracellular widgets on this page.
        main_window.sim_conf_space_extra_grid_size.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.grid_size)
        main_window.sim_conf_space_extra_is_ecm.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.is_ecm)
        main_window.sim_conf_space_extra_world_len.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.world_len)