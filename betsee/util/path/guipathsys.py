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
:mod:`betsee.guimetaapp`
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

# ....................{ GETTERS ~ dir                     }....................
#FIXME: Actually implement this function as described. For simplicity, this
#function currently defers to *ALWAYS* return get_user_documents_dirname(). Instead:
#
#* Define a new set_path_dialog_init_pathname() setter in this submodule,
#  internally caching the passed pathname to the application's "QSettings" store.
#* In the get_selected_prior_dirname() function:
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
#FIXME: Actually, the above may be slightly overkill. It would appear that
#Qt already provides such functionality internally -- but *ONLY* for dialogs
#opened with the QFileDialog.getOpenFileName() getter passed an "init_pathname"
#of "None" and a "dialog_options" bit-field containing the
#"QFileDialog.DontUseNativeDialog" option. Why? Because Qt's builtin non-native
#file dialog implementation internally defaults to the last opened pathname,
#which Qt even preserves across application invocations. That said, the
#usefulness of this feature is somewhat hampered by these constraints. What
#would be more useful would be to obtain access to the internal global that Qt
#preserves across application invocations -- which, hopefully, PySide2 will
#somehow expose. Let's examine the C++-based implementation of the
#QFileDialog.getOpenFileName() getter to discover this global's identity.
#
#See also this relevant StackOverflow question:
#    https://stackoverflow.com/a/23003370/2809027
#FIXME: We have confirmed that, indeed, such a C++ global exists --
#"QFileDialog.lastVisitedDir", as visible here:
#    https://code.woboq.org/qt5/qtbase/src/widgets/dialogs/qfiledialog.cpp.html#lastVisitedDir
#Sadly, as expected, neither PyQt5 nor PySide2 expose this global to Python
#code. For this reason, Qt-based Python applications reimplement this global in
#Python space by... wait for it, using a similar approach to that delineated in
#the first FIXME comment above. Of course, since the exact approach that we've
#outlined appears to demonstrably superior to anything any other application is
#doing, let's just run with that, shall we? *sigh*

def get_selected_prior_dirname() -> str:
    '''
    Absolute dirname of the **last selected directory** (i.e., the directory
    component of the pathname returned by the most recent call to this
    function; equivalently, the return value of the
    :func:`guipathsys.get_selected_prior_dirname` function)
    directory to be initially selected by **path dialogs**
    (i.e., dialogs requesting the end user interactively select a possibly
    non-existing path).

    Returns
    ----------
    str
        Absolute dirname of either:

        * If the current user has already successfully selected at least one
          path from a path dialog *and* the most recently selected such path
          still exists, the directory component of that path.
        * Else (i.e., if this user has yet to select a path from a path
          dialog), a directory assumed to contain work-related files for this
          user.
    '''

    # Return the dirname of the current user's documents directory.
    return get_user_documents_existing_dirname()

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
