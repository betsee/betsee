#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based directory functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QFileDialog
# from betse.util.io.log import logs
from betse.util.path import dirs, pathnames
from betse.util.type.types import type_check  #, GeneratorType
from betsee.util.app.guiapp import APP_GUI

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
def select_subdir(parent_dirname: str, current_dirname: str) -> str:
    '''
    Display a dialog requiring the user to select an existing subdirectory of
    the parent directory with the passed path, returning the relative path of
    this subdirectory with respect to this parent directory.

    Parameters
    ----------
    parent_dirname : str
        Absolute path of the parent directory to select a subdirectory of.
    current_dirname : str
        Absolute path of the directory to initially display in this dialog.

    Returns
    ----------
    str
        Relative path of an existing subdirectory of this parent directory.
    '''

    # If either of these directories are relative, raise an exception.
    pathnames.die_if_relative(parent_dirname)

    # If this parent directory does not exist, raise an exception.
    dirs.die_unless_dir(parent_dirname)

    #FIXME: Non-ideal. Ideally, if this current directory does not exist, we
    #should instead iteratively find the first parent directory of this current
    #directory that does exist, halting at the passed "parent_dirname".

    # If this current directory does not exist, fallback to this existing parent
    # directory as the current directory.
    if not dirs.is_dir(current_dirname):
        current_dirname = parent_dirname

    # Absolute path of the subdirectory selected by the user.
    child_dirname = QFileDialog.getExistingDirectory(
        # Parent widget of this dialog.
        APP_GUI.betsee_main_window,

        # Translated title of this dialog.
        QCoreApplication.translate('select_subdir', 'Select Subdirectory'),

        # Working directory of this dialog.
        current_dirname,

        # Options with which to initialize this dialog. Specifically:
        #
        # * "ShowDirsOnly", both preventing users from selecting non-directory
        #   files and permitting Qt to display a native rather than non-native
        #   directory dialog. By default, this static function permits users to
        #   select any arbitrary file or directory *AND* prevents Qt from
        #   displaying a native dialog -- which, frankly, defeats the purpose.
        QFileDialog.ShowDirsOnly,
    )

    # If this directory is *NOT* a subdirectory of this parent directory, raise
    # an exception.
    pathnames.die_unless_parent(
        parent_dirname=parent_dirname, child_pathname=child_dirname)

    # Relative path of this subdirectory relative to this parent directory,
    # equivalent to stripping the latter from the former.
    child_dirname_relative = pathnames.relativize(
        trg_pathname=child_dirname, src_dirname=parent_dirname)

    # Return this relative path.
    return child_dirname_relative