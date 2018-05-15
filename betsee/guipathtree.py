#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Collection of the absolute paths of numerous critical files and directories
describing the structure of this application on the local filesystem.

These are intended for consumption by both this application and downstream
reverse dependencies of this application. For portability, these paths are
initialized in a system-aware manner guaranteed to be sane under insane
installation environments -- including PyInstaller-frozen executables and
:mod:`setuptools`-installed script wrappers.

See Also
----------
:mod:`betsee.util.path.guipathsys`
    Collection of the absolute paths of numerous critical files and directories
    describing the structure of the local filesystem.
'''

#FIXME: The current globals-based approach is inefficient in the case of BETSE
#being installed as a compressed EGG rather than an uncompressed directory. In
#the former case, the current approach (namely, the call to
#resources.get_pathname() performed below) silently extracts the entirety of
#this egg to a temporary setuptools-specific cache directory. That's bad. To
#circumvent this, we'll need to refactor the codebase to directly require only
#"file"-like objects rather than indirectly requiring the absolute paths of
#data resources that are then opened as "file"-like objects.
#
#Specifically, whenever we require a "file"-like object for a codebase resource,
#we'll need to call the setuptools-specific pkg_resources.resource_stream()
#function rather than attempting to open the path given by a global below.
#Ultimately, *ALL* of the codebase-specific globals declared below (e.g.,
#"DATA_DIRNAME") should go away.

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on missing mandatory dependencies,
# the top-level of this module may import *ONLY* from packages guaranteed to
# exist at installation time (i.e., standard Python packages). Likewise, to
# avoid circular import dependencies, the top-level of this module should avoid
# importing application packages except where explicitly required.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from betse import pathtree as betse_pathtree
from betse.util.path import dirs, files, pathnames
from betse.util.type.decorator.decmemo import func_cached
from betsee import guimetadata

# ....................{ GETTERS ~ dir : data               }....................
@func_cached
def get_data_dirname() -> str:
    '''
    Absolute path of this application's top-level data directory if found *or*
    raise an exception otherwise (i.e., if this directory is *not* found).

    This directory contains application-internal resources (e.g., media files)
    required at application runtime.
    '''

    # Avoid circular import dependencies.
    import betsee

    # Absolute path of this directory.
    data_dirname = pathnames.get_app_pathname(package=betsee, pathname='data')

    # If this directory is not found, raise an exception.
    dirs.die_unless_dir(data_dirname)

    # Return the absolute path of this directory.
    return data_dirname


@func_cached
def get_data_py_dirname() -> str:
    '''
    Absolute path of this application's data subdirectory containing
    pure-Python modules and packages generated at runtime by this application if
    found *or* raise an exception otherwise (i.e., if this directory is *not*
    found).
    '''

    # Create this directory if needed and return its dirname.
    return dirs.join_and_die_unless_dir(get_data_dirname(), 'py')


@func_cached
def get_data_qrc_dirname() -> str:
    '''
    Absolute path of this application's data subdirectory containing
    XML-formatted Qt resource collection (QRC) files exported by the external Qt
    Designer application and all binary resource files listed in these files if
    found *or* raise an exception otherwise (i.e., if this directory is *not*
    found).
    '''

    # Return this dirname if this directory exists or raise an exception.
    return dirs.join_and_die_unless_dir(get_data_dirname(), 'qrc')


@func_cached
def get_data_ui_dirname() -> str:
    '''
    Absolute path of this application's data subdirectory containing
    XML-formatted user interface (UI) files exported by the external Qt Designer
    application if found *or* raise an exception otherwise (i.e., if this
    directory is *not* found).
    '''

    # Return this dirname if this directory exists or raise an exception.
    return dirs.join_and_die_unless_dir(get_data_dirname(), 'ui')

# ....................{ GETTERS ~ dir : dot                }....................
@func_cached
def get_dot_dirname() -> str:
    '''
    Absolute path of this application's top-level dot directory in the home
    directory of the current user, silently creating this directory if *not*
    already found.

    This directory contains user-specific files (e.g., generated Python modules)
    both read from and written to at application runtime. These are typically
    plaintext files consumable by external users and third-party utilities.

    For tidiness, this directory currently resides under BETSE's dot directory
    (e.g., ``~/.betse/betsee`` under Linux).
    '''

    # Create this directory if needed and return its dirname.
    return dirs.join_and_make_unless_dir(
        betse_pathtree.get_dot_dirname(), guimetadata.SCRIPT_BASENAME)

# ....................{ GETTERS ~ file : data              }....................
@func_cached
def get_data_qrc_filename() -> str:
    '''
    Absolute path of the XML-formatted Qt resource collection (QRC) file
    exported by the external Qt Designer application structuring all external
    resources (e.g., icons) required by this application's main window if found
    *or* raise an exception otherwise (i.e., if this file is *not* found).
    '''

    # Return this filename if this file exists or raise an exception.
    #
    # Note that this basename *MUST* be the same as that specified by the
    # "resources" attribute of all XML tags contained in the file whose path is
    # given by the get_data_ui_filename() function. Why? Because obfuscatory Qt.
    return files.join_and_die_unless_file(
        get_data_qrc_dirname(), guimetadata.SCRIPT_BASENAME + '.qrc')


@func_cached
def get_data_ui_filename() -> str:
    '''
    Absolute path of the XML-formatted user interface (UI) file exported by the
    external Qt Designer application structuring this application's main window
    if found *or* raise an exception otherwise (i.e., if this file is *not*
    found).
    '''

    # Return this filename if this file exists or raise an exception.
    return files.join_and_die_unless_file(
        get_data_ui_dirname(), guimetadata.SCRIPT_BASENAME + '.ui')

# ....................{ GETTERS ~ file : data              }....................
@func_cached
def get_data_py_qrc_filename() -> str:
    '''
    Absolute path of the pure-Python module generated from the XML-formatted Qt
    resource collection (QRC) file exported by the external Qt Designer
    application structuring all external resources (e.g., icons) required by
    this application's main window if found *or* raise an exception otherwise
    (i.e., if this directory is *not* found).

    Caveats
    ----------
    This module is guaranteed to be importable but *not* necessarily be
    up-to-date with the input paths from which this module is dynamically
    regenerated at runtime. The caller is assumed to do so explicitly.

    See Also
    ----------
    :mod:`betsee.gui.guicache`
        Submodule dynamically generating this module.
    '''

    # Note that this basename *MUST* be:
    #
    # * Prefixed by the same basename excluding filetype returned by the
    #   get_data_qrc_filename() function.
    # * Suffixed by "_rc.py". Why? Because the Python code generated at runtime
    #   by the "pyside2uic" package assumes this to be the case. Naturally, this
    #   assumption is *NOT* configurable.
    return files.join_and_die_unless_file(
        get_data_py_dirname(), guimetadata.MAIN_WINDOW_QRC_MODULE_NAME + '.py')


@func_cached
def get_data_py_ui_filename() -> str:
    '''
    Absolute path of the pure-Python module generated from the XML-formatted
    user interface (UI) file exported by the external Qt Designer application
    structuring this application's main window if found *or* raise an exception
    otherwise (i.e., if this directory is *not* found).

    Caveats
    ----------
    This module is guaranteed to be importable but *not* necessarily be
    up-to-date with the input paths from which this module is dynamically
    regenerated at runtime. The caller is assumed to do so explicitly.

    See Also
    ----------
    :mod:`betsee.gui.guicache`
        Submodule dynamically generating this module.
    '''

    return files.join_and_die_unless_file(
        get_data_py_dirname(), guimetadata.MAIN_WINDOW_UI_MODULE_NAME + '.py')
