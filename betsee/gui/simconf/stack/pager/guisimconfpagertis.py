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
from betse.science.config.model.conftis import SimConfTissueABC
from betse.science.enum import enumion
from betse.util.type.obj import objects
# from betse.util.io.log import logs
from betse.util.type.iterable import sequences
from betse.util.type.types import type_check
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

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(
        self,
        main_window: QMainWindow,
        widget_name_prefix: str,
        tissue_profile: SimConfTissueABC,
    ) -> None:
        '''
        Initialize this pager against the passed parent main window.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window
        may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this pager.
        widget_name_prefix : str
            Substring prefixing the name of all instance variables of the
            passed ``main_window`` whose values are all child widgets of the
            page controlled by this pager.
        tissue_profile : SimConfTissueABC
            Current YAML-backed tissue profile subconfiguration (i.e.,
            :class:`SimConfTissueABC` instance) associated with this page.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Type of this tissue profile.
        tissue_profile_cls = type(tissue_profile)

        # Widget editing this tissue's name.
        widget_name = main_window.get_widget(
            widget_name=widget_name_prefix + 'name')

        # Widget editing the filename of this tissue's image mask.
        widget_image_filename = main_window.get_widget(
            widget_name=widget_name_prefix + 'image_line')

        # Widget labelling the filename of this tissue's image mask.
        widget_image_label = main_window.get_widget(
            widget_name=widget_name_prefix + 'image_label')

        # Widget enabling end users to interactively browse the local
        # filesystem for the filename of this tissue's image mask.
        widget_image_btn = main_window.get_widget(
            widget_name=widget_name_prefix + 'image_btn')

        # Initialize all general-purpose widgets on this page.
        widget_name.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=tissue_profile_cls.name,
            sim_conf_alias_parent=tissue_profile,
        )

        # Initialize all filename-specific widgets on this page.
        widget_image_filename.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=tissue_profile_cls.picker_image_filename,
            sim_conf_alias_parent=tissue_profile,
            push_btn=widget_image_btn,
            image_label=widget_image_label,
        )

        # For the abbreviated name of each supported ion...
        for ion_name in enumion.iter_ion_names():
            # Widget editing this ion's membrane diffusion constant.
            ion_widget = main_window.get_widget(
                widget_name='{}mem_{}'.format(widget_name_prefix, ion_name))

            # Data descriptor of this tissue's class providing this constant.
            ion_descriptor = objects.get_attr(
                obj=tissue_profile_cls, attr_name='Dm_' + ion_name)

            # Initialize this widget with this data descriptor.
            ion_widget.init(
                sim_conf=main_window.sim_conf,
                sim_conf_alias=ion_descriptor,
                sim_conf_alias_parent=tissue_profile,
            )

# ....................{ SUBCLASSES ~ default              }....................
class QBetseeSimConfTissueDefaultStackedWidgetPager(
    QBetseeSimConfTissueStackedWidgetPagerABC):
    '''
    Default tissue-specific stack widget page controller, connecting all
    editable widgets of the page with the corresponding low-level settings of
    the current simulation configuration.
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Finalize the initialization of our superclass.
        super().init(
            main_window=main_window,
            widget_name_prefix='sim_conf_tis_default_',
            tissue_profile=main_window.sim_conf.p.tissue_default,
        )

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

    # ..................{ SUPERCLASS ~ initializers         }..................
    # Override the superclass init() method, which the reinit() method
    # subsequently calls immediately before this page is displayed to configure
    # a specific custom tissue profile, with a silent noop.
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Silently defer this finalization to the reinit() method.
        pass


    @type_check
    def reinit(self, list_item_index: int) -> None:

        # Main window of this application.
        main_window = guiappwindow.get_main_window()

        # Sequence of all currently configured tissue profiles.
        tissue_profiles = main_window.sim_conf.p.tissue_profiles

        # If this index does *NOT* index this sequence, raise an exception.
        sequences.die_unless_index(
            sequence=tissue_profiles, index=list_item_index)
        # Else, index indexes this sequence.

        # Refinalize the initialization of our superclass.
        super().init(
            main_window=main_window,
            widget_name_prefix='sim_conf_tis_custom_',
            tissue_profile=tissue_profiles[list_item_index],
        )


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
