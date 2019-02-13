#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to tissue profiles.
'''

#FIXME: Generalize the "QBetseeSimConfTissueStackedWidgetPagerABC" superclass
#to non-default tissue profiles as follows:
#
#* Define the following new private abstract properties:
#  * "_SIM_CONF_STACK_PAGE_NAME_PREFIX", redefined by subclasses as follows:
#    * "QBetseeSimConfTissueDefaultStackedWidgetPager" should return
#      "sim_conf_tis_default_" for this property.
#    * "QBetseeSimConfTissueCustomStackedWidgetPager" should return
#      "sim_conf_tis_custom_" for this property.
#
#See below for further FIXME commentary.

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.lib.yaml.abc.yamlabc import YamlABC
from betse.science.config.model.conftis import SimConfTissueDefault
from betse.util.type.obj import objects
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.app import guiappwindow
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUPERCLASSES                      }....................
class QBetseeSimConfTissueStackedWidgetPagerABC(QBetseeControllerABC):
    '''
    Abstract base class of all tissue-specific stack widget page controller
    subclasses, connecting all editable widgets of the page with the
    corresponding low-level settings of the current simulation configuration.
    '''

    # ..................{ INITIALIZERS                      }..................
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

# ....................{ SUBCLASSES ~ default              }....................
class QBetseeSimConfTissueDefaultStackedWidgetPager(
    QBetseeSimConfTissueStackedWidgetPagerABC):
    '''
    Default tissue-specific stack widget page controller, connecting all
    editable widgets of the page with the corresponding low-level settings of
    the current simulation configuration.
    '''

    pass

# ....................{ SUBCLASSES ~ custom               }....................
class QBetseeSimConfTissueCustomStackedWidgetPager(
    QBetseeSimConfTissueStackedWidgetPagerABC):
    '''
    Custom tissue-specific stack widget page controller, connecting all
    editable widgets of the page with the corresponding low-level settings of
    the current simulation configuration.

    Design
    ----------
    **This controller implements the well-known flyweight design pattern.**
    Specifically, this single controller is shared between the zero or more
    custom tissue profiles configured for this simulation and hence *cannot* be
    implicitly initialized at application startup but must instead be
    explicitly reinitialized in an on-the-fly manner immediately before this
    page is displayed to configure a specific custom tissue profile.
    '''

    # ..................{ INITIALIZERS                      }..................
    # Override the superclass init() method, which the reinit() method
    # subsequently calls immediately before this page is displayed to configure
    # a specific custom tissue profile, with a silent noop.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        pass


    #FIXME: Externally call this method immediately before this page is
    #displayed to configure a specific custom tissue profile -- presumably from
    #either the "guisimconftree" or "guisimconfstack" widgets.

    #FIXME: Define a corresponding deinit() method as well -- which should be
    #called under at least the following circumstances:
    #
    #* When the custom tissue profile currently associated with this stack page
    #  is removed. Note that this should cleanly generalize to handle both the
    #  explicit removal of a single custom tissue profile by the end user *AND*
    #  the closure of the current simulation configuration file. Ergo, we
    #  should *NOT* to manually handle such closure; detecting the condition
    #  when the custom tissue profile currently associated with this stack page
    #  is removed should thus gracefully scale to all possible cases.
    #
    #  When this condition occurs *AND* this stack page is currently displayed,
    #  the default tissue profile stack page (which is guaranteed to exist)
    #  should be automatically switched to.
    #
    #Nice, eh?

    @type_check
    def reinit(self) -> None:

        # Reinitialize our superclass with this application's main window.
        super().init(guiappwindow.get_main_window())
