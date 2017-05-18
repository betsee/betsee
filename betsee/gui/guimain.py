#!/usr/bin/env python3
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Classes defining this application's graphical user interface (GUI).
'''

#FIXME: To simplify future localization efforts, all human-readable strings to
#be displayed should be filtered through the Qt translate() function.

# ....................{ IMPORTS                            }....................
from betsee import pathtree
from betsee.lib.pyside import psdui

# ....................{ GLOBALS                            }....................
#FIXME: PySide and hence presumably PySide2 as well lacks an analogue to the
#loadUiType() function. To circumvent this, consider defining our own
#loadUiType() function performing the equivalent thereof. This is low-hanging
#fruit. Since doing so on every GUI startup is presumably inefficient, however,
#this should also be improved in the long-term to perform caching: namely,
#
#* On the first execution of the GUI:
#  1. Convert the UI file referenced below into in-memory Python code.
#  2. Convert that code into a Python file, presumably cached in the current
#     dot directory for BETSE (e.g., "~/.betse/").
#* On all subsequent executions of the GUI:
#  1. Compare the time stamps of this UI file and this cached Python file.
#  2. If the time stamps are the same, reuse the latter as is.
#  3. Else, recreate the latter as above and use the newly cached file.

# ....................{ CLASSES                            }....................
class BetseeGUI(object):
    '''
    Graphical user interface (GUI) for this application, doubling as both the
    main window and root Qt widget for this application.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # UI class generated from the XML-formatted Qt Designer file specifying
        # the non-dynamic core of the BETSEE GUI (i.e., excluding dynamic
        # signals and slots), which requires Python logic.
        psdui.convert_ui_to_type(ui_filename=pathtree.get_main_ui_filename())
