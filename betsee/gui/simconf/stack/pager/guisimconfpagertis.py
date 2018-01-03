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
from betse.science.config.model.conftis import SimConfTissueDefault
# from betse.util.io.log import logs
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
        tissue_default = sim_conf.p.tissue_default

        # Initialize all scalar widgets on this page.
        main_window.sim_conf_tis_default_name.init(
            sim_conf=sim_conf,
            sim_conf_alias=SimConfTissueDefault.name,
            sim_conf_alias_parent=tissue_default,
        )
