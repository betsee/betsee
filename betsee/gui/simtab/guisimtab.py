#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **tabbed simulation results** (i.e., partitioning of the
simulation results into multiple pages, each displaying and controlling all
settings associated with a single result of the current simulation) facilities.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
from PySide2.QtWidgets import QMainWindow, QTabWidget
# from betse.util.io.log import logs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ CLASSES                            }....................
class QBetseeSimmerTabWidget(QBetseeObjectMixin, QTabWidget):
    '''
    :mod:`PySide2`-based tab widget containing multiple tabs, each displaying
    and controlling all settings associated with a single simulation result
    (e.g., pickled file, plot, animation) of the current simulation created by a
    single CLI-oriented simulation subcommand (e.g., ``betse plot init``).

    Attributes (Public)
    ----------
    simmer : QBetseeSimmer
        **Simulator** (i.e., :mod:`PySide2`-based object both displaying *and*
        controlling the execution of simulation-specific subcommands).

    Attributes (Private: Non-widgets)
    ----------

    Attributes (Private: Widgets)
    ----------
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator.
        '''

        # Avoid circular import dependencies.
        from betsee.gui.simtab.run.guisimrun import QBetseeSimmer

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Simulator, displaying and controlling simulation-specific subcommands.
        self.simmer = QBetseeSimmer()

        # Nullify all remaining instance variables for safety.
        # self.simmer = None


    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QMainWindow" subclass of the "betsee.gui.window.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Finalize this widget's initialization, owned by the passed main window
        widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulation subcommander.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child widgets
        (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().init()

        # Initialize all widgets concerning simulation subcommand state the
        # *BEFORE* connecting all relevant signals and slots typically expecting
        # these widgets to be initialized.
        self._init_widgets(main_window)
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (not necessarily owned by this object) whose internal
        state pertains to the high-level state of simulation subcommands.

        Parameters
        ----------
        main_window : QMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Classify all instance variables of this main window subsequently
        # required by this object.
        # self._action_make_sim     = main_window.action_make_sim

        # Initialize the simulator.
        self.simmer.init(main_window=main_window)


    @type_check
    def _init_connections(self, main_window: QMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of simulation subcommands.
        '''

        # Connect each such action to this object's corresponding slot.
        # self._action_make_sim.triggered.connect(self._make_sim)

        # Connect this object's signals to all corresponding slots.
        # self.set_filename_signal.connect(self.set_filename)

        # Set the state of all widgets dependent upon this simulation
        # subcommand state *AFTER* connecting all relavant signals and slots.
        # Initially, no simulation subcommands have yet to be queued or run.
        #
        # Note that, as this slot only accepts strings, the empty string rather
        # than "None" is intentionally passed for safety.
        # self.set_filename_signal.emit('')

        pass

    # ..................{ PROPERTIES ~ bool                  }..................
    # @property
    # def is_open(self) -> bool:
    #     '''
    #     ``True`` only if a simulation configuration file is currently open.
    #     '''
    #
    #     return self.p.is_loaded

    # ..................{ PROPERTIES ~ str                   }..................
    # @property
    # def dirname(self) -> StrOrNoneTypes:
    #     '''
    #     Absolute path of the directory containing the currently open
    #     simulation configuration file if any *or* ``None`` otherwise.
    #     '''
    #
    #     return self.p.conf_dirname

    # ..................{ EXCEPTIONS                         }..................
    # def die_unless_open(self) -> bool:
    #     '''
    #     Raise an exception unless a simulation configuration file is currently
    #     open.
    #     '''
    #
    #     if not self.is_open:
    #         raise BetseeSimConfException(
    #             'No simulation configuration currently open.')

    # ..................{ SIGNALS                            }..................
    # set_filename_signal = Signal(str)
    # '''
    # Signal passed either the absolute path of the currently open YAML-formatted
    # simulation configuration file if any *or* the empty string otherwise.
    #
    # This signal is typically emitted on the user:
    #
    # * Opening a new simulation configuration.
    # * Closing a currently open simulation configuration.
    # '''

    # ..................{ SLOTS ~ state                      }..................
    # @Slot(str)
    # def set_filename(self, filename: str) -> None:
    #     '''
    #     Slot signalled on both the opening of a new simulation configuration
    #     and closing of an open simulation configuration.
    #
    #     Parameters
    #     ----------
    #     filename : StrOrNoneTypes
    #         Absolute path of the currently open YAML-formatted simulation
    #         configuration file if any *or* the empty string otherwise (i.e., if
    #         no such file is open).
    #     '''
    #
    #     # Notify all interested slots that no unsaved changes remain, regardless
    #     # of whether a simulation configuration has just been opened or closed.
    #     self.set_dirty_signal.emit(False)

    # ..................{ SLOTS ~ action                     }..................
    # @Slot()
    # def _open_sim(self) -> None:
    #     '''
    #     Slot invoked on the user requesting that the currently open simulation
    #     configuration if any be closed and an existing external simulation
    #     configuration be opened.
    #     '''
    #
    #     # Absolute path of an existing YAML-formatted simulation configuration
    #     # file selected by the user.
    #     conf_filename = self._show_dialog_sim_conf_open()
    #
    #     # If the user canceled this dialog, silently noop.
    #     if conf_filename is None:
    #         return
    #     # Else, the user did *NOT* cancel this dialog.
    #
    #     # Close the currently open simulation configuration if any.
    #     self._close_sim()
    #
    #     # Deserialize this low-level file into a high-level configuration.
    #     self.load(conf_filename)
    #
    #     # Update the status bar *AFTER* successfully completing this action.
    #     self._status_bar.showMessage(QCoreApplication.translate(
    #         'QBetseeSimConf', 'Simulation opened.'))
