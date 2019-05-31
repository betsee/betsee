#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Collection of the absolute paths of numerous critical files and directories
(both system-wide and user-specific) describing the structure of the local
filesystem in a general-purpose, cross-platform manner independent of this
application's specific usage of this filesystem.

See Also
----------
:mod:`betsee.guiappmeta`
    Collection of the absolute paths of numerous critical files and directories
    describing the structure of this application on the local filesystem.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QStandardPaths
from betse.util.io.log import logs
from betse.util.os.shell import shelldir
from betse.util.path import dirs
from betse.util.type.decorator.decmemo import func_cached
from betse.util.type.types import type_check

# ....................{ GETTERS ~ dir : cached            }....................
@func_cached
def get_user_documents_existing_dirname() -> str:
    '''
    Absolute dirname of the **last existing directory compoment** (i.e.,
    longest trailing dirname whose directory actually exists) of the platform-
    and typically user-specific directory containing work-oriented files for
    the current user.

    Unlike the directory returned by the comparable
    :func:`get_user_documents_dirname` getter, this directory is guaranteed to
    exist on all platforms. For safety, this function does *not* create any
    additional directories; this function only finds an existing directory
    whose dirname most closely approximates that of the expected directory.

    See Also
    ----------
    :func:`get_user_documents_dirname`
        Comparable getter *not* guaranteeing the returned directory to exist.
    '''

    return dirs.get_parent_dir_last(get_user_documents_dirname())


@func_cached
def get_user_documents_dirname() -> str:
    '''
    Absolute dirname of the platform- and typically user-specific directory
    containing work-oriented files for the current user.

    This directory is:

    * On both Linux and macOS, ``~/Documents``.
    * On Windows, ``C:/Users/{USERNAME}/Documents``.

    Caveats
    ----------
    **This directory is not guaranteed to exist on all platforms.** Under:

    * Microsoft Windows, this directory is guaranteed to exist.
    * macOS, this directory is guaranteed to exist.
    * Linux, this directory is *not* guaranteed to exist. This directory is
      likely to exist under Linux distributions complying with the
      freedesktop.org XDG Base Directory Specification. Even under these
      distributions, however, users remain freely at liberty to remove this
      directory. (Freedom has its price, does it not?)

    See Also
    ----------
    :func:`get_user_documents_existing_dirname`
        Comparable getter guaranteeing the returned directory to exist.
    '''

    return _get_dir(QStandardPaths.DocumentsLocation)

# ....................{ PRIVATE                           }....................
@type_check
def _get_dir(location: QStandardPaths.StandardLocation) -> str:
    '''
    Absolute dirname of the **standard directory** (i.e., platform- and
    typically user-specific directory) identified by the passed Qt enumeration
    constant.

    Parameters
    ----------
    location : QStandardPaths.StandardLocation
        Qt-specific enumeration constant identifying the standard directory to
        return this path of.

    Returns
    ----------
    str
        Absolute dirname of this standard directory.
    '''

    # Qt provides two means of querying for standard paths:
    #
    # * QStandardPaths.standardLocations(), a static getter function that may
    #   unsafely return the empty list "...if no locations for [the passed]
    #   type are defined."
    # * QStandardPaths.writableLocation(), a static getter function that may
    #   unsafely return "...an empty string if the location cannot be
    #   determined."
    #
    # Although both functions may return unsafe empty values, the latter is
    # more likely to do so and is thus less safe. Why? Because the former is
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
            'No platform-specific directories '
            'defined for QStandardPaths type "%d"; '
            'falling back to current working directory (CWD).',
            location)

        # For safety, fallback to the current working directory (CWD).
        dirname = shelldir.get_cwd_dirname()

    # Return this path.
    return dirname
