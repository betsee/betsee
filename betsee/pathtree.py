#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
High-level constants describing this application's filesystem usage.

These constants provide the absolute paths of files and directories intended for
general use by both this application and downstream reverse dependencies of this
application. For portability, these constants are initialized in a system-aware
manner guaranteed to be sane under various installation environments --
including PyInstaller-frozen executables and :mod:`setuptools`-installed script
wrappers.
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

from betsee import metadata
from betse.util.type.call.memoizers import callable_cached

# ....................{ GETTERS ~ dir                      }....................
@callable_cached
def get_data_dirname() -> str:
    '''
    Absolute path of this application's top-level data directory if found *or*
    raise an exception otherwise (i.e., if this directory is *not* found).

    This directory contains application-internal resources (e.g., media files)
    required at application runtime.
    '''

    # Avoid circular import dependencies.
    import betsee
    from betse.util.path import dirs, pathnames

    # Absolute path of this directory.
    data_dirname = pathnames.get_app_pathname(package=betsee, pathname='data')

    # If this directory is not found, raise an exception.
    dirs.die_unless_dir(data_dirname)

    # Return the absolute path of this directory.
    return data_dirname


@callable_cached
def get_data_ui_dirname() -> str:
    '''
    Absolute path of this application's data subdirectory containing
    XML-formatted user interface (UI) file exported by the external Qt Designer
    application if found *or* raise an exception otherwise (i.e., if this
    directory is *not* found).
    '''

    # Avoid circular import dependencies.
    from betse.util.path import dirs

    # Return this dirname if this directory exists or raise an exception.
    return dirs.join_and_die_unless_dir(get_data_dirname(), 'ui')

# ....................{ GETTERS ~ file                     }....................
@callable_cached
def get_main_ui_filename() -> str:
    '''
    Absolute path of the XML-formatted user interface (UI) file exported by the
    external Qt Designer application structuring this application's main window
    if found *or* raise an exception otherwise (i.e., if this file is *not*
    found).
    '''

    # Avoid circular import dependencies.
    from betse.util.path import files

    # Return this dirname if this directory exists or raise an exception.
    return files.join_and_die_unless_file(
        get_data_ui_dirname(), metadata.SCRIPT_BASENAME + '.ui')
