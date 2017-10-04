#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget exposing all low-level settings associated
with each high-level feature of a simulation configuration.
'''

#FIXME: Refactor all other stacked pages similarly.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
from betse.science.config.confenum import IonProfileType
# from betse.util.io.log import logs
from betse.util.type.mapping.mapcls import OrderedArgsDict
from betsee.gui.widget.sim.config.stack.pager.guisimconfpagerabc import (
    QBetseeSimConfStackedWidgetPagerABC)

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfIonStackedWidgetPager(
    QBetseeSimConfStackedWidgetPagerABC):
    '''
    :mod:`PySide2`-based stack widget page controller, connecting all editable
    widgets of the "Ion" page with the corresponding low-level settings of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all widgets on this page.
        main_window.sim_conf_ion_profile.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.ion_profile,
            enum_member_to_item_text=OrderedArgsDict(
                IonProfileType.BASIC, QCoreApplication.translate(
                    'QBetseeSimConfIonStackedWidgetPage', 'Basic'),
                IonProfileType.BASIC_CA, QCoreApplication.translate(
                    'QBetseeSimConfIonStackedWidgetPage', 'Basic + Ca2+'),
                IonProfileType.MAMMAL, QCoreApplication.translate(
                    'QBetseeSimConfIonStackedWidgetPage', 'Mammal'),
                IonProfileType.AMPHIBIAN, QCoreApplication.translate(
                    'QBetseeSimConfIonStackedWidgetPage', 'Amphibian'),
                IonProfileType.CUSTOM, QCoreApplication.translate(
                    'QBetseeSimConfIonStackedWidgetPage', 'Custom'),
            ),
        )
