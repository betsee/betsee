#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to tissue profiles.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.exceptions import BetseMethodUnimplementedException
from betse.lib.yaml.abc.yamlabc import YamlABC
from betse.science.config.model.conftis import (
    SimConfTissueDefault, SimConfTissueListItem)
from betse.util.type.obj import objects
# from betse.util.io.log import logs
from betse.util.type.types import type_check, ClassType
from betsee.util.app import guiappwindow
from betsee.util.widget.abc.control.guictlpagerabc import (
    QBetseeStackedWidgetPagerABC,
    QBetseeStackedWidgetPagerItemizedMixin
)

# ....................{ SUPERCLASSES                      }....................
class QBetseeSimConfTissueStackedWidgetPagerABC(QBetseeStackedWidgetPagerABC):
    '''
    Abstract base class of all tissue-specific stack widget page controller
    subclasses, connecting all editable widgets of the page with the
    corresponding low-level settings of the current simulation configuration.
    '''

    # ..................{ SUBCLASS ~ properties             }..................
    # Abstract properties required to be implemented by subclasses. Ideally,
    # these methods would be decorated by our @abstractproperty decorator.
    # Since doing so conflicts with metaclass semantics, these properties are
    # instead defined as concrete methods raising exceptions here.

    @property
    def _WIDGET_NAME_PREFIX(self) -> str:
        '''
        Substring prefixing the name of all :class:`QBetseeMainWindow`
        variables providing all child widgets of the top-level stack widget
        page controlled by this pager.
        '''

        raise BetseMethodUnimplementedException()


    @property
    def _tissue_profile(self) -> ClassType:
        '''
        YAML-backed tissue profile subconfiguration (i.e., instance of the
        :class:`SimConfTissueABC` superclass) specific to this pager.
        '''

        raise BetseMethodUnimplementedException()


    #FIXME: Excise this in favor of simply retrieving
    #"type(self._tissue_profile)". *sigh*
    @property
    def _tissue_profile_cls(self) -> ClassType:
        '''
        Type of the YAML-backed tissue profile subconfiguration (i.e., subclass
        of the :class:`SimConfTissueABC` superclass) specific to this pager.
        '''

        raise BetseMethodUnimplementedException()

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Names of instance variables of this main window whose values are
        # child widgets of this page required below.
        #
        # Name of the widget editing this tissue's name.
        widget_name = main_window.get_widget(
            widget_name=self._WIDGET_NAME_PREFIX + 'name')

        # Name of the widget editing the filename of this tissue's image mask.
        widget_image_filename = main_window.get_widget(
            widget_name=self._WIDGET_NAME_PREFIX + 'image_line')

        # Name of the widget labelling the filename of this tissue's image mask.
        widget_image_label = main_window.get_widget(
            widget_name=self._WIDGET_NAME_PREFIX + 'image_label')

        # Name of the widget enabling end users to interactively browse the
        # local filesystem for the filename of this tissue's image mask.
        widget_image_btn = main_window.get_widget(
            widget_name=self._WIDGET_NAME_PREFIX + 'image_btn')

        #FIXME: Generalize as follows:
        #
        #* Define a new abstract property "_tissue_profile" returning either
        #  "sim_conf.p.tissue_default" or... something.

        # YAML-backed simulation subconfiguration whose class declares all
        # data descriptor-driven aliases referenced below.
        tissue_default = sim_conf.p.tissue_default

        # Initialize all general-purpose widgets on this page.
        widget_name.init(
            sim_conf=sim_conf,
            sim_conf_alias=self._tissue_profile_cls.name,
            sim_conf_alias_parent=tissue_default,
        )

        # Initialize all filename-specific widgets on this page.
        widget_image_filename.init(
            sim_conf=sim_conf,
            sim_conf_alias=self._tissue_profile_cls.picker_image_filename,
            sim_conf_alias_parent=tissue_default,
            push_btn=widget_image_btn,
            image_label=widget_image_label,
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

    # ..................{ SUPERCLASS ~ properties           }..................
    @property
    def _WIDGET_NAME_PREFIX(self) -> str:
        return 'sim_conf_tis_default_'


    @property
    def _tissue_profile_cls(self) -> ClassType:
        return SimConfTissueDefault

# ....................{ SUBCLASSES ~ custom               }....................
class QBetseeSimConfTissueCustomStackedWidgetPager(
    QBetseeStackedWidgetPagerItemizedMixin,
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

    # ..................{ SUPERCLASS ~ properties           }..................
    @property
    def _WIDGET_NAME_PREFIX(self) -> str:
        return 'sim_conf_tis_custom_'


    @property
    def _tissue_profile_cls(self) -> ClassType:
        return SimConfTissueListItem

    # ..................{ SUPERCLASS ~ initializers         }..................
    # Override the superclass init() method, which the reinit() method
    # subsequently calls immediately before this page is displayed to configure
    # a specific custom tissue profile, with a silent noop.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        pass


    @type_check
    def reinit(self, list_leaf_index: int) -> None:

        # Reinitialize our superclass with this application's main window.
        super().init(guiappwindow.get_main_window())


    #FIXME: Implement us up.
    #FIXME: Call this method under at least the following circumstances:
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
    def deinit(self) -> None:

        pass
