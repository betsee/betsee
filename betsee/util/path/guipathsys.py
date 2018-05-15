#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Collection of the absolute paths of numerous critical files and directories
(both system-wide and user-specific) describing the structure of the local
filesystem in a general-purpose, cross-platform manner independent of this
application's specific usage of this filesystem.

See Also
----------
:mod:`betsee.guipathtree`
    Collection of the absolute paths of numerous critical files and directories
    describing the structure of this application on the local filesystem.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QStandardPaths
from betse.util.io.log import logs
from betse.util.os.shell import shelldir
from betse.util.type.decorator.decmemo import func_cached
from betse.util.type.types import type_check

# ....................{ GETTERS ~ dir                      }....................
#FIXME: Actually implement this function as described. For simplicity, this
#function currently defers to *ALWAYS* return get_user_docs_dirname(). Instead:
#
#* Define a new set_path_dialog_init_pathname() setter in this submodule,
#  internally caching the passed pathname to the application's "QSettings" store.
#* In the get_path_dialog_init_pathname() function:
#  * If the application's "QSettings" store contains this previously cached
#    pathname *AND* this pathname still exists, return this pathname.
#  * Else, return get_user_docs_pathname().
#* In all select_*() functions defined by the "guidir" and "guifile" submodules:
#  * *BEFORE* the path dialog is displayed and the caller passed no
#    "init_pathname" parameter (i.e., if this parameter is "None"), externally
#    call this getter to obtain the default value of this "init_pathname"
#    parameter. <---- O.K., this is now done.
#  * *AFTER* the end user successfully confirms this path dialog, externally
#    call this setter.
#
#Not terribly arduous and quite useful. Make it so, please.

def get_path_dialog_init_pathname() -> str:
    '''
    Absolute pathname of the path of arbitrary type (e.g., file, directory) to
    initially display in *path dialogs* (i.e., dialogs requesting the end user
    interactively select a possibly non-existing path).

    Returns
    ----------
    str
        Absolute pathname of either:
        * If the current user has already successfully selected at least one
          path from a path dialog _and_ the most recently selected such path
          still exists, that path.
        * Else (i.e., if this user has yet to select a path from a path dialog),
          a directory containing work-oriented files for this user.
    '''

    # Return the current user's documents directory.
    return get_user_docs_dirname()

# ....................{ GETTERS ~ dir : cached             }....................
@func_cached
def get_user_docs_dirname() -> str:
    '''
    Absolute pathname of the platform- and typically user-specific directory
    containing work-oriented files for the current user.

    This directory is:

    * On both Linux and macOS, ``~/Documents``.
    * On Windows, ``C:/Users/{USERNAME}/Documents``.
    '''

    return _get_dir(QStandardPaths.DocumentsLocation)

# ....................{ PRIVATE                            }....................
@type_check
def _get_dir(location: QStandardPaths.StandardLocation) -> str:
    '''
    Absolute path of the **standard directory** (i.e., platform- and typically
    user-specific directory) identified by the passed Qt enumeration constant.

    Parameters
    ----------
    location : QStandardPaths.StandardLocation
        Qt-specific enumeration constant identifying the standard directory to
        return this path of.

    Returns
    ----------
    str
        Absolute path of this standard directory.
    '''

    # Qt provides two means of querying for standard paths:
    #
    # * QStandardPaths.standardLocations(), a static getter function that may
    #   unsafely return the empty list "...if no locations for [the passed] type
    #   are defined."
    # * QStandardPaths.writableLocation(), a static getter function that may
    #   unsafely return "...an empty string if the location cannot be
    #   determined."
    #
    # Although both functions may return unsafe empty values, the latter is more
    # likely to do so and is thus less safe. Why? Because the former is
    # guaranteed to return at least as much and typically more than the latter.

    # List of the absolute paths of all directories satisfying this location,
    # sorted in descending order of presumed preference.
    dirnames = QStandardPaths.standardLocations(location)

    # If at least one such directory exists, defer to the absolute path of the
    # first such directory -- typically the same path returned by
    # "QStandardPaths.writableLocation(location)".
    if dirnames:
        dirname = dirnames[0]
    # Else, no such directories exist.
    else:
        # Log a non-fatal warning.
        logs.log_warning(
            'Standard location "%d" directories not found.', location)

        # For safety, fallback to the current working directory (CWD).
        dirname = shelldir.get_cwd_dirname()

    # Return this path.
    return dirname
