#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to tissue settings.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.lib.yaml.abc.yamlabc import YamlABC
from betse.science.config.model.conftis import SimConfTissueDefault
from betse.util.type.obj import objects
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUBCLASSES                         }....................
#FIXME: Generalize to non-default tissue profiles.
class QBetseeSimConfTissueDefaultStackedWidgetPager(QBetseeControllerABC):
    '''
    :mod:`PySide2`-based stack widget page controller, connecting all editable
    widgets of the tissue page with the corresponding low-level settings of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # YAML-backed simulation subconfiguration whose class declares all
        # data descriptor-driven aliases referenced below.
        tissue_default = sim_conf.p.tissue_default

        # Initialize all general-purpose widgets on this page.
        main_window.sim_conf_tis_default_name.init(
            sim_conf=sim_conf,
            sim_conf_alias=SimConfTissueDefault.name,
            sim_conf_alias_parent=tissue_default,
        )

        # Initialize all filename-specific widgets on this page.
        main_window.sim_conf_tis_default_image_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=SimConfTissueDefault.picker_image_filename,
            sim_conf_alias_parent=tissue_default,
            push_btn   =main_window.sim_conf_tis_default_image_btn,
            image_label=main_window.sim_conf_tis_default_image_label,
        )

        # Initialize all ion-specific widgets on this page.
        self._init_widgets_ion(
            main_window=main_window, page_conf=tissue_default)


    #FIXME: Can this be generalized to custom ion profiles as well?
    def _init_widgets_ion(
        self, main_window: QMainWindow, page_conf: YamlABC) -> None:
        '''
        Initialize all ion-specific widgets on this page.

        Attributes
        ----------
        main_window : QMainWindow
            Main window singleton.
        page_conf : YamlABC
            YAML-backed simulation subconfiguration specific to this page.
        '''

        #FIXME: Consider shifting into BETSE itself -- perhaps in a new
        #"betse.science.simulate.simion" submodule?

        # Set of the abbreviated names of all available ions.
        ION_NAMES = {'Na', 'K', 'Cl', 'Ca', 'M', 'P',}

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # For the abbreviated name of each supported ion...
        for ion_name in ION_NAMES:
            # Name of the instance variable of the main window providing the
            # widget on this page editing the default tissue profile's membrane
            # diffusion constant for this ion.
            ion_widget_name = 'sim_conf_tis_default_mem_' + ion_name

            # Name of the data descriptor of the default tissue profile's class
            # providing this membrane diffusion constant.
            ion_descriptor_name = 'Dm_' + ion_name

            # This widget.
            ion_widget = objects.get_attr(
                obj=main_window, attr_name=ion_widget_name)

            # This data descriptor.
            ion_descriptor = objects.get_attr(
                obj=SimConfTissueDefault, attr_name=ion_descriptor_name)

            # Initialize this widget with this data descriptor.
            ion_widget.init(
                sim_conf=sim_conf,
                sim_conf_alias=ion_descriptor,
                sim_conf_alias_parent=page_conf,
            )
