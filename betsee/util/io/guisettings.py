#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-based application-wide settings facilities.

See Also
----------
:class:`PySide2.QtCore.QSettings`
    This class' official documentation is a comprehensive, comprehensible
    commentary on cross-platform, thread- and process-safe (de)serialization of
    application-wide settings. This documentation doubles as a human-readable
    FAQ and hence comes recommended, particularly for the Qt neophyte.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QSettings
from betse.util.os import oses

# ....................{ INITIALIZERS                       }....................
def init() -> None:
    '''
    Initialize the :class:`QSettings` class *before* the :func:`make` function
    is called elsewhere to instantiate that class.

    Specifically, this function establishes the default settings format
    subsequently accessed by the default :class:`QSettings` constructor as
    follows:

    * If the current platform is non-Cygwin Windows, request that settings be
      formatted in INI format to a physical file. By default, Windows settings
      are formatted as registery keys. Since the registery is fragile, insecure,
      and broken by design, this default remains unfortunate but fixable.
    * Else, request that settings be formatted in the format preferred by the
      current platform guaranteed to be a physical file.
    '''

    # Set the default settings format in a platform-specific manner.
    QSettings.setDefaultFormat(
        QSettings.IniFormat if oses.is_windows_vanilla() else
        QSettings.NativeFormat)

# ....................{ MAKERS                             }....................
def make() -> QSettings:
    '''
    Create and return a new :class:`QSettings` instance, encapsulating all
    application-wide settings in a cross-platform, thread- and process-safe
    manner guaranteed to be safely (de)serializable to and from a predefined
    application- and user-specific on-disk file.

    Design
    ----------
    Note that repeatedly calling this function throughout the lifetime of this
    application is guaranteed to be efficient by design. Thus, callers are
    encouraged to do so rather than persist a permanent reference to the first
    :class:`QSettings` instance returned by this function.
    '''

    # Default settings leveraging the default QSettings() constructor,
    # including:
    #
    # * The "QCoreApplication.applicationName", "organizationName", and
    #   "organizationName" attributes previously set by the "betsee.util.psdapp"
    #   submodule.
    # * The "QSettings.defaultFormat" attribute previously set by the above
    #   init() function.
    # * The default "QSettings.UserScope" scope.
    settings = QSettings()

    # Prevent settings from being read and/or written in a Cascading Style
    # Sheets (CSS)-style manner over a hierarchically nested multiplicity of
    # discontiguous files littered across the filesystem.
    #
    # Equivalently, read and write settings only to the single file specific to
    # the current platform, application, and user.
    settings.setFallbacksEnabled(False)

    # Encode settings persisted to INI files (e.g., on *nix platforms) with the
    # standard UTF-8. By default, settings are persisted to such files with the
    # non-standard INI escape sequences "codec." That's just asking for trouble.
    settings.setIniCodec('UTF-8')

    # Return these settings.
    return settings
