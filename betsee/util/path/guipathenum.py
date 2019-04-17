#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Pathname dialog option** (i.e., member of the Qt-specific
:attr:`QFileDialog.Option` enumeration type conveniently reduced to
integer-based bit masks to be passed as the optionally OR-ed values of the
``dialog_options`` parameter of the
:func:`betsee.util.path.guipath.select_path` function by callers) constants.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtWidgets import QFileDialog

# ....................{ CONSTANTS                         }....................
SHOW_DIRS_ONLY = int(QFileDialog.ShowDirsOnly)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to *only* permit
directories to be selected.

By default, this dialog permits both files *and* directories to be selected.
'''


DONT_RESOLVE_SYMLINKS = int(QFileDialog.DontResolveSymlinks)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to *not* resolve symbolic
links under POSIX-compatible platforms.

By default, this dialog resolves symbolic links.
'''


DONT_CONFIRM_OVERWRITE = int(QFileDialog.DontConfirmOverwrite)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to *not* request
confirmation if an existing path is selected.

By default, this dialog requests such confirmation.
'''


DONT_USE_NATIVE_DIALOG = int(QFileDialog.DontUseNativeDialog)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to *not* be a native
(i.e., platform-specific) path dialog, implying this dialog to be a non-native,
platform-agnostic, Qt-specific dialog instead.

By default, this dialog is guaranteed to be a native path dialog unless any of
the following conditions apply:

* This function internally instantiates a :class:`QFileDialog` subclass
  containing the ``Q_OBJECT`` macro.
* The current platform does *not* provide a native path dialog of the type
  requested by the caller.
'''


#FIXME: What do "read-only" and "writable" actually mean in this context?
#Official Qt documentation is sadly uncommunicative on this matter.
READ_ONLY = int(QFileDialog.ReadOnly)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to be read-only.

By default, this dialog is writable.
'''


HIDE_NAME_FILTER_DETAILS = int(QFileDialog.HideNameFilterDetails)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to hide pathname filter
details.

By default, this dialog displays pathname filter details.
'''


DONT_USE_CUSTOM_DIRECTORY_ICONS = int(QFileDialog.DontUseCustomDirectoryIcons)
'''
Instruct the modal dialog displayed by the
:func:`betsee.util.path.guipath.select_path` function to *only* display the
default icon for directories, in which case the
:attr:`QFileIconProvider.DontUseCustomDirectoryIcons` option will be enabled
in this dialog's underlying icon provider.

By default, this dialog displays custom icons for directories on platforms
supporting this feature. Note, however, that lookup of these icons may impose
non-negligible performance impacts over network or removable drives.
'''
