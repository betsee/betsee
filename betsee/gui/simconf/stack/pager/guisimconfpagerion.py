#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to ions.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
from betse.science.config.confenum import IonProfileType
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betse.util.type.mapping.mapcls import OrderedArgsDict
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfIonStackedWidgetPager(QBetseeControllerABC):
    '''
    :mod:`PySide2`-based stack widget page controller, connecting all editable
    widgets of the ion page with the corresponding low-level settings of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
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

        #FIXME: Excise this after custom ion profile settings stabilize in the
        #BETSE core. When doing so:
        #
        #* Define a new _ion_profile_current_index_changed() slot in this class.
        #* Connect the "main_window.sim_conf_ion_profile.currentIndexChanged"
        #  signal to this slot.
        #* In the body of this slot:
        #  1. Add a one-liner disabling or enabling the
        #     "main_window.sim_conf_ion_custom" group box based on whether the
        #     newly selected ion profile type is the custom type or not.

        # Disable all currently non-working widgets on this page.
        main_window.sim_conf_ion_custom.setVisible(False)
