#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
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

from betse.cli.cliabc import CLIABC
from betse.cli.cliopt import CLIOptionArgStr
from betse.util.io.log import logs
from betse.util.type.types import type_check, MappingType
from betsee import guiignition, guimetadata
from betsee.util.io.log import guilogs

# ....................{ SUBCLASS                           }....................
class BetseeCLI(CLIABC):
    '''
    Command line interface (CLI) for this application.

    Attributes
    ----------
    _sim_conf_filename : StrOrNoneTypes
        Absolute or relative path of the initial YAML-formatted simulation
        configuration file to be initially opened if any *or* ``None`` otherwise
        parsed from the passed options.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self):

        # Initialize our superclass.
        super().__init__()

        # Nullify all instance variables for safety.
        self._sim_conf_filename = None

    # ..................{ SUPERCLASS ~ header                }..................
    def _show_header(self) -> None:
        guilogs.log_header()

    # ..................{ SUPERCLASS ~ properties            }..................
    @property
    def _arg_parser_top_kwargs(self) -> MappingType:

        return {
            # Human-readable multi-sentence application description.
            'description': guimetadata.DESCRIPTION,

            #FIXME: Define an epilog encouraging users requiring full access to
            #the BETSE's command-line suite of subcommands to call the "betse"
            #command instead.

            # Human-readable multi-sentence application help suffix.
            # 'epilog': SUBCOMMANDS_SUFFIX,
        }

    # ..................{ SUPERCLASS ~ options               }..................
    def _make_options_top(self) -> tuple:

        # Tuple of all default top-level options.
        options_top = super()._make_options_top()

        # Return a tuple extending this tuple with subclass-specific options.
        return options_top + (
            CLIOptionArgStr(
                long_name='--sim-conf-file',
                synopsis='simulation configuration file to initially open',
                var_name='sim_conf_filename',
                default_value=None,
            ),
        )


    def _parse_options_top(self) -> None:

        # Parse all default top-level options.
        super()._parse_options_top()

        # Initial simulation configuration file parsed from the passed options.
        self._sim_conf_filename = self._args.sim_conf_filename

    # ..................{ SUPERCLASS ~ methods               }..................
    def _ignite_app(self) -> None:

        # (Re-)initialize both BETSEE and BETSE.
        guiignition.reinit()


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
        # global variable, ensuring this GUI is destroyed before the root Qt
        # application widget containing this GUI.
        app_gui = BetseeGUI(sim_conf_filename=self._sim_conf_filename)

        #FIXME: Propagate the exit status returned by the following method call
        #as the exit status of the entire process. To do so, we'll probably need
        #to generalize the "CLIABC" superclass to provide an instance variable
        #(e.g., "self.exit_status") defaulting to None. When non-None, the
        #superclass returns this exit status rather than "SUCCESS".

        # Run this GUI's event loop and display this GUI.
        exit_status = app_gui.run()

        # Return this GUI.
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


