#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for integrating :mod:`PySide2` widget classes with
XML-formatted Qt resource collection (QRC) files exported by the external Qt
Designer application.
'''

# ....................{ IMPORTS                            }....................
from PySide2 import QtWidgets
from betse.util.path import files, pathnames
from betse.util.type.types import type_check
from betsee.exceptions import BetseePySideUICException
from io import StringIO
from pyside2uic.Compiler.compiler import UICompiler

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
#    from PySide2.QtWidgets import QMainWindow
#    from betsee import pathtree
#    from betsee.lib.pyside import pysides
#
#    class BetseeMainWindow(QMainWindow):
#
#        # ..................{ INITIALIZERS                       }..................
#        def __init__(self, *args, **kwargs) -> None:
#
#            # Initialize our superclass with all passed parameters.
#            super().__init__(*args, **kwargs)
#
#            self._ui = pysides.convert_ui_to_type(
#                ui_filename=pathtree.get_ui_filename(),
#            )
#            self._ui.setupUi(self)
#
#Consider shifting the above logic into a new "betse.gui.mainwindow" submodule.

#FIXME: Define and docstring us up. Ideally, this method should convert the
#passed UI file into a pickled file providing the desired form class, as this
#latter file will be more efficiently deserialized. The filetype of this file
#should probably be something resembling ".betseui". We probably won't want to
#gzip this file, unless space truly does become a concern here.
#
#The absolute path of this file should be given by the
#pathtree.get_cache_ui_py_filename() method. This path need *NOT* be passed by
#callers; simply use this path internally in this function.

@type_check
def convert_ui_to_type_cached(ui_filename: str) -> type:
    '''
    '''

    #FIXME: Call the convert_ui_to_type() function defined below.
    pass


@type_check
def convert_qrc_file_to_py(ui_filename: str) -> type:
    '''
    Helper class generated from the XML-formatted file with the passed
    ``.ui``-suffixed filename exported by the external Qt Designer application.

    This class defines only the following attributes:

    * The ``BASE_CLASS`` class attribute, providing the :mod:`PySide2` widget
      base class of the object passed to the ``setupUi()`` method. While this
      method does *not* technically validate this to be the case, this method
      typically raises non-human-readable exceptions when passed objects that
      are *not* instances of this base class. This base class is defined by this
      file and is typically one of the following:
      * :class:`PySide2.QWidget.QDialog`.
      * :class:`PySide2.QWidget.QWidget`.
      * :class:`PySide2.QWidget.QMainWindow`.
    * The ``setupUi()`` method, accepting a widget instance of this
      ``BASE_CLASS`` and returning ``None``. This method customizes this
      widget in the manner specified by this file.
    * The ``retranslateUi()`` method, accepting a widget instance of this
      ``BASE_CLASS`` and returning ``None``. This method translates all strings
      displayed by this widget from their default language (typically, English)
      into the locale of the current user.

    This function provides a :mod:`PySide2`-specific implementation of the
    PyQt-specific :func:`PyQt5.uic.loadUiType` function, albeit with a more
    typesafe API. For unknown reasons (presumably laziness), :mod:`PySide2`
    lacks an analogue to this function.

    Nomenclature
    ----------
    For unknown reasons, the class returned by this function is commonly
    referred to as the "form class" in most Qt documentation. This class has no
    relation to the :class:`PySide2.QLayout.QFormLayout` base class and is thus
    arguably *not* a "form class." For disambiguity, we prefer to refer to this
    class as simply a "generated UI class."

    Parameters
    ----------
    ui_filename : str
        Absolute or relative path of the input ``.ui``-suffixed filename.

    Returns
    ----------
    type
        UI class generated from the XML-formatted file with this filename
        exported by the external Qt Designer application.

    See Also
    ----------
    http://pyqt.sourceforge.net/Docs/PyQt5/designer.html
        :mod:`PyQt5`-specific documentation detailing this conversion. Although
        :mod:`PyQt5`-specific, this documentation probably serves as the
        canonical resource for understanding this function's internal behaviour.
    '''

    # If this file does *NOT* exist, raise an exception.
    files.die_unless_file(ui_filename)

    # If this file does *NOT* have the expected filetype, raise an exception.
    pathnames.die_unless_filetype_equals(pathname=ui_filename, filetype='qrc')
