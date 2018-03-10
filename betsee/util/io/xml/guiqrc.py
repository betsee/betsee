#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for integrating :mod:`PySide2` widget classes with
XML-formatted Qt resource collection (QRC) files exported by the external Qt
Designer application.
'''

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logs
from betse.util.path import files, pathnames
from betse.util.path.command import cmdrun, cmds
from betse.util.type.types import type_check

# ....................{ CONVERTERS                         }....................
@type_check
def convert_qrc_to_py_file_if_able(qrc_filename: str, py_filename: str) -> None:
    '''
    Convert the XML-formatted file with the passed ``.qrc``-suffixed filename
    *and* all binary resources referenced by this file exported by the external
    Qt Designer GUI into the :mod:`PySide2`-based Python module with the passed
    ``.py``-suffixed filename if capable of doing so *or* log a non-fatal
    warning and return otherwise.

    Dependencies
    ----------
    This function requires the optional third-party dependency ``pyside2-tools``
    distributed by The Qt Company. Specifically, this high-level function wraps
    the low-level ``pyside2-rcc`` command installed by this dependency with a
    human-usable API.

    If this command is unavailable, this function logs a non-fatal warning and
    returns *without* raising a fatal exception.

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

    # If the optional third-party dependency required by this function is
    # unavailable, log a non-fatal warning and return.
    if not cmds.is_command('pyside2-rcc'):
        logs.log_warning(
            'Skipping! Command "pyside2-rcc" not found, '
            'probably due to "pyside2-tools" not being installed.')
        return

    # If this output file is unwritable, log a non-fatal warning and return.
    if not files.is_exists_writable(py_filename):
        logs.log_warning(
            'Skipping! PySide2 module "%s" unwritable, '
            'probably due to a system-wide installation.', py_filename)
        return

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

    #FIXME: The contents of this output "py_filename" should additionally be
    #opened for writing and prefixed by a shebang line running the active Python
    #interpreter. See the "guiui" submodule for relevant logic.
