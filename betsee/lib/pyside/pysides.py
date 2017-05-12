#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for :mod:`PySide2`, a mandatory runtime
dependency.
'''

# ....................{ IMPORTS                            }....................
from PySide2 import QtWidgets
from betse.exceptions import BetseePySideUICException
from betse.util.path import files, paths
from betse.util.type.types import type_check
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
#            #FIXME: Define the pathtree.get_ui_filename() function.
#            #FIXME: Can the "ui" parameter be privatized? If so, please do it so.
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
def convert_ui_to_type(ui_filename: str) -> type:
    '''
    UI class generated from the XML-formatted file with the passed
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
    paths.die_unless_filetype_equals(pathname=ui_filename, filetype='ui')

    # Title of all exceptions explicitly raised below.
    EXCEPTION_TITLE = 'PySide2 UI Compiler Error'

    # File-like string buffer containing the Python code converted from this
    # file to be subsequently evaluated.
    ui_code_str = StringIO()

    # Dictionary of high-level metadata describing the high-level types produced
    # by converting this file into this string buffer, containing the following
    # key strings:
    #
    # * "baseclass", whose value is the name of the PySide2-specific widget base
    #   class that objects passed to the setupUi() and retranslateUi() methods
    #   of the generated UI class are required to be instances of.
    # * "uiclass", whose value is the name of the generated UI class defining
    #   the setupUi() and retranslateUi() methods.
    # * "widgetname", whose value is... an unknown string. (Not our fault.)
    #
    # See the UICompiler.compileUi() method implementation for details.
    #
    # Note that most online examples call the slightly higher-level
    # pyside2uic.compileUi() function internally calling the lower-level
    # UICompiler.compileUi() method in the exact same manner as below. The
    # former has significant disadvantages and is thus ignored in favour of the
    # latter. In particular, the pyside2uic.compileUi() function:
    #
    # * Does *NOT* return the dictionary returned by the UICompiler.compileUi()
    #   method required below. While the contents of this dictionary are
    #   technically reverse engineerable by manually parsing the XML of this
    #   ".ui" file for the corresponding elements (e.g., via the
    #   "xml.etree.ElementTree" package), doing so needlessly incurs space,
    #   time, and code complexity costs. Due presumably to path dependency, most
    #   online examples (insanely) do so.
    # * Adds no meaningful advantages over the UICompiler.compileUi() method for
    #   most common cases, including this case.
    #
    # In short, the pyside2uic.compileUi() function is useless and no one should
    # ever call it.
    ui_code_metadata = UICompiler.compileUi(
        input_stream=ui_filename,
        output_stream=ui_code_str,

        # Force all generated imports to be absolute rather than relative.
        from_imports=False,
    )

    # Name of the custom class to be generated.
    ui_form_class_name = ui_code_metadata['uiclass']

    # Name of the PySide2 base class expected by methods of this custom class.
    ui_base_class_name = ui_code_metadata['baseclass']

    # This base class or "None" if no such class exists.
    ui_base_class = getattr(QtWidgets, ui_base_class_name, None)

    # If no such base class exists, raise an exception.
    if ui_base_class is None:
        raise BetseePySideUICException(
            title=EXCEPTION_TITLE,
            synopsis='PySide2 widget base class "{}" not found.'.format(
                ui_base_class_name))

    # Dictionary of all global attributes both passed as input to and defined as
    # output from the subsequent evaluation of this Python code.
    ui_code_dict = {}

    # Evaluate this Python code into this dictionary.
    exec(ui_code_str, ui_code_dict)

    # If this evaluation generated no such custom class, raise an exception.
    if ui_form_class_name not in ui_code_dict:
        raise BetseePySideUICException(
            title=EXCEPTION_TITLE,
            synopsis='PySide2 UI form class "{}" not found.'.format(
                ui_form_class_name),
            exegesis=('Generated code expected to contain this class:\n\n' +
                ui_code_str),
        )

    # Custom class generated by this evaluation.
    ui_form_class = ui_code_dict[ui_form_class_name]

    # Define the "BASE_CLASS" class attribute on this class.
    ui_form_class.BASE_CLASS = ui_base_class

    # Return this class.
    return ui_form_class
