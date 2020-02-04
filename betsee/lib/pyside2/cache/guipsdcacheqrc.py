#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level support facilities for integrating :mod:`PySide2` widget classes
with XML-formatted Qt resource collection (QRC) files exported by the external
Qt Designer application.
'''

# ....................{ IMPORTS                           }....................
from betse.util.io.log import logs
from betse.util.path import files, pathnames, paths
from betse.util.os.command import cmdrun, cmds
from betse.util.type.types import type_check

# ....................{ CONVERTERS                        }....................
@type_check
def convert_qrc_to_py_file(qrc_filename: str, py_filename: str) -> None:
    '''
    Convert the XML-formatted file with the passed ``.qrc``-suffixed filename
    *and* all binary resources referenced by this file exported by the external
    Qt Designer GUI into the :mod:`PySide2`-based Python module with the passed
    ``.py``-suffixed filename if capable of doing so *or* log a non-fatal
    warning and return otherwise.

    This function requires the optional third-party dependency
    ``pyside2-tools`` distributed by The Qt Company. Specifically, this
    high-level function wraps the low-level ``pyside2-rcc`` command installed
    by that dependency with a human-usable API.

    Parameters
    ----------
    qrc_filename : str
        Absolute or relative filename of the input ``.qrc``-suffixed file.
    py_filename : str
        Absolute or relative filename of the output ``.py``-suffixed file.
    '''

    # Log this conversion attempt.
    logs.log_info(
        'Synchronizing PySide2 module "%s" from "%s"...',
        pathnames.get_basename(py_filename),
        pathnames.get_basename(qrc_filename))

    # If "rcc" is *NOT* in the current ${PATH}, raise an exception.
    cmds.die_unless_command(
        filename='rcc',
        reason='(e.g., as package "pyside2-tools" not installed).')

    # If this input file does *NOT* exist, raise an exception.
    files.die_unless_file(qrc_filename)

    # If this output file is unwritable, raise an exception.
    paths.die_unless_writable(py_filename)

    # If these files do *NOT* have the expected filetypes, raise an exception.
    pathnames.die_unless_filetype_equals(pathname=qrc_filename, filetype='qrc')
    pathnames.die_unless_filetype_equals(pathname=py_filename,  filetype='py')

    # Convert this input file to this output file if successful *OR* raise an
    # exception otherwise (i.e., if unsuccessful), redirecting output to this
    # application's stdout, stderr, and logging file handles for debuggability.
    cmdrun.log_output_or_die(
        command_words=(
            'rcc',
            # Avoid attempting to perform C++-specific compression of media
            # files referenced by the input QRC file passed below. Since these
            # files are *ALL* vector- rather than raster-based, compression
            # yields no tangible benefits and incurs non-negligible costs at
            # runtime for both this function call and at application startup.
            '--compress-algo', 'none',
            # Output something other than nothing (the default).
            '--verbose',
            # Output Python 3.x rather than C++ (the default).
            '--generator', 'python',
            # Output to this file rather than stdout (the default).
            '--output', py_filename,
            # Input the contents of this QRC file.
            qrc_filename,
        ))

    #FIXME: The contents of this output "py_filename" should additionally be
    #opened for writing and prefixed by a shebang line running the active Python
    #interpreter. See the "guipsdcacheui" submodule for relevant logic.
