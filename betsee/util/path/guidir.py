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
from betse.util.type.types import type_check, StrOrNoneTypes

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
def select_subdir(
    init_pathname: str, parent_dirname: str, *args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing subdirectory of
    the parent directory with the passed path, returning the relative pathname
    of this subdirectory with respect to this parent directory if this dialog
    was not cancelled *or* ``None`` otherwise (i.e., if this dialog was
    cancelled).

    Parameters
    ----------
    init_pathname : str
        Absolute or relative pathname of the subdirectory to initially display
        in this dialog. If this pathname is relative, this pathname is
        interpreted as relative to the ``parent_dirname`` parameter.
    parent_dirname : str
        Absolute pathname of the parent directory to select a subdirectory of.

    All remaining paremeters are passed as is to the :func:`guipath.select_path`
    function.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * If this dialog was confirmed, the absolute pathname of this
          subdirectory.
        * If this dialog was cancelled, ``None``.
    '''

    # Avoid circular import dependencies.
    from betsee.util.path import guipath

    # If no title was passed, default to a sensible title.
    if 'dialog_title' not in kwargs:
        kwargs['dialog_title'] = QCoreApplication.translate(
            'select_subdir', 'Select Subdirectory')

    # Return the user-based result of displaying this path dialog.
    return guipath.select_path(
        *args,
        dialog_callable=QFileDialog.getExistingDirectory,

        # Options with which to initialize this dialog. Specifically:
        #
        # * "ShowDirsOnly", both preventing users from selecting non-directory
        #   files and permitting Qt to display a native rather than non-native
        #   directory dialog. By default, this static function permits users to
        #   select any arbitrary file or directory *AND* prevents Qt from
        #   displaying a native dialog -- which, frankly, defeats the purpose.
        dialog_options=QFileDialog.ShowDirsOnly,

        # Passed pathnames unmodified.
        init_pathname=init_pathname,
        parent_dirname=parent_dirname,

        # Require these subdirectories to reside in this parent directory.
        is_subpaths=True,
        **kwargs)
