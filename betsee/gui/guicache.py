#!/usr/bin/env python3
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level caching functionality for this application's graphical user interface
(GUI), persisting external resources required by this GUI to user-specific files
on the local filesystem.
'''

#FIXME: Still insufficient. Why? Because we need to automatically invalidate
#caches whenever any file in the BETSEE codebase changes. *sigh*

# ....................{ IMPORTS                            }....................
import PySide2, pyside2uic
from betse.util.io.log import logs
from betse.util.path import files, paths, pathnames
from betse.util.path.command import cmdpath
from betse.util.py import pys
from betse.util.type import modules
from betse.util.type.types import type_check, IterableTypes
from betsee import pathtree
from betsee.lib.pyside import psdqrc, psdui

# ....................{ CACHERS ~ public                   }....................
def cache_py_files() -> None:
    '''
    Either create and cache *or* reuse each previously cached pure-Python
    module required at runtime by this GUI, including all :mod:`PySide2`-based
    modules converted from XML-formatted files and binary resources exported by
    the external Qt Designer GUI.

    For efficiency, previously generated modules are regenerated *only* as
    needed (i.e., if older than the underlying XML files and other associated
    paths from which these modules are generated).
    '''

    # Append the directory containing all generated modules to the PYTHONPATH,
    # permitting these modules to be subsequently imported elsewhere.
    pys.add_import_dirname(pathtree.get_dot_py_dirname())

    # Generate the requisite pure-Python modules (in any arbitrary order).
    _cache_py_qrc_file()
    _cache_py_ui_file()

    # For safety, raise an exception unless all such modules exist now.
    files.die_unless_file(
        pathtree.get_dot_py_qrc_filename(),
        pathtree.get_dot_py_ui_filename())

# ....................{ CACHERS ~ private                  }....................
def _cache_py_qrc_file() -> None:
    '''
    Either create and cache *or* reuse the previously cached pure-Python
    :mod:`PySide2`-based module embedding all binary resources in this
    application's main Qt resource collection (QRC).

    See Also
    ----------
    :func:`_is_qt_to_py_file_conversion_needed`
        Further details.
    '''

    # If either:
    #
    # * The input "pyside2-rcc" executable run by the
    #   psdqrc.convert_qrc_to_py_file() function called below.
    # * Any file or subdirectory in the input directory containing both this
    #   input QRC file and all resource files referenced by this file.
    #
    # ...is older than this output module, recreate this output module from
    # these input paths.
    if _is_output_path_outdated(
        input_pathnames=(
            cmdpath.get_filename('pyside2-rcc'),
            pathtree.get_data_qrc_dirname(),
        ),
        output_filename=pathtree.get_dot_py_qrc_filename(),
    ):
        psdqrc.convert_qrc_to_py_file(
            qrc_filename=pathtree.get_data_qrc_filename(),
            py_filename=pathtree.get_dot_py_qrc_filename())


def _cache_py_ui_file() -> None:
    '''
    Either create and cache *or* reuse the previously cached pure-Python
    :mod:`PySide2`-based module implementing the superficial construction of
    this application's main window.

    See Also
    ----------
    :func:`_is_qt_to_py_file_conversion_needed`
        Further details.
    '''

    # If either:
    #
    # * Any file or subdirectory in the input directories containing the
    #   "PySide2" and "pyside2uic" packages required by the
    #   psdui.convert_ui_to_py_file() function called below.
    # * This input UI file.
    #
    # ...is older than this output module, recreate this output module from
    # these input paths.
    if _is_output_path_outdated(
        input_pathnames=(
            modules.get_dirname(PySide2),
            modules.get_dirname(pyside2uic),
            pathtree.get_data_ui_filename(),
        ),
        output_filename=pathtree.get_dot_py_ui_filename(),
    ):
        psdui.convert_ui_to_py_file(
            ui_filename=pathtree.get_data_ui_filename(),
            py_filename=pathtree.get_dot_py_ui_filename())


@type_check
def _is_output_path_outdated(
    input_pathnames: IterableTypes, output_filename: str) -> bool:
    '''
    ``True`` only if the output path either does not exist, does but is older
    than all input paths in the passed iterable, *or* does but is an empty
    (i.e., zero-byte) file.

    If this function returns ``True``, the caller is expected to explicitly
    (re)create this output path from these input paths.

    Parameters
    ----------
    input_pathnames: IterableTypes
        Absolute or relative pathnames of all input paths required to (re)create
        this output path.
    output_filename : str
        Absolute or relative pathname of the output path.
    '''

    # Log this inspection.
    logs.log_info(
        'Inspecting PySide2 module "%s" for changes...',
        pathnames.get_basename(output_filename))

    # Return true only if either...
    return (
        # This output module does *NOT* exist or...
        not paths.is_path(output_filename) or
        # This output module does exist but is older than at least one of these
        # output paths or...
        paths.get_mtime(output_filename) <
        paths.get_mtime_newest(input_pathnames) or
        # This output module is a zero-byte file.
        files.get_size(output_filename) == 0
    )
