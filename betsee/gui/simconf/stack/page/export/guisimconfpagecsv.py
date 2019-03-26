#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**CSV simulation configuration pager** (i.e., :mod:`PySide2`-based controller
for stack widget pages specific to comma-separated value (CSV) exports)
functionality.
'''

#FIXME: Implement this submodule, which currently only serves as a placeholder
#facade implementation to avoid raising disruptive exceptions at runtime.

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
# from betse.science.enum.enumconf import CellLatticeType
# from betse.util.io.log import logs
from betse.util.type.iterable import sequences
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlpageabc import (
    QBetseePagerABC, QBetseePagerItemizedABC)

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfPagerCSV(QBetseePagerABC):
    '''
    **CSV exports simulation configuration pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the stack widget page for
    *all* comma-separated value (CSV) exports with corresponding settings of
    the current simulation configuration).
    '''

    # ..................{ INITIALIZERS                      }..................
    #FIXME: Initialize all widgets (if any) on this page.
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all widgets on this page.
        # main_window.sim_conf_time_init_total.init(
        #     sim_conf=sim_conf, sim_conf_alias=Parameters.init_time_total)


class QBetseeSimConfPagerCSVExport(QBetseePagerItemizedABC):
    '''
    **CSV export simulation configuration pager** (i.e., :mod:`PySide2`-based
    controller connecting all editable widgets of the stack widget page for the
    currently selected comma-separated value (CSV) export with corresponding
    settings of the current simulation configuration).

    **This controller implements the well-known flyweight design pattern.**
    Specifically, this single controller is shared between the zero or more CSV
    exports configured for this simulation and hence *cannot* be implicitly
    initialized at application startup. Instead, this controller is explicitly
    reinitialized in an on-the-fly manner immediately before this page is
    displayed to edit a single such export.
    '''

    # ..................{ INITIALIZERS                      }..................
    #FIXME: Excise if unneeded, which appears likely.
    # @type_check
    # def init(self, main_window: QMainWindow) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().init(main_window)
    #
    #     # Simulation configuration state object.
    #     sim_conf = main_window.sim_conf
    #
    #     # Initialize all widgets on this page.
    #     main_window.sim_conf_space_intra_cell_radius.init(
    #         sim_conf=sim_conf, sim_conf_alias=Parameters.cell_radius)


    #FIXME: Reinitialize all remaining widgets (if any) on this page.
    @type_check
    def reinit(self, main_window: QMainWindow, list_item_index: int) -> None:

        # CSV export currently controlled by this pager.
        csv_export = sequences.get_index(
            sequence=main_window.sim_conf.csv.csvs_after_sim,
            index=list_item_index)

        # Type of this CSV export.
        csv_export_cls = type(csv_export)

        #FIXME: Obtain this sequence from the
        #"from betse.science.pipe.export.pipeexpcsv import SimPipeExportCSVs"
        #pipeline. To do so, we'll probably want to define a new
        #SimPipeABC.iter_runners_metadata_kind() iterator returning a
        #*SEQUENCE* of the "kind" instance variables of all runner metadata (in
        #sorted lexicographic order). Trivial to define, happily.

        # Sequence of the names of all colormaps currently registered with
        # matplotlib (in sorted lexicographic order).
        # colormap_names = mplcolormap.iter_colormap_names()

        # Widget editing this CSV export's name.
        widget_name = main_window.get_widget(
            widget_name='sim_conf_csv_item_name')

        # Initialize all general-purpose widgets on this page.
        widget_name.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=csv_export_cls.name,
            sim_conf_alias_parent=csv_export,
            is_reinitable=True,
        )
