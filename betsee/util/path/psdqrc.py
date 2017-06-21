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
# from PySide2 import QtWidgets
from betse.util.io.log import logs
from betse.util.path import files, pathnames
from betse.util.path.command import cmdrun
from betse.util.type.types import type_check
# from betsee.exceptions import BetseePySideUICException

# ....................{ CONVERTERS                         }....................
@type_check
def convert_qrc_to_py_file(qrc_filename: str, py_filename: str) -> None:
    '''
    Convert the XML-formatted file with the passed ``.qrc``-suffixed filename
    and all binary resources referenced by this file exported by the external Qt
    Designer GUI into the :mod:`PySide2`-based Python module with the passed
    ``.py``-suffixed filename.

    This high-level function wraps the low-level ``pyside2-rcc`` command
    provided by the external ``pyside2-tools`` project.

    Parameters
    ----------
    qrc_filename : str
        Absolute or relative path of the input ``.qrc``-suffixed file.
    py_filename : str
        Absolute or relative path of the output ``.py``-suffixed file.
    '''

    # Log this conversion attempt.
    logs.log_info(
        'Generating PySide2 module "%s" from "%s"...',
        pathnames.get_basename(py_filename),
        pathnames.get_basename(qrc_filename))

    # If this input file does *NOT* exist, raise an exception.
    files.die_unless_file(qrc_filename)

    # If these files do *NOT* have the expected filetypes, raise an exception.
    pathnames.die_unless_filetype_equals(pathname=qrc_filename, filetype='qrc')
    pathnames.die_unless_filetype_equals(pathname=py_filename,  filetype='py')

    # Convert this input file to this output file or raise an exception if
    # unsuccessful. For debuggability, this command's stdout and stderr is
    # redirected to this application's stdout, stderr, and logging file handles.
    cmdrun.log_output_or_die(
        command_words=('pyside2-rcc', '-o', py_filename, qrc_filename))
