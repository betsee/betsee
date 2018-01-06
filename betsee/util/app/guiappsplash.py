#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Submodule providing the startup splash progress visualizing the current progress
of this application loading.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python, PySide2, and BETSE, and BETSEE modules.
#   This excludes all other third-party modules (mandatory or optional), whose
#   importability has yet to be validated.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtCore import Qt, QPixmap
from PySide2.QtWidgets import QSplashScreen
from betse.util.type.types import type_check
from betsee.util.app import guiapp

# ....................{ GLOBALS                            }....................
# This global is initialized by the make_splash() function called elsewhere.
GUI_APP_SPLASH = None
'''
:class:`QBetseeSplashScreen` singleton widget for this application.
'''

# ....................{ CLASSES                            }....................
class QBetseeSplashScreen(QSplashScreen):
    '''
    :class:`QSplashScreen`-based widget displaying a non-modal splash screen,
    typically used to present a multi-threaded graphical progress bar during
    time-consuming application startup.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, image_uri: str) -> None:
        '''
        Initialize this splash screen with the passed properties.

        Parameters
        ----------
        image_uri : str
            Qt-specific Uniform Resource Identifier (URI) of the single image to
            be displayed by this splash screen (e.g., ``://image/splash.svg``).
        '''

        # Initialize our superclass.
        super().__init__()

        # Application singleton, localized to avoid retaining references.
        gui_app = guiapp.get_app()

        #FIXME: Does this *REALLY* have to be rasterized and hence reduced to a
        #bitmap or can an SVG URI be encapsulated properly... somehow? The
        #answer currently appears to be "Nope!"

        # Display an in-memory image loaded from this on-disk URI.
        self.setPixmap(QPixmap(image_uri))

        # Prevent a frame (i.e., border) from being displayed around this splash
        # screen, thus displaying this screen as a "frameless window."
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        #FIXME: Is this actually required?
        # Prevent a background from being displayed under this splash screen,
        # preserving the alpha layer (i.e., transparency) in this image if any.
        self.setAutoFillBackground(False)

        # Display this splash screen *AFTER* setting all settings above.
        self.show()

        # Manually handle all outstanding GUI events. Since the main event loop
        # has yet to be started (i.e., by calling GUI_APP._exec()), event
        # handling *MUST* be performed manually.
        gui_app.processEvents()

    # ..................{ SETTERS                            }..................
    @type_check
    def set_info(self, info: str) -> None:
        '''
        Display the passed human-readable single-line string as the current
        message for this splash screen, replacing the prior such string if any.
        '''

        # Application singleton, localized to avoid retaining references.
        gui_app = guiapp.get_app()

        # Display this message.
        self.showMessage(info)

        # Manually handle all outstanding GUI events. See the __init__() method.
        gui_app.processEvents()
