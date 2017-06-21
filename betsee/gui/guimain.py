#!/usr/bin/env python3
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Root-level classes defining this application's graphical user interface (GUI).
'''

#FIXME: To simplify future localization efforts, all human-readable strings to
#be displayed should be filtered through the Qt translate() function. Note that
#the external "pyside2-lupdate" command will probably need to be called to
#convert raw translation files into importable Python modules.

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logs
from betsee.gui import guicache
from betsee.util.psdapp import APP_WIDGET

# ....................{ CLASSES                            }....................
class BetseeGUI(object):
    '''
    Graphical user interface (GUI) for this application, doubling as both the
    main window and root Qt widget for this application.

    Attributes
    ----------
    _main_window : BetseeMainWindow
        Main window widget for this GUI.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Generate all modules required at runtime by this GUI.
        guicache.cache_py_files()

    # ..................{ SHOWERS                            }..................
    def run(self) -> int:
        '''
        Run this GUI's main event loop and display this GUI.

        Returns
        ----------
        int
            Exit status of this event loop as an unsigned byte.
        '''

        # Main window Qt widget class for this application. Since this class
        # subclasses the custom user interface (UI) base class defined by a
        # module generated at runtime above, this importation is deferred until
        # *AFTER* this module is guaranteed to be importable.
        from betsee.gui.guimainwindow import BetseeMainWindow

        # Log this initialization.
        logs.log_info('Initiating PySide2 UI...')

        # Main window widget for this GUI.
        #
        # For safety, this window is scoped to an instance rather than global
        # variable, ensuring that this window is destroyed before the root Qt
        # application widget containing this window,
        self._main_window = BetseeMainWindow()

        # Log this display.
        logs.log_info('Displaying PySide2 UI...')

        # Run this GUI's event loop and propagate the resulting exit status to
        # our caller. This displays this window and thus all of this GUI.
        return APP_WIDGET.exec_()
