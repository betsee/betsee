#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
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

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, QSettings
from betse.util.os.brand import windows
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideSettingsException
from betsee.util.type.guitype import QVariantTypes, QVariantOrNoneTypes

# ....................{ INITIALIZERS                      }....................
def init() -> None:
    '''
    Initialize the :class:`QSettings` class *before* the :func:`make` function
    is called elsewhere to instantiate that class.

    Specifically, this function establishes the default settings format
    subsequently accessed by the default :class:`QSettings` constructor as
    follows:

    * If the current platform is non-Cygwin Windows, request that settings be
      formatted in INI format to a physical file. By default, Windows settings
      are formatted as registery keys. Since the Windows registery is
      well-known to be fragile, insecure, and broken by design, this default
      remains sadly unfortunate but unfixable.
    * Else, request that settings be formatted in the format preferred by the
      current platform guaranteed to be a physical file.
    '''

    # Set the default settings format in a platform-specific manner.
    QSettings.setDefaultFormat(
        QSettings.IniFormat if windows.is_windows_vanilla() else
        QSettings.NativeFormat)

# ....................{ EXCEPTIONS                        }....................
@type_check
def die_unless_setting(setting_name: str) -> None:
    '''
    Raise an exception unless the application-wide setting with the passed name
    has been previously saved to the backing store containing these settings.

    Parameters
    ----------
    setting_name : str
        Name of the setting to be validated.

    Raises
    ----------
    BetseePySideSettingsException
        If this setting has *not* been previously saved to this backing store.
    '''

    # If this setting has *NOT* been previously saved to this backing store,
    # raise an exception.
    if not is_setting(setting_name):
        raise BetseePySideSettingsException(QCoreApplication.translate(
            'guisettings', 'Application setting "{0}" not found.'.format(setting_name)))

# ....................{ TESTERS                           }....................
@type_check
def is_setting(setting_name: str) -> bool:
    '''
    ``True`` only if the application-wide setting with the passed name has been
    previously saved to the backing store containing these settings.

    Parameters
    ----------
    setting_name : str
        Name of the setting to be tested for.

    Returns
    ----------
    bool
        If this setting has been previously saved to this backing store.
    '''

    return get_settings().contains(setting_name)

# ....................{ GETTERS                           }....................
def get_settings() -> QSettings:
    '''
    New :class:`QSettings` instance encapsulating all application-wide settings
    in a cross-platform, thread- and process-safe manner guaranteed to be
    safely (de)serializable to and from a platform-, application-, and
    user-specific file guaranteed to be disambiguously unique.

    Design
    ----------
    By Qt design, repeatedly calling this function throughout the lifetime of
    this application is guaranteed to be efficient. Thus, callers are
    encouraged to do so rather than persist a permanent reference to the first
    :class:`QSettings` instance returned by this function.
    '''

    # Default settings leveraging the default QSettings() constructor,
    # including:
    #
    # * The "QCoreApplication.applicationName", "organizationName", and
    #   "organizationName" attributes previously set by the
    #   "betsee.util.psdapp" submodule.
    # * The "QSettings.defaultFormat" attribute previously set by the above
    #   init() function.
    # * The default "QSettings.UserScope" scope.
    settings = QSettings()

    # Prevent settings from being written and/or read in a Cascading Style
    # Sheets (CSS)-style manner over a hierarchically nested multiplicity of
    # discontiguous files littered across the filesystem. Equivalently,
    # instruct Qt to write and read settings *ONLY* to and from the single file
    # specific to this combination of platform, application, and user.
    settings.setFallbacksEnabled(False)

    # Encode settings persisted to INI files (e.g., on *nix platforms) with the
    # standard UTF-8. By default, settings are persisted to such files with the
    # non-standard INI escape sequences "codec." That's asking for trouble.
    settings.setIniCodec('UTF-8')

    # Return these settings.
    return settings

# ....................{ GETTERS ~ setting                 }....................
@type_check
def get_setting(setting_name: str) -> QVariantTypes:
    '''
    Previously saved value of the application-wide setting with the passed name
    if this setting has been previously saved to the backing store containing
    these settings *or* raise an exception otherwise (i.e., if this setting has
    *not* been saved to this backing store).

    Parameters
    ----------
    setting_name : str
        Name of the setting to be retrieved.

    Returns
    ----------
    QVariantTypes
        Previously saved value of this setting.

    Raises
    ----------
    BetseePySideSettingsException
        If this setting has *not* been previously saved to this backing store.
    '''

    # If this setting has *NOT* been previously saved to this backing store,
    # raise an exception.
    #
    # Note that this validation is effectively mandatory. The
    # QSettings::value() method returns a sentinel "QVariant" instance
    # reducing to 0 if this setting has *NOT* been previously saved to this
    # backing store -- which, of course, is simply insane. (Thanks, Qt!)
    die_unless_setting(setting_name)
    # Else, this setting has been previously saved to this backing store.

    # Return the previously saved value of this setting.
    return get_settings().value(setting_name)


@type_check
def get_setting_or_default(
    setting_name: str,
    setting_value_default: QVariantTypes,
) -> QVariantTypes:
    '''
    Previously saved value of the application-wide setting with the passed name
    if this setting has been previously saved to the backing store containing
    these settings *or* the passed default value otherwise (i.e., if this
    setting has *not* been saved to this backing store).

    Parameters
    ----------
    setting_name : str
        Name of the setting to be retrieved.
    setting_value_default : QVariantTypes
        Default value to be returned if this setting has been previously saved
        to this backing store.

    Returns
    ----------
    QVariantTypes
        Either:

        * If this setting has been previously saved to this backing store,
          the previously saved value of this setting.
        * Else, this default value.
    '''

    # A Qt API did something right. Break open the champagne!
    return get_settings().value(setting_name, setting_value_default)


@type_check
def get_setting_or_none(setting_name: str) -> QVariantOrNoneTypes:
    '''
    Previously saved value of the application-wide setting with the passed name
    if this setting has been previously saved to the backing store containing
    these settings *or* ``None`` otherwise (i.e., if this setting has *not*
    been saved to this backing store).

    Parameters
    ----------
    setting_name : str
        Name of the setting to be retrieved.

    Returns
    ----------
    QVariantOrNoneTypes
        Either:

        * If this setting has been previously saved to this backing store,
          the previously saved value of this setting.
        * Else, ``None``.
    '''

    # If this setting has been previously saved to this backing store, return
    # the previously saved value of this setting; else, return "None".
    return get_setting(setting_name) if is_setting(setting_name) else None

# ....................{ SETTERS                           }....................
@type_check
def set_setting(setting_name: str, setting_value: QVariantTypes) -> None:
    '''
    Set the application-wide setting with the passed name to the passed
    :class:`PySide2.QtCore.QVariant`-compliant value.

    :class:`PySide2.QtCore.QVariant`-compliant values include instances of:

    * Most primitive Python types -- notably, :class:`bool`, :class:`float`,
      :class:`int`, and :class:`str` but *not* :class:`complex`.
    * Several structured Qt types -- notably, :class:`PySide2.QtCore.QLine`,
      :class:`PySide2.QtCore.QPoint`, :class:`PySide2.QtCore.QRect`, and
      :class:`PySide2.QtCore.QSize`.

    Parameters
    ----------
    setting_name : str
        Name of the setting to be set.
    setting_value : QVariantTypes
        Value to set this setting to.
    '''

    # Set this setting to this value.
    return get_settings().setValue(setting_name, setting_value)
