#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for integrating :mod:`PySide2` widget classes with
XML-formatted user interface (UI) files exported by the external Qt Designer
application.
'''

# ....................{ IMPORTS                            }....................
from PySide2 import QtWidgets
from betse.util.io import iofiles
from betse.util.io.log import logs
from betse.util.path import files, pathnames
from betse.util.type.types import type_check
from betsee import metadata
from betsee.exceptions import BetseePySideException
from io import StringIO
from pyside2uic.Compiler.compiler import UICompiler

# ....................{ GLOBALS                            }....................
# To avoid conflict with PySide2-generated attribute names, obfuscate this
# global's name in an application-specific manner.
BASE_CLASSES_GLOBAL_NAME = '__{}_BASE_CLASSES'.format(metadata.NAME)
'''
Unqualified name of the application-specific global appended to the Python code
generated by the :func:`convert_ui_to_py_file` function.

This global declares the sequence of all base classes that the main window Qt
widget subclass for this application is expected to subclass (in order).
'''

# ....................{ CONVERTERS                         }....................
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

@type_check
def convert_ui_to_py_file(ui_filename: str, py_filename: str) -> None:
    '''
    Convert the XML-formatted file with the passed ``.ui``-suffixed filename
    exported by the external Qt Designer GUI into the :mod:`PySide2`-based
    Python module with the passed ``.py``-suffixed filename.

    This high-level function wraps the low-level :meth:`UICompiler.compileUi`
    method with a useful and user-friendly interface.

    Design
    ----------
    This function silently overwrites this output file with the dynamically
    compiled contents of a pure-Python model declaring:

    * A custom helper class defining the following methods:

      * ``setupUi()``, accepting an instance of the :mod:`PySide2` widget base
        class listed as the last item of the global sequence described below and
        customizing this widget as specified by this input UI file.
      * ``retranslateUi()``, accepting a similar instance and translating all
        strings displayed by this widget from their default language (typically,
        English) into the locale of the current user.

    * A global sequence variable whose:

      * Name is the value of the
        :data:`BASE_CLASSES_GLOBAL_NAME` global string variable,
      * Value is the sequence of all base classes that the main Qt window widget
        class for this application *must* subclass (in order):

        #. The custom helper class described above.
        #. The :mod:`PySide2` widget base class of the object to be passed to
           all methods defined by this class (e.g., ``setupUi()``). These
           methods do *not* validate this to be the case but do raise
           non-human-readable exceptions when passed objects that are *not*
           instances of this base class. This base class is defined by this
           input UI file and is typically one of the following:

           * :class:`PySide2.QWidget.QDialog`.
           * :class:`PySide2.QWidget.QWidget`.
           * :class:`PySide2.QWidget.QMainWindow`.

    This function provides a :mod:`PySide2`-specific implementation of the
    PyQt-specific :func:`PyQt5.uic.loadUiType` function, albeit with a more
    typesafe API. For unknown reasons (presumably laziness), :mod:`PySide2`
    lacks an analogue to this function.

    For equally unknown reasons, the class returned by that function is commonly
    referred to as the "form class" in most Qt documentation. This class has no
    relation to the :class:`PySide2.QLayout.QFormLayout` base class and is thus
    arguably *not* a "form class." For disambiguity, we prefer to refer to this
    class as simply the "generated UI class."

    Parameters
    ----------
    ui_filename : str
        Absolute or relative path of the input ``.ui``-suffixed file.
    py_filename : str
        Absolute or relative path of the output ``.py``-suffixed file.

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

    # Log this conversion attempt.
    logs.log_info(
        'Generating PySide2 module "%s" from "%s"...',
        pathnames.get_basename(py_filename),
        pathnames.get_basename(ui_filename))

    # If this input file does *NOT* exist, raise an exception.
    files.die_unless_file(ui_filename)

    # If these files do *NOT* have the expected filetypes, raise an exception.
    pathnames.die_unless_filetype_equals(pathname=ui_filename, filetype='ui')
    pathnames.die_unless_filetype_equals(pathname=py_filename, filetype='py')

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
    ui_code_metadata = UICompiler().compileUi(
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
        raise BetseePySideException(
            title='PySide2 UI Compiler Error',
            synopsis='PySide2 widget base class "{}" not found.'.format(
                ui_base_class_name))

    # Append an application-specific global to the Python code generated above,
    # declaring the sequence of all base classes that the main Qt window widget
    # class for this application *MUST* subclass (in order). In particular, note
    # that the base Qt widget class is subclassed last and thus remains the
    # "parent" base class of this multiple inheritance.
    ui_code_str.write('''
from QtWidgets import {base_class}
{var_name} = ({form_class}, {base_class})
'''.format(
    var_name=BASE_CLASSES_GLOBAL_NAME,
    form_class=ui_form_class_name,
    base_class=ui_base_class_name,))

    # Overwrite this output module with the contents of this string buffer.
    iofiles.write_file_to_filename(
        input_file=ui_code_str,
        output_filename=py_filename,
        is_overwritable=True,
    )
