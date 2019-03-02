#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **tabbed simulation results** (i.e., partitioning of the
simulation results into multiple pages, each displaying and controlling all
settings associated with a single result of the current simulation) facilities.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
from PySide2.QtWidgets import QMainWindow, QTabWidget
# from betse.util.io.log import logs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ CLASSES                           }....................
class QBetseeSimmerTabWidget(QBetseeObjectMixin, QTabWidget):
    '''
    :mod:`PySide2`-based tab widget containing multiple tabs, each displaying
    and controlling all settings associated with a single simulation result
    (e.g., pickled file, plot, animation) of the current simulation created by
    a single CLI-oriented simulation subcommand (e.g., ``betse plot init``).

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

    # ..................{ INITIALIZERS                      }..................
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
        references to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().init()

        # Initialize all widgets concerning simulation subcommand state the
        # *BEFORE* connecting all relevant signals and slots typically
        # expecting these widgets to be initialized.
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
            Initialized parent :class:`QMainWindow` widget.
        '''

        # Initialize the simulator.
        self.simmer.init(main_window=main_window)


    @type_check
    def _init_connections(self, main_window: QMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of simulation subcommands.

        Parameters
        ----------
        main_window : QMainWindow
            Initialized parent :class:`QMainWindow` widget.
        '''

        pass

    # ..................{ FINALIZERS                        }..................
    # Although the implementation of this method is currently trivial, this
    # method will be generalized (at some later date) to transparently halt
    # work being asynchronously performed in additional tabs (e.g., animation
    # encoding export) and thus should be preserved as is for now.
    def halt_work(self) -> None:
        '''
        Schedule all currently running simulation work if any for immediate
        and thus possibly non-graceful termination *or* silently reduce to a
        noop otherwise (i.e., if no simulation work is currently running).

        Caveats
        ----------
        This method may induce data loss or corruption in simulation output.
        In theory, this should only occur in edge cases in which the current
        simulator worker fails to gracefully stop within a sensible window of
        time. In practice, this implies that this method should *only* be
        called when otherwise unavoidable (e.g., at application shutdown).

        See Also
        ----------
        :meth:`QBetseeSimmer.halt_work`
            Further details.
        '''

        # Halt the simulator if currently running.
        self.simmer.halt_work()
