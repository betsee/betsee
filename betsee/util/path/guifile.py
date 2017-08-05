#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based file functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import QFileDialog
# from betse.util.io.log import logs
# from betse.util.path import dirs, pathnames
from betse.util.type import strs
from betse.util.type.types import (
    type_check,
    CallableTypes,
    MappingOrNoneTypes,
    # SequenceTypes,
    StrOrNoneTypes,
)
from betsee.util.app.guiapp import APP_GUI

# ....................{ SELECTORS                          }....................
@type_check
def open_file(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requiring the user to select an existing file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute path of this file if this dialog was not canceled *or* ``None``
    otherwise (i.e., if this dialog was canceled).

    Parameters
    ----------
    All paremeters are passed as is to the :func:`_make_file_dialog_args`
    function.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * Absolute path of this file if the user did *not* cancel this dialog.
        * ``None`` if the user cancelled this dialog.
    '''

    return _call_file_dialog_func(
        *args, file_dialog_func=QFileDialog.getOpenFileName, **kwargs)


@type_check
def Save_file(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requiring the user to select an arbitrary file (either
    existing or non-existing) to be subsequently opened for in-place saving and
    hence overwriting, returning the absolute path of this file if this dialog
    was not canceled *or* ``None`` otherwise (i.e., if this dialog was
    canceled).

    If this file already exists, this dialog additionally requires the user to
    accept the subsequent overwriting of this file.

    Parameters
    ----------
    All paremeters are passed as is to the :func:`_make_file_dialog_args`
    function.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * Absolute path of this file if the user did *not* cancel this dialog.
        * ``None`` if the user cancelled this dialog.
    '''

    return _call_file_dialog_func(
        *args, file_dialog_func=QFileDialog.getSaveFileName, **kwargs)

# ....................{ CALLERS                            }....................
@type_check
def _call_file_dialog_func(
    # Mandatory parameters.
    file_dialog_func: CallableTypes,
    title: str,

    # Optional parameters.
    label_to_filetypes: MappingOrNoneTypes = None,
) -> StrOrNoneTypes:
    '''
    Call the passed file-oriented static getter of the :class:`QFileDialog`
    class (e.g., :func:`QFileDialog.getOpenFileName`) configured by the passed
    parameters, returning the absolute path of the file selected by the user if
    this dialog was not canceled *or* ``None`` otherwise (i.e., if this dialog
    was canceled).

    Parameters
    ----------
    file_dialog_func : CallableTypes
        Static getter function of the :class:`QFileDialog` class to be called by
        this function.
    title : str
        Human-readable title of this dialog.
    label_to_filetypes : optional[MappingType]
        Dictionary mapping from a human-readable label to be displayed for each
        iterable of related filetypes accepted by this dialog (e.g., ``Images``)
        to that iterable (e.g., ``('jpg', 'png')``) *or* ``None`` if this dialog
        unconditionally accepts all files regardless of filetype. Defaults to
        ``None``.

    Returns
    ----------
    SequenceTypes
        Sequence of such arguments.
    '''

    # Avoid circular import dependencies.
    from betsee.util.path import guipathsys

    #FIXME: Non-ideal. Ideally, the application would redisplay the same
    #directory as that displayed by the most recent "QFileDialog" instance --
    #regardless of whether that was a file- or directory-specific dialog. To do
    #so, persist the directory containing the filename returned by the most
    #recent "QFileDialog" call (e.g., QFileDialog.getOpenFileName()) to the
    #application's "QSettings" store and restore that directory on the next such
    #"QFileDialog" call.

    # Initial working directory of this dialog. For generality, assume the
    # current user's documents directory.
    start_dirname = guipathsys.get_user_docs_dirname()

    # List of all arguments to be returned.
    file_dialog_args = [
        # Parent widget of this dialog.
        APP_GUI.betsee_main_window,

        # Translated title of this dialog.
        title,

        # Initial working directory of this dialog.
        start_dirname,
    ]

    # If a dictionary of acceptable filetypes was passed, reduce this to a...
    if label_to_filetypes is not None:
        # Qt-formatted string of the form accepted by "QFileDialog".
        filetypes_filter = ''

        # For each such filetype...
        for filetypes_label, filetypes_iterable in label_to_filetypes.items():
            # String listing these filetypes, delimited by spaces and...
            filetypes_listed = strs.join_on_space(
                # Prefixed by "*." for each filetype *NOT* equal to "*", as the
                # filetype "*.*" is more restrictive and hence less desirable
                # than the filetype "*".
                filetype if filetype == '*' else '*.' + filetype
                for filetype in filetypes_iterable
            )

            # Qt-formatted string containing this label and these filetypes.
            filetypes_filter += '{} ({});;'.format(
                filetypes_label, filetypes_listed)

        # Append this Qt-formatted string to the tuple of all arguments to pass.
        file_dialog_args.append(filetypes_filter)
        # file_dialog_args += filetypes_filter[:-len(';;')]
    # logs.log_debug('QFileDialog args: %r', file_dialog_args)

    # Absolute path of the file selected by the user if this dialog was *NOT*
    # canceled *or* the empty string otherwise.
    #
    # Note that the second item of the tuple returned by this function is the
    # "filetypes_filter" substring corresponding to the filetype of this file
    # (e.g., "YAML files (*.yml *.yaml);;" for a file "sim_config.yaml"). Since
    # this substring conveys no metadata not already conveyed by this filetype,
    # this substring is safely ignorable.
    filename, _ = file_dialog_func(*file_dialog_args)

    # Return this filename if non-empty or "None" otherwise.
    return filename if filename else None
