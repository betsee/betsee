#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based directory functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QFileDialog
# from betse.util.io.log import logs
from betse.util.path import dirs, pathnames
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.util.app import guiappwindow

# ....................{ SELECTORS                          }....................
#FIXME: Generalize to prevent users from traversing up (but *NOT* down) the
#directory tree during subdirectory selection. Doing so is non-trivial but
#absolutely feasible, requiring:
#
#* Definition of a new "QBetseeSubFileDialog" subclass of the stock
#  "QFileDialog" class.
#* In this subclass:
#  * Define a new "self._cwd_dirname" instance variable.
#  * Define a new enter_dir() @Slot.
#  * Connect this enter_dir() @Slot to the standard "directoryEntered" signal.
#  * In this @Slot (in order):
#    1. Test whether the passed dirname is prefixed by the desired dirname.
#    2. If so, set "self._cwd_dirname" to the passed dirname.
#    3. If not:
#       1. Preserve the current "self._cwd_dirname" as is.
#       2. Call "self.setDirectory(self._cwd_dirname)".
#* Manual instantiation and configuration of a "QBetseeSubFileDialog" instance
#  rather than simply calling the QFileDialog.getExistingDirectory() getter.
#
#It's actually pretty trivial. Make it so, please. Once we do, supply the
#resulting solution to the following StackOverflow answer -- which has yet to
#receive a single solution (but actually received the prototypical snarky "Why
#do you want to do this, because you never should."-style comment):
#    https://stackoverflow.com/questions/42001425/how-to-force-qfiledialog-getopenfilename-to-read-file-only-in-a-specific-folder
#    https://stackoverflow.com/questions/12169878/limit-directory-traversal-in-qfiledialog
#
#Full credit in our answer should go to the following quasi-answer:
#    https://stackoverflow.com/a/12173504/2809027

@type_check
def select_subdir(init_dirname: str, parent_dirname: str) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing subdirectory of
    the parent directory with the passed path, returning the relative pathname
    of this subdirectory with respect to this parent directory if this dialog
    was not cancelled *or* ``None`` otherwise (i.e., if this dialog was
    cancelled).

    Parameters
    ----------
    init_dirname : str
        Absolute or relative pathname of the directory to initially display in
        this dialog. If this pathname is relative, this pathname is interpreted
        as relative to the ``parent_dirname`` parameter.
    parent_dirname : str
        Absolute pathname of the parent directory to select a subdirectory of.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * If this dialog was confirmed, the absolute pathname of this
          subdirectory.
        * If this dialog was cancelled, ``None``.
    '''

    # If this parent directory is relative, raise an exception.
    pathnames.die_if_relative(parent_dirname)

    # If this parent directory does *NOT* exist, raise an exception.
    dirs.die_unless_dir(parent_dirname)

    # If this initial directory is relative, expand this into an absolute
    # pathname relative to this parent directory.
    if pathnames.is_relative(init_dirname):
        init_dirname = pathnames.join(parent_dirname, init_dirname)

    # Absolute pathname of this initial directory reduced to the last (i.e.,
    # most deeply nested) parent directory of this directory that exists,
    # ensuring this dialog opens to an existing directory.
    init_dirname = dirs.get_parent_dir_last(init_dirname)

    # Absolute path of the subdirectory selected by the user if this dialog was
    # not canceled *OR* the empty string otherwise.
    child_dirname = QFileDialog.getExistingDirectory(
        # Parent widget of this dialog.
        guiappwindow.get_main_window(),

        # Translated title of this dialog.
        QCoreApplication.translate('select_subdir', 'Select Subdirectory'),

        # Initial working directory of this dialog.
        init_dirname,

        # Options with which to initialize this dialog. Specifically:
        #
        # * "ShowDirsOnly", both preventing users from selecting non-directory
        #   files and permitting Qt to display a native rather than non-native
        #   directory dialog. By default, this static function permits users to
        #   select any arbitrary file or directory *AND* prevents Qt from
        #   displaying a native dialog -- which, frankly, defeats the purpose.
        QFileDialog.ShowDirsOnly,
    )

    # If this dialog was canceled, silently noop.
    if not child_dirname:
        return None
    # Else, this dialog was *NOT* canceled.

    # If this directory is *NOT* a subdirectory of this parent directory, raise
    # an exception.
    pathnames.die_unless_parent(
        parent_dirname=parent_dirname, child_pathname=child_dirname)

    # Relative pathname of this subdirectory relative to this parent directory,
    # equivalent to stripping the latter from the former.
    child_dirname = pathnames.relativize(
        src_dirname=parent_dirname, trg_pathname=child_dirname)

    # Return this relative pathname.
    return child_dirname
