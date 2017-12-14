#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to tissue settings.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.config.confenum import CellsPickerType
from betse.science.config.model.conftis import SimConfTissueDefault
# from betse.util.io.log import logs
from betse.util.type.mapping.mapcls import OrderedArgsDict
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfTissueStackedWidgetPager(QBetseeControllerABC):
    '''
    :mod:`PySide2`-based stack widget page controller, connecting all editable
    widgets of the tissue page with the corresponding low-level settings of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # YAML-backed simulation subconfiguration whose class declares all
        # data descriptor-driven aliases referenced below.
        sim_conf_alias_parent = sim_conf.p.tissue_default

        # Initialize all intracellular widgets on this page.
        main_window.sim_conf_tis_default_name.init(
            sim_conf=sim_conf,
            sim_conf_alias=SimConfTissueDefault.name,
            sim_conf_alias_parent=sim_conf_alias_parent,
        )

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
