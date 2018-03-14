#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Concrete subclasses defining this application's command line interface (CLI).
'''

#FIXME: Display a splash screen in the BetseeCLI.__init__() method. Fortunately,
#Qt 5 makes this absurdly simple via the stock "QSplashScreen" class -- which
#comes self-provisioned with multi-threading capability, preventing us from
#having to interface with multi-threading merely to display a splash screen --
#which is pretty awesome, actually.
#
#It's trivially simple to use. The "QSplashScreen" documentation actually turns
#out to be the most useful help here. In particular, the workflow appears to
#resemble:
#
#* Define a new "betsee.util.app.guiappsplash" submodule containing:
#
#    from PySide2.QtCore import QPixmap
#    from PySide2.QtWidgets import QSplashScreen
#    from betsee.util.app.guiapp import APP_GUI
#
#    GUI_APP_SPLASH = None
#    '''
#    Singleton :class:`QSplashScreen`-based widget
#    '''
#
#    class QBetseeSplashScreen(QSplashScreen):
#        '''
#        :class:`QSplashScreen`-based widget displaying a non-modal splash
#        screen, typically used to present a multi-threaded loading screen
#        during time-consuming application startup.
#        '''
#
#        @type_check
#        def __init__(self, image_uri: str) -> None:
#
#            pixmap = QPixmap(image_uri)
#            super().__init__(pixmap)
#            self.show()
#            APP_GUI.processEvents()
#
#        def set_info(self, info: str) -> None:
#            '''
#            Display the passed human-readable single-line string as the
#            current progress message for this splash screen.
#            '''
#
#            self.showMessage(info)
#            APP_GUI.processEvents()
#
#
#* In this submodule, improve the existing
#
#    from betsee.util.widget import guisplash
#    from betsee.util.widget.guisplash import QBetseeSplashScreen
#
#
#    def __init__(self) -> None:
#
#        #FIXME: Non-ideal way to set a singleton, but... meh.
#        guisplash.GUI_SPLASH = QBetseeSplashScreen(
#            image_uri=':/GUI_SPLASH.png')
#
#        # Loading some items
#        guisplash.GUI_SPLASH.set_info("Loaded modules")
#
#        # Establishing connections
#        guisplash.GUI_SPLASH.set_info("Established connections")
#
#        #FIXME: This obviously needs to happen elsewhere. Since "GUI_SPLASH" is
#        #a globally accessible singleton, this shouldn't be an issue. *shrug*
#        # Create the main window.
#        main_window = QMainWindow()
#        guisplash.GUI_SPLASH.finish(main_window)
#
#        # Populate and show the main window.
#        main_window.show()
#        APP_GUI.exec_()
#        guisplash.GUI_SPLASH = None
#
#It's all pretty trivial stuff, frankly. Awesomeness!

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and application modules, including both
#   BETSEE and BETSE modules.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from betse.util.cli.cliabc import CLIABC
from betse.util.cli.cliopt import CLIOptionArgStr
from betse.util.io.log import logs
from betse.util.type.types import type_check, ModuleType, SequenceTypes
from betsee import guiignition, guimetadata
from betsee.lib import guilibs

# ....................{ SUBCLASS                           }....................
class BetseeCLI(CLIABC):
    '''
    Command line interface (CLI) for this application.

    Attributes
    ----------
    _sim_conf_filename : StrOrNoneTypes
        Absolute or relative filename of the initial YAML-formatted simulation
        configuration file to be initially opened by this application's GUI if
        any *or* ``None`` otherwise. This filename is parsed from command-line
        options passed by the current user.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self):

        # Initialize our superclass.
        super().__init__()

        # Nullify all instance variables for safety.
        self._sim_conf_filename = None

    # ..................{ SUPERCLASS ~ properties : optional }..................
    # The following properties *MAY* be implemented by subclasses.

    @property
    def _is_option_matplotlib_backend(self) -> bool:
        '''
        ``False``, preventing this CLI from exposing the
        ``--matplotlib-backend`` option and hence permitting users to externally
        specify an arbitrary matplotlib backend at the command line.

        Of necessity, this Qt-based application strictly requires a single
        Qt-based matplotlib backend (e.g., ``Qt5Agg``).
        '''

        return False

    # ..................{ SUPERCLASS ~ properties : mandatory}..................
    # The following properties *MUST* be implemented by subclasses.

    @property
    def _help_epilog(self) -> str:

        return '''
To simulate any simulation produced by this GUI at the command line, consider
running the "betse" command underlying this GUI instead. For example, to
seed, initialize, and then simulate such a simulation in the current directory:

;    betse seed sim_config.yaml
;    betse init sim_config.yaml
;    betse  sim sim_config.yaml
'''


    @property
    def _module_ignition(self) -> ModuleType:

        return guiignition


    @property
    def _module_metadata(self) -> ModuleType:

        return guimetadata

    # ..................{ SUPERCLASS ~ igniters              }..................
    def _init_app_libs(self) -> None:

        # Initialize all mandatory runtime dependencies of this application,
        # including both BETSE and BETSEE.
        #
        # Note that the superclass _init_app_libs() method is intentionally
        # *NOT* called, as that method sets the matplotlib backend. While doing
        # so is typically desirable, a chicken-and-egg conflict between Qt and
        # matplotlib complicates the initialization of both.
        #
        # See the body of the function called here for further details.
        guilibs.reinit()

    # ..................{ SUPERCLASS ~ options               }..................
    def _make_options_top(self) -> SequenceTypes:

        # Sequence of all default top-level options.
        options_top = super()._make_options_top()

        # Return a list extending this sequence with subclass-specific options.
        return list(options_top) + [
            CLIOptionArgStr(
                long_name='--sim-conf-file',
                synopsis='simulation configuration file to initially open',
                var_name='sim_conf_filename',
                default_value=None,
            ),
        ]


    def _parse_options_top(self) -> None:

        # Parse all default top-level options.
        super()._parse_options_top()

        # Initial simulation configuration file parsed from the passed options.
        self._sim_conf_filename = self._args.sim_conf_filename

    # ..................{ SUPERCLASS ~ methods               }..................
    def _do(self) -> object:
        '''
        Implement this command-line interface (CLI) by running the corresponding
        graphical user interface (GUI), returning this interface to be memory
        profiled when the ``--profile-type=size`` CLI option is passed.
        '''

        # Defer imports *NOT* guaranteed to exist at this module's top-level.
        from betsee.gui.guimain import BetseeGUI

        # Application GUI.
        #
        # For safety, this GUI is scoped to a local rather than instance or
        # global variable, ensuring this GUI is implicitly destroyed by Python
        # before the root Qt application widget containing this GUI.
        app_gui = BetseeGUI(sim_conf_filename=self._sim_conf_filename)

        # Run this GUI's event loop and display this GUI, propagating the
        # returned exit status as this application's exit status.
        self._exit_status = app_gui.run()

        # Return this GUI for optional profiling purposes.
        return app_gui


    @type_check
    def _handle_exception(self, exception: Exception) -> None:

        # Defer to superclass handling, which typically logs this exception.
        super()._handle_exception(exception)

        # Additionally attempt to...
        try:
            # Import PySide2.
            from betsee.util.io import guierr

            # Display a PySide2-based message box displaying this exception.
            guierr.show_exception(exception)
        # If PySide2 or any other module indirectly imported above is
        # unimportable, print this exception message but otherwise ignore this
        # exception. Why? Because we have more significant fish to fry.
        except ImportError as import_error:
            logs.log_error(str(import_error))
