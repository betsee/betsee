#!/usr/bin/env python3
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level caching functionality for this application's graphical user interface
(GUI), persisting external resources required by this GUI to user-specific files
on the local filesystem.
'''

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logs
from betse.util.path import dirs, paths, pathnames
from betse.util.py import pys
from betsee import pathtree
from betsee.lib.pyside import psdrc

# ....................{ CACHERS                            }....................
def cache_dot_py_files() -> None:
    '''
    Generate all pure-Python modules required at runtime by this GUI, including
    all :mod:`PySide2`-based modules converted from XML-formatted file exported
    by the external Qt Designer application.

    For efficiency, previously generated modules are regenerated *only* as
    needed (i.e., if older than the underlying XML files and other associated
    paths from which these modules are generated).
    '''

    # Append the directory containing all generated modules to the PYTHONPATH,
    # permitting these modules to be subsequently imported elsewhere.
    pys.add_import_dirname(pathtree.get_dot_py_dirname())

    # Generate the module for this application's Qt resource collection (QRC).
    _cache_dot_py_qrc_file()



def _cache_dot_py_qrc_file() -> None:
    '''
    Generate the pure-Python :mod:`PySide2`-based module embedding all binary
    resources in this application's main Qt resource collection (QRC).
    '''

    # Absolute path of this output module.
    PY_FILENAME = pathtree.get_dot_py_qrc_filename()

    # Absolute path of the input QRC file generating this module.
    QRC_FILENAME = pathtree.get_data_qrc_filename()

    # Absolute path of the input directory containing all resource files listed
    # within this QRC file.
    QRC_DIRNAME = pathtree.get_data_qrc_dirname()

    # Log this generation.
    logs.log_info(
        'Inspecting PySide2 module "%s" synchronicity...',
        pathnames.get_basename(PY_FILENAME))

    # If this module exists and hence has already been generated...
    if paths.is_path(PY_FILENAME):
        # And this module is as recent this QRC file or any resource
        # listed within this file...
        if paths.get_mtime(PY_FILENAME) >= dirs.get_mtime_newest(QRC_DIRNAME):
            # Reuse this module as is.
            return

    # Else, this module requires (re)generation. Do so.
    psdrc.convert_qrc_file_to_py_file(
        qrc_filename=QRC_FILENAME, py_filename=PY_FILENAME)
