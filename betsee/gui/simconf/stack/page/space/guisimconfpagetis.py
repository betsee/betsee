#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Tissue simulation configuration pager** (i.e., :mod:`PySide2`-based
controller for stack widget pages specific to tissue profiles) functionality.
'''

#FIXME: Add support to the "QBetseeSimConfPagerTissueCustom"
#subclass for all YAML-based data descriptors specific to the
#"betse.science.config.model.conftis.SimConfTissueListItem" subclass.

#FIXME: We're not quite done here. Yet again, there exists a desynchronization
#issue between the "QBetseeSimConfPagerTissueCustom" subclass and
#the "QBetseeSimConfTreeWidget" subclass. Namely, when the end user attempts to
#interactively rename the currently selected tissue profile via the
#corresponding line edit widget, we need to:
#
#* Explicitly validate that this profile's new name does *NOT* collide with
#  that of any other existing tissue profile -- either default or custom.
#* If this profile's new name does collide:
#  * Display a non-fatal warning dialog that name collisions are prohibited.
#  * Implicitly revert this profile's name to the prior name (e.g., by
#    leveraging our existing undo functionality), thus guaranteeing no
#    collisions.

#FIXME: We're not quite done here. There currently exists a desynchronization
#issue between the "QBetseeSimConfPagerTissueCustom" subclass and
#the "QBetseeSimConfTreeWidget" subclass. Namely, when the name of the
#currently selected tissue profile is interactively renamed by the end user via
#the corresponding line edit widget, the first-column text of the corresponding
#tree item of the tree widget must *ALSO* be renamed. To do so, we'll probably
#want to define a new custom slot connected to a signal of this line edit
#widget signalled on changes. The question, of course, is where that slot
#should reside: in the "QBetseeSimConfPagerTissueCustom" subclass,
#in the "QBetseeSimConfTreeWidget" subclass, or elsewhere (e.g., in the
#"QBetseeSimConfStackedWidget" subclass)?
#
#Ultimately, that slot will need to map from the current stacked widget page to
#the corresponding tree widget item and hence should probably be defined in the
#subclass that has direct access to internal dictionaries mapping between tree
#widget items and stacked widget pages -- so, possibly in the
#"QBetseeSimConfStackedWidget" subclass. Consider it up, please.

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.config.model.conftis import SimConfTissueABC
from betse.science.enum import enumion
from betse.util.type.obj import objects
# from betse.util.io.log import logs
from betse.util.type.iterable import sequences
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlpageabc import (
    QBetseePagerABC, QBetseePagerItemizedMixin)

# ....................{ SUPERCLASSES                      }....................
class QBetseeSimConfPagerTissueABC(QBetseePagerABC):
    '''
    Abstract base class of all **tissue simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of a
    stack widget page applicable to tissue profiles of a particular type with
    corresponding settings of the current simulation configuration) subclasses.
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(
        self,

        # Mandatory parameters.
        main_window: QMainWindow,
        widget_name_prefix: str,
        tissue_profile: SimConfTissueABC,

        # Optional parameters.
        is_reinitable: bool = False,
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
        is_reinitable : bool
            ``True`` only if this method may be safely called multiple times.
            Defaults to ``False``.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window=main_window, is_reinitable=is_reinitable)

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
            is_reinitable=is_reinitable,
        )

        # Initialize all filename-specific widgets on this page.
        widget_image_filename.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=tissue_profile_cls.picker_image_filename,
            sim_conf_alias_parent=tissue_profile,
            push_btn=widget_image_btn,
            image_label=widget_image_label,
            is_reinitable=is_reinitable,
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
                is_reinitable=is_reinitable,
            )

# ....................{ SUBCLASSES ~ default              }....................
class QBetseeSimConfPagerTissueDefault(QBetseeSimConfPagerTissueABC):
    '''
    **Default tissue simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of the
    stack widget page for the default tissue profile with corresponding
    settings of the current simulation configuration).
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
class QBetseeSimConfPagerTissueCustom(
    QBetseePagerItemizedMixin, QBetseeSimConfPagerTissueABC):
    '''
    **Custom tissue simulation configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of the
    stack widget page for the currently selected custom tissue profile with
    corresponding settings of the current simulation configuration).

    **This controller implements the well-known flyweight design pattern.**
    Specifically, this single controller is shared between the zero or more
    custom tissue profiles configured for this simulation and hence *cannot* be
    implicitly initialized at application startup. Instead, this controller is
    explicitly reinitialized in an on-the-fly manner immediately before this
    page is displayed to edit a single such profile.
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
    def reinit(self, main_window: QMainWindow, list_item_index: int) -> None:

        # Tissue profile currently controlled by this pager.
        tissue_profile = sequences.get_index(
            sequence=main_window.sim_conf.p.tissue_profiles,
            index=list_item_index)

        # Refinalize the initialization of our superclass.
        super().init(
            main_window=main_window,
            widget_name_prefix='sim_conf_tis_custom_',
            tissue_profile=tissue_profile,
            is_reinitable=True,
        )
