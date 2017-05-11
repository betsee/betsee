#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for PySide2, a mandatory runtime dependency.
'''

# ....................{ IMPORTS                            }....................
import pyside2uic
from betse.util.path import files, paths
from betse.util.type.types import type_check
# from io import StringIO
# from xml.etree import ElementTree

# ....................{ CONVERTERS                         }....................
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
#
#For relevant code doing the first part above under PySide and Python 2.7, see:
#    https://gist.github.com/mstuttgart/bc246b25b8e0f7edd743
#
#For relevant code partially doing the second part, see the
#pyside2uic.compileUiDir() utility function.
#FIXME: Given this function, the canonical means of defining the main window
#class appears to be:
#
#    from QtGui import QWidget
#    from betsee import pathtree
#    from betsee.lib.pyside import pysides
#
#    class BetseeWindow(QWidget):
#
#        # ..................{ INITIALIZERS                       }..................
#        def __init__(self, *args, **kwargs) -> None:
#
#            # Initialize our superclass with all passed parameters.
#            super().__init__(*args, **kwargs)
#
#            #FIXME: Define the pathtree.get_ui_filename() function.
#            #FIXME: Can the "ui" parameter be privatized? If so, please do it so.
#            self.ui, _ = pysides.convert_ui_to_py_file(
#                ui_filename=pathtree.get_ui_filename(),
#                py_filename=pathtree.get_cache_ui_py_filename().
#            )
#            self.ui.setupUi(self)
#
#Consider shifting the above logic into a new "betse.gui.mainwindow" submodule.
#FIXME: Validate this file to exist.
#FIXME: Return a custom class instance rather than a 2-tuple.

@type_check
def convert_ui_to_types(
    ui_filename: str,
) -> tuple:
    '''
    Deserialize the Qt Designer User Interface (UI) from the XML-formatted file
    with the passed ``.ui``-suffixed filename into a 2-tuple ``(FormClass,
    BaseClass)`` providing PySide2 classes encapsulating this UI.

    This utility function provides a PySide2-specific implementation of the
    PyQt-specific :func:`PyQt5.uic.loadUiType` function.

    Parameters
    ----------
    ui_filename : str
        Absolute or relative path of the input
    '''

    #FIXME: Call the convert_ui_to_py_file() function defined below.
    pass


#FIXME: Actually, this would probably be more usefully refactored to convert the
#passed UI file into a pickled file providing the 2-tuple of the desired form
#and base classes, as this latter file will be more efficiently deserialized.
#The filetype of this file should probably be something resembling ".betseui",
#though we needn't enforce that here.. We probably won't want to gzip this file,
#unless space truly does become a concern here.
@type_check
def convert_ui_to_py_file(
    ui_filename: str,
    py_filename: str,
) -> tuple:
    '''
    Deserialize the Qt Designer User Interface (UI) from the XML-formatted file
    with the passed ``.ui``-suffixed filename into the Python 3-formatted file
    with the passed ``.py``-suffixed filename.

    Parameters
    ----------
    ui_filename : str
        Absolute or relative path of the input ``.ui``-suffixed filename.
    py_filename : str
        Absolute or relative path of the output ``.py``-suffixed filename.
    '''

    # If this input file does *NOT* exist, raise an exception.
    files.die_unless_file(ui_filename)

    # If this output file already exists, raise an exception.
    paths.die_if_path(py_filename)

    # If either file does *NOT* have the expected filetype, raise an exception.
    paths.die_unless_filetype_equals(pathname=ui_filename, filetype='ui')
    paths.die_unless_filetype_equals(pathname=py_filename, filetype='py')

    # Convert this ".ui" file into this ".py" file.
    pyside2uic.compileUi(uifile=ui_filename, pyfile=py_filename)
