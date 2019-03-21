#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Export simulation configuration pager** (i.e., :mod:`PySide2`-based
controller for stack widget pages specific to export settings) functionality.
'''

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

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Sequence of the names of all colormaps currently registered with
        # matplotlib (in sorted lexicographic order).
        colormap_names = mplcolormap.iter_colormap_names()

        #FIXME: Initialize all remaining widgets *AFTER* this is worky.

        # Initialize all colormap combobox widgets on this page.
        main_window.sim_conf_exp_colormap_diverging.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.colormap_diverging_name,
            items_iconless_text=colormap_names,
        )
