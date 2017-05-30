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
from betsee import pathtree
from betsee.gui import guicache
from betsee.lib.pyside import psdui

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

        # Generate all pure-Python modules required at runtime by this GUI.
        guicache.cache_py_files()

        # UI class generated from the XML-formatted Qt Designer file specifying
        # the non-dynamic core of the BETSEE GUI (i.e., excluding dynamic
        # signals and slots), which requires Python logic.
        # ui_class = psdui.convert_ui_file_to_class_cached(
        #     ui_filename=pathtree.get_data_ui_filename())

        #FIXME: Do something with "ui_class" here, presumably resembling:
        #
        #* Define a new "BetseeMainWindow" class inheriting from both "ui_class"
        #  and "ui_class.BASE_CLASS" in the correct order. The significant issue
        #  here is... in which scope should this class be defined? Ideally, it
        #  would be defined at the top-level scope -- but, of course, we can't
        #  do that, because we require the "ui_class" variable. We can, of
        #  course, declare this class as an inner class defined here at this
        #  indentation level -- but that, of course, would become cumbersome
        #  painfully quickly. The ideal approach is probably to acknowledge that
        #  "ui_class" is effectively a global singleton for the lifetime of this
        #  application by:
        #  * Defining a new "betsee.lib.pyside.psdglobal" submodule containing
        #    all PySide-specific global (ideally, singleton) variables. This
        #    submodule is distinct from the special "betsee.lib.pyside.psdapp"
        #    submodule, which provides *ONLY* the "APP_WIDGET" global in a safe
        #    manner *NOT* importing from BETSE submodules. The "psdglobal"
        #    submodule is under no such constraints and may (indeed, should)
        #    safely import from BETSE submodules. If not for this
        #    chicken-and-egg constraint, these two submodules would ideally be
        #    conjoined. They cannot be. Document this subtle issue...somewhere.
        #  * Declaring a "MAIN_WINDOW_UI_CLASS" global at the top-level of the
        #    "betsee.lib.pyside.psdapp" submodule initialized to "None".
        #  * Defining a set_main_window_ui_class() convenience function in that
        #    submodule setting that global, which should be called here to do
        #    so immediately. As a safety check, this function should raise an
        #    exception if that global is non-None (i.e., this function should
        #    only be called once per application).
        #  * Defining a get_main_window_ui_class() convenience function in that
        #    submodule getting that global. As a safety check, this function
        #    should raise an exception if that global is None.
        #  * Defining a new "betse.gui.guimainwindow" submodule.
        #  * Importing that submodule here *ONLY* after calling the
        #    set_main_window_ui_class() function.
        #  * In that submodule, importing
        #    "betsee.lib.pyside.psdapp" and calling the
        #    psdapp.get_main_window_ui_class() function *AT THE TOP LEVEL.*
        #    This, of course, is the key to the universe of fun.
        #  * Define the BetseeMainWindow.__init__() method to call the
        #    setupUi() method inherited from this UI class, passing itself as
        #    the only parameter. (Wacky, but that's PySide.)
        #* Instantiate this "BetseeMainWindow" class here.
