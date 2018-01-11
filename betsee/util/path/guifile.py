#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based file functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QFileDialog
# from betse.util.io.log import logs
from betse.lib.pil import pils
from betse.lib.yaml import yamls
from betse.util.path import dirs, pathnames
from betse.util.type.text import strs
from betse.util.type.types import (
    type_check,
    CallableTypes,
    MappingOrNoneTypes,
    # SequenceTypes,
    StrOrNoneTypes,
)
from betsee.util.app import guiappwindow

# ....................{ GLOBALS                            }....................
_YAML_LABEL_TO_FILETYPES = {'YAML files': yamls.FILETYPES,}
'''
Dictionary mapping from a human-readable label to be displayed for each
iterable of YAML-specific filetypes accepted by this dialog to that iterable.
'''

# ....................{ SELECTORS ~ read                   }....................
@type_check
def select_file_read(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute or relative filename of this file if this dialog was not cancelled
    *or* ``None`` otherwise (i.e., if this dialog was cancelled).

    Parameters
    ----------
    All paremeters are passed as is to the :func:`_call_file_dialog_func`
    function. Note that:

    * The ``title`` parameter *must* be passed by the caller.
    * The ``file_dialog_func`` parameter must *not* be passed by the caller.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * If this dialog was confirmed, the absolute filename of this file.
        * If this dialog was cancelled, ``None``.
    '''

    return _call_file_dialog_func(
        *args, file_dialog_func=QFileDialog.getOpenFileName, **kwargs)


@type_check
def select_file_yaml_read(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing YAML file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute or relative filename of this file if this dialog was not cancelled
    *or* ``None`` otherwise (i.e., if this dialog was cancelled).

    See Also
    ----------
    :func:`select_file_read`
        Further details.
    '''

    return select_file_read(
        *args, label_to_filetypes=_YAML_LABEL_TO_FILETYPES, **kwargs)


@type_check
def select_image_read(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing image file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute or relative filename of this file if this dialog was not cancelled
    *or* ``None`` otherwise (i.e., if this dialog was cancelled).

    For generality, this dialog recognizes all image filetypes recognized by the
    third-party image processing framework leveraged by BETSE itself: Pillow.
    BETSE defers to this framework for most low-level image I/O operations.
    Deferring to the same framework guarantees parity with BETSE behaviour.

    See Also
    ----------
    :func:`select_file_read`
        Further details.
    '''

    # If no title was passed, default to a sensible title.
    if 'title' not in kwargs:
        kwargs['title'] = QCoreApplication.translate(
            'select_image_read', 'Select Image')

    # Select an image for reading and return the filename of this image.
    return select_file_read(
        *args,
        label_to_filetypes={'Image files': pils.get_filetypes(),},
        **kwargs)

# ....................{ SELECTORS ~ save                   }....................
@type_check
def select_file_save(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an arbitrary file (either
    existing or non-existing) to be subsequently opened for in-place saving and
    hence overwriting, returning the absolute filename of this file if this
    dialog was not cancelled *or* ``None`` otherwise (i.e., if this dialog was
    cancelled).

    If this file already exists, this dialog additionally requires the user to
    accept the subsequent overwriting of this file.

    See Also
    ----------
    :func:`select_file_read`
        Further details.
    '''

    return _call_file_dialog_func(
        *args, file_dialog_func=QFileDialog.getSaveFileName, **kwargs)


@type_check
def select_file_yaml_save(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing YAML file to be
    subsequently opened for in-place saving and hence overwriting, returning the
    absolute filename of this file if this dialog was not cancelled *or* ``None``
    otherwise (i.e., if this dialog was cancelled).

    See Also
    ----------
    :func:`select_file_save`
        Further details.
    '''

    return select_file_save(
        *args, label_to_filetypes=_YAML_LABEL_TO_FILETYPES, **kwargs)

# ....................{ CALLERS                            }....................
@type_check
def _call_file_dialog_func(
    # Mandatory parameters.
    file_dialog_func: CallableTypes,
    title: str,

    # Optional parameters.
    init_pathname: StrOrNoneTypes = None,
    parent_dirname: StrOrNoneTypes = None,
    label_to_filetypes: MappingOrNoneTypes = None,
) -> StrOrNoneTypes:
    '''
    Absolute or relative filename of a file interactively selected by the end
    user from a dialog displayed by calling the passed static getter of the
    :class:`QFileDialog` class (e.g., :func:`QFileDialog.getOpenFileName`)
    configured with the passed parameters if this dialog was not cancelled *or*
    ``None`` otherwise (i.e., if this dialog was cancelled).

    Constraints
    ----------
    Whether the filename returned by this function is absolute or relative *and*
    whether the initial pathname accepted by this function is required to be
    absolute or relative depends on which optional parameters are passed.

    Specifically:

    * If the ``parent_dirname`` parameter is non-``None``:
      * The returned filename is either:
        * If this file resides in this parent directory or a subdirectory
          thereof, relative to the absolute pathname of this parent directory.
        * Else, absolute.
      * If the ``init_pathname`` parameter is also non-``None``, this pathname
        may be either:
        * Relative, in which case this pathname is interpreted as relative to
          the absolute pathname of this parent directory.
        * Absolute, in which case this pathname is preserved as is.
    * Else (i.e., if the ``parent_dirname`` parameter is ``None``):
      * The returned filename is absolute.
      * If the ``init_pathname`` parameter is non-``None``, this pathname *must*
        also be absolute. If this is *not* the case, an exception is raised.

    Parameters
    ----------
    file_dialog_func : CallableTypes
        Static getter function of the :class:`QFileDialog` class to be called by
        this function (e.g., :func:`QFileDialog.getOpenFileName`).
    title : str
        Human-readable title of this dialog.
    init_pathname : StrOrNoneTypes
        Absolute or relative pathname of the path of arbitrary type (e.g., file,
        directory) to initially display in this dialog. Defaults to ``None``, in
        which case the pathname selected by the most recent call of this
        function is defaulted to.
    parent_dirname : StrOrNoneTypes
        Absolute pathname of the parent directory to select a file from.
        Defaults to ``None``, in which case no parental constraint is applied.
        See above for details.
    label_to_filetypes : MappingOrNoneTypes
        Dictionary mapping from a human-readable label to be displayed for each
        iterable of related filetypes accepted by this dialog (e.g., ``Images``)
        to that iterable (e.g., ``('jpg', 'png')``). Defaults to ``None``, in
        which case all files regardless of filetype are accepted.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * If this dialog was confirmed, the absolute filename of this file.
        * If this dialog was cancelled, ``None``.
    '''

    # Avoid circular import dependencies.
    from betsee.util.path import guipathsys

    # If no initial path was passed, default to a sane path. To avoid subtle
    # edge cases, do so *BEFORE* handling the passed parent directory if any.
    if init_pathname is None:
        init_pathname = guipathsys.get_path_dialog_init_pathname()

    # If no parent directory was passed...
    if parent_dirname is None:
        # If this initial pathname is relative, raise an exception. Since no
        # parent directory was passed, this pathname *CANNOT* be relativized.
        pathnames.die_if_relative(init_pathname)
    # Else, a parent directory was passed. In this case...
    else:
        # If this parent directory does *NOT* exist, raise an exception.
        dirs.die_unless_dir(parent_dirname)

        # If this initial path is relative, expand this into an absolute
        # pathname relative to this parent directory.
        if pathnames.is_relative(init_pathname):
            init_pathname = pathnames.join(parent_dirname, init_pathname)

    # List of all arguments to be passed to this dialog creation function.
    file_dialog_args = [
        # Parent widget of this dialog.
        guiappwindow.get_main_window(),

        # Translated title of this dialog.
        title,

        # Initial path displayed by this dialog.
        init_pathname,
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
                filetype if filetype == '*' else (
                    '*' + pathnames.dot_filetype(filetype))
                for filetype in filetypes_iterable
            )

            # Qt-formatted string containing this label and these filetypes.
            filetypes_filter += '{} ({});;'.format(
                filetypes_label, filetypes_listed)

        # Append this Qt-formatted string to the tuple of all arguments to pass.
        file_dialog_args.append(filetypes_filter)
        # file_dialog_args += filetypes_filter[:-len(';;')]
    # logs.log_debug('QFileDialog args: %r', file_dialog_args)

    # Absolute path of the file selected by the user if this dialog was not
    # canceled *OR* the empty string otherwise.
    #
    # Note that the second item of the tuple returned by this function is the
    # "filetypes_filter" substring corresponding to the filetype of this file
    # (e.g., "YAML files (*.yml *.yaml);;" for a file "sim_config.yaml"). Since
    # this substring conveys no metadata not already conveyed by this filetype,
    # this substring is safely ignorable.
    filename, _ = file_dialog_func(*file_dialog_args)

    # If this dialog was canceled, silently noop.
    if not filename:
        return None
    # Else, this dialog was *NOT* canceled.

    # If a parent directory was passed *AND* this file is in this directory,
    # "relativize" this filename relative to this directory.
    if parent_dirname is not None and pathnames.is_parent(
        parent_dirname=parent_dirname, child_pathname=filename):
        filename = pathnames.relativize(
            src_dirname=parent_dirname, trg_pathname=filename)

    # Return this filename.
    return filename
