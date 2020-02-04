#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Export simulation configuration pager** (i.e., :mod:`PySide2`-based
controller for stack widget pages specific to export settings) functionality.
'''

#FIXME: Replace the combo box selecting each colormap with a widget more
#appropriate to the excrutiating number of available colormaps. Honestly, the
#best (albeit hardest to implement) approach would be to adopt a similar
#approach used in most applications that enable end users to configure specific
#colors. Think "color wheels." Specifically:
#
#* Augment the "betse.lib.matplotlib.mplcolormap" submodule with a *MASSIVE*
#  database describing all well-known colormaps bundled with matplotlib. Since
#  this will be positively massive, we actually probably want to:
#  * Define a new "betse.lib.matplotlib.colormap" subpackage.
#  * Shift the existing "betse.lib.matplotlib.mplcolormap" submodule to
#    "betse.lib.matplotlib.colormap.mplcolormap".
#  * Define a new "betse.lib.matplotlib.colormap.mplcmapmetadata" submodule
#    defining this database.
#  Although we'll obviously never be able to keep up with modern matplotlib
#  developments, we should at least be able to make a reasonable go of things.
#  To do so, this submodule should:
#  * Define a new "MplColormapMetadata" class, which should define the
#    following instance variables:
#    * "kind", the machine-readable matplotlib-specific name of this colormap.
#    * "categories", a sequence of one or more human-readable strings
#       iteratively naming all arbitrary categories to which this colormap
#       belongs (in descending order of hierarchical taxonomy).
#    * "description", a human-readable description of this colormap.
#  * Define a new "COLORMAP_KIND_TO_METADATA" dictionary mapping from the
#    "kind" of each such colormap to a "MplColormapMetadata" instance
#    describing that colormap in detail.
#  * Define an init() function whose implementation:
#    * Determines if there are any currently registered matplotlib colormaps
#      whose names are *NOT* keys of the "COLORMAP_KIND_TO_METADATA"
#      dictionary. If one or more such colormaps exist, a *SINGLE* non-fatal
#      warning containing the names of these colormaps should be logged.
#* For each of the four types of colormaps currently configurable by this
#  pager:
#  * Display a label presenting the human-readable name of this colormap,
#    probably synthesized from the "categories" variable detailed above.
#  * Display a push button with text resembling "Select..." or "Browse...".
#    When pushed, this button should display a modal dialog that:
#    * Displays a *TREE* dynamically constructed from the "categories" sequence
#      of each "MplColormapMetadata" instance of the
#      "COLORMAP_KIND_TO_METADATA" dictionary.
#    * Displays a label presenting the human-readable description of the
#      currently selected colormap in this tree, equivalent to the
#      "description" variable detailed above.
#    * Display a label presenting the machine-readable kind of this colormap,
#      equivalent to the "kind" variable detailed above.
#    * Display a line segment visualizing this colormap. (See "FIXME:" below.)
#  * Display a line segment visualizing this colormap. (See "FIXME:" below.)
#
#Extraordinarily non-trivial, of course. Which suggests we'll probably never
#implement even a tenth of the above plan. Still, a volunteer coder can dream.

#FIXME: Below the combobox selecting each colormap on the page controlled by
#this pager, visually display a line segment depicting the perceptual gradiant
#implemented by that colormap. Fortunately, this is considerably more trivial
#than one might expect. See the matplotlib-specific logic at the end of:
#    https://matplotlib.org/tutorials/colors/colormaps.html
#Technically, PySide2 cannot directly display matplotlib-specific logic.
#Pragmatically, however, there should be some means of doing so. After all,
#we'll need to resolve this issue when attempting to embed mid-simulation
#matplotlib figures and animations in BETSEE's Qt-based simulator. Therefore,
#we should be able to generically reuse the solution we discover there *HERE*.
#Alternately, it should also be feasible to manually paint each such colormap
#onto an appropriate Qt canvas widget of some sort. (Non-trivial, presumably.)

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
from betse.science.config.export.visual.confexpvisual import (
    SimConfExportVisual)
# from betse.util.io.log import logs
from betse.lib.matplotlib import mplcolormap
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlpageabc import QBetseePagerABC

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfPagerExport(QBetseePagerABC):
    '''
    **Export simulation configuration pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the export stack widget page
    with corresponding settings of the current simulation configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Visual export subconfiguration.
        sim_conf_visual = main_window.sim_conf.p.visual

        # Initialize all cell index-centric widgets on this page.
        main_window.sim_conf_exp_is_show_cell_indices.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=SimConfExportVisual.is_show_cell_indices,
            sim_conf_alias_parent=sim_conf_visual,
        )
        main_window.sim_conf_exp_single_cell_index.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=SimConfExportVisual.single_cell_index,
            sim_conf_alias_parent=sim_conf_visual,
        )

        # Sequence of the names of all colormaps currently registered with
        # matplotlib (in sorted lexicographic order).
        colormap_names = mplcolormap.iter_colormap_names()

        # Initialize all colormap combobox widgets on this page.
        main_window.sim_conf_exp_colormap_diverging.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=Parameters.colormap_diverging_name,
            items_iconless_text=colormap_names,
        )
        main_window.sim_conf_exp_colormap_sequential.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=Parameters.colormap_sequential_name,
            items_iconless_text=colormap_names,
        )
        main_window.sim_conf_exp_colormap_gj.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=Parameters.colormap_gj_name,
            items_iconless_text=colormap_names,
        )
        main_window.sim_conf_exp_colormap_grn.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=Parameters.colormap_grn_name,
            items_iconless_text=colormap_names,
        )
