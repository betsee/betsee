#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based file functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtWidgets import QFileDialog
from betse.util.path import dirs, pathnames, paths
from betse.util.type import sequences
from betse.util.type.text import strs
from betse.util.type.types import (
    type_check,
    CallableTypes,
    IntOrNoneTypes,
    MappingType,
    MappingOrNoneTypes,
    NoneType,
    StrOrNoneTypes,
)
from betsee.util.app import guiappwindow

# ....................{ CALLERS                            }....................
@type_check
def select_path(
    # Mandatory parameters.
    dialog_callable: CallableTypes,
    dialog_title: str,

    # Optional parameters.
    dialog_options: (QFileDialog.Option, NoneType) = None,
    init_pathname: StrOrNoneTypes = None,
    parent_dirname: StrOrNoneTypes = None,
    is_subpaths: bool = False,
    label_to_filetypes: MappingOrNoneTypes = None,
) -> StrOrNoneTypes:
    '''
    Absolute or relative pathname of a path interactively selected by the end
    user from a dialog displayed by calling the passed static getter of the
    :class:`QFileDialog` class (e.g., :func:`QFileDialog.getOpenFileName`)
    configured with the passed parameters if this dialog was not cancelled *or*
    ``None`` otherwise (i.e., if this dialog was cancelled).

    Constraints
    ----------
    Whether the pathname returned by this function is absolute or relative *and*
    whether the initial pathname accepted by this function is required to be
    absolute or relative depends on which optional parameters are passed.

    Specifically:

    * If the ``parent_dirname`` parameter is non-``None``:
      * The returned pathname is either:
        * If this path resides in this parent directory or a subdirectory
          thereof, relative to the absolute pathname of this parent directory.
        * Else, absolute.
      * If the ``init_pathname`` parameter is also non-``None``, this pathname
        may be either:
        * Relative, in which case this pathname is interpreted as relative to
          the absolute pathname of this parent directory.
        * Absolute, in which case this pathname is preserved as is.
    * Else (i.e., if the ``parent_dirname`` parameter is ``None``):
      * The returned pathname is absolute.
      * If the ``init_pathname`` parameter is non-``None``, this pathname *must*
        also be absolute. If this is *not* the case, an exception is raised.

    Parameters
    ----------
    dialog_callable : CallableTypes
        Static getter function of the :class:`QFileDialog` class to be called by
        this function (e.g., :func:`QFileDialog.getOpenFileName`).
    dialog_title : str
        Human-readable title of this dialog.
    dialog_options : (QFileDialog.Option, NoneType)
        *Bit field* (i.e., integer OR-ed together from mutually exclusive bit
        flags ala C-style enumeration types) of all :attr:`QFileDialog.Option`
        flags with which to configure this dialog. Defaults to ``None``, in
        which case this dialog defaults to the default configuration.
    init_pathname : StrOrNoneTypes
        Absolute or relative pathname of the path of arbitrary type (e.g., file,
        directory) to initially display in this dialog. Defaults to ``None``, in
        which case the pathname selected by the most recent call of this
        function is defaulted to.
    parent_dirname : StrOrNoneTypes
        Absolute pathname of the parent directory to select a path from.
        Defaults to ``None``, in which case no parental constraint is applied.
        See above for details.
    is_subpaths : bool
        ``True`` only if both the ``init_pathname`` parameter *and* the returned
        selected path are required to be children of the ``parent_dirname``
        parameter (i.e., residing either in this directory or a transitive
        subdirectory of this directory). Defaults to ``False``, in which case
        these paths may reside in any directory.
    label_to_filetypes : MappingOrNoneTypes
        Dictionary mapping from a human-readable label to be displayed for each
        iterable of related filetypes selectable by this dialog (e.g.,
        ``Images``) to that iterable (e.g., ``('jpg', 'png')``) if this dialog
        selects only files of specific filetypes *or* ``None`` otherwise. If
        this dialog only selects directories, this should be ``None``. Defaults
        to ``None``, in which case all paths of the requisite type (e.g., file,
        directory) regardless of filetype are selectable.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * If this dialog was confirmed, the absolute pathname of this path.
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
        # If this parent directory is relative, raise an exception.
        pathnames.die_if_relative(parent_dirname)

        # If this parent directory does *NOT* exist, raise an exception.
        dirs.die_unless_dir(parent_dirname)

        # If this initial path is relative, expand this into an absolute
        # pathname relative to this parent directory.
        if pathnames.is_relative(init_pathname):
            init_pathname = pathnames.join(parent_dirname, init_pathname)
        # Else, this initial path is absolute. If this path is required to live
        # in this parent directory, raise an exception if this is not the case.
        elif is_subpaths:
            pathnames.die_unless_parent(
                parent_dirname=parent_dirname, child_pathname=init_pathname)

    # If this initial path does *NOT* exist, silently reduce this path to the
    # last (i.e., most deeply nested) parent directory of this path that
    # exists. This ensures this dialog opens to an existing path.
    if not paths.is_path(init_pathname):
        init_pathname = dirs.get_parent_dir_last(init_pathname)

    # List of all arguments to be passed to this dialog creation function.
    dialog_args = [
        # Parent widget of this dialog.
        guiappwindow.get_main_window(),

        # Translated title of this dialog.
        dialog_title,

        # Initial path displayed by this dialog.
        init_pathname,
    ]

    # If a dictionary of acceptable filetypes was passed...
    if label_to_filetypes is not None:
        # String listing these filetypes converted from this dictionary.
        filetypes_filter = _make_filetypes_filter(label_to_filetypes)

        # Append this string to the tuple of all arguments to pass.
        dialog_args.append(filetypes_filter)

        # Append an explicit "None" value for the following optional
        # "selectedFilter" parameter, thus assigning all subsequently appended
        # positional parameters (e.g., "dialog_options") the proper index.
        dialog_args.append(None)

    # If a bit field of dialog flags was passed, append this field to the tuple
    # of all arguments to pass.
    if dialog_options is not None:
        dialog_args.append(dialog_options)
    # logs.log_debug('QFileDialog args: %r', dialog_args)

    # Absolute pathname of the path selected by the user if this dialog was not
    # canceled *OR* the empty string otherwise.
    pathname = dialog_callable(*dialog_args)

    # If this pathname is actually a 2-tuple "(pathname, filetypes_filter)",
    # this dialog was created by a file-specific callable (e.g.,
    # QFileDialog.getOpenFileName()) rather than directory-specific callable
    # (e.g., QFileDialog.getExistingDirectory()).
    #
    # Extract this pathname from the first item of this tuple. The second item
    # of this tuple is the "filetypes_filter" substring corresponding to the
    # filetype of this file (e.g., "YAML files (*.yml *.yaml);;" for a file
    # "sim_config.yaml"). Since this substring conveys no metadata not already
    # conveyed by this filetype, this substring is safely ignorable.
    if sequences.is_sequence(pathname) and len(pathname) == 2:
        pathname = pathname[0]

    # If this dialog was canceled, silently noop.
    if not pathname:
        return None
    # Else, this dialog was *NOT* canceled.

    # If a parent directory was passed...
    if parent_dirname is not None:
        # If this path lives in this parent directory, reduce this path to a
        # relative pathname relative to this parent directory.
        if pathnames.is_parent(
            parent_dirname=parent_dirname, child_pathname=pathname):
            pathname = pathnames.relativize(
                src_dirname=parent_dirname, trg_pathname=pathname)
        # ELse, this path does *NOT* live in this parent directory. If this path
        # is required to do so, raise an exception.
        elif is_subpaths:
            pathnames.die_unless_parent(
                parent_dirname=parent_dirname, child_pathname=init_pathname)

    # Return this pathname.
    return pathname

# ....................{ PRIVATE ~ makers                   }....................
@type_check
def _make_filetypes_filter(label_to_filetypes: MappingType) -> str:
    '''
    ``;;``-delimited string of all filetypes (e.g.,
    ``All files (*);; YAML files (*.yaml *.yml)``) specified by the passed
    dictionary, syntactically conforming to the Qt-specific format supported by
    the :class:`QFileDialog` class.

    Parameters
    ----------
    label_to_filetypes : MappingType
        Dictionary mapping from a human-readable label to be displayed for each
        iterable of related filetypes selectable by this dialog (e.g.,
        ``Images``) to that iterable (e.g., ``('jpg', 'png')``).

    Returns
    ----------
    str
        ``;;``-delimited string of all filetypes specified by this dictionary.
    '''

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

    # Return this Qt-formatted string.
    return filetypes_filter
