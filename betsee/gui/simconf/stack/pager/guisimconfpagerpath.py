#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based stack widget page controllers specific to paths.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import QMainWindow
from betse.science.parameters import Parameters
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfPathStackedWidgetPager(QBetseeControllerABC):
    '''
    :mod:`PySide2`-based stack widget page controller, connecting all editable
    widgets of the paths page with the corresponding low-level settings of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Simulation configuration state object.
        sim_conf = main_window.sim_conf

        # Initialize all seed widgets on this page.
        main_window.sim_conf_path_seed_pick_file_line.init(
            sim_conf=sim_conf, sim_conf_alias=Parameters.seed_pickle_basename)

        # Initialize all initialization widgets on this page.
        main_window.sim_conf_path_init_pick_file_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.init_pickle_basename,
        )
        main_window.sim_conf_path_init_pick_dir_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.init_pickle_dirname_relative,
            push_btn=main_window.sim_conf_path_init_pick_dir_btn,
        )
        main_window.sim_conf_path_init_exp_dir_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.init_export_dirname_relative,
            push_btn=main_window.sim_conf_path_init_exp_dir_btn,
        )

        # Initialize all simulation widgets on this page.
        main_window.sim_conf_path_sim_pick_file_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.sim_pickle_basename,
        )
        main_window.sim_conf_path_sim_pick_dir_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.sim_pickle_dirname_relative,
            push_btn=main_window.sim_conf_path_sim_pick_dir_btn,
        )
        main_window.sim_conf_path_sim_exp_dir_line.init(
            sim_conf=sim_conf,
            sim_conf_alias=Parameters.sim_export_dirname_relative,
            push_btn=main_window.sim_conf_path_sim_exp_dir_btn,
        )
