#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
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

# ....................{ MAKERS                             }....................
def make_settings(self) -> QSettings:
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

    # Platform-specific format to (de)serialize settings in.
    settings_format = None

    # If the current platform is non-Cygwin Windows, format settings in INI
    # format to a physical file. By default, Windows settings are formatted
    # as registery keys. Since the registery is fragile, insecure, and
    # broken by design, this default remains unfortunate but fixable.
    if oses.is_windows_vanilla():
        settings_format = QSettings.IniFormat
    # Else, format settings in the format preferred by this platform.
    else:
        settings_format = QSettings.NativeFormat

    # Since the QCoreApplication::applicationName, ::applicationVersion,
    # ::organizationName, and ::organizationName properties have already been
    # set, the default QSettings() constructor may be safely called. So, do so.
    settings = QSettings(settings_format, QSettings.UserScope)

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
