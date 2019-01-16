#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based file functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtWidgets import QFileDialog
from betse.util.io.log import logs
from betse.util.path import dirs, pathnames, paths
from betse.util.type.iterable import sequences
from betse.util.type.numeric import bits
from betse.util.type.text import strs
from betse.util.type.types import (
    type_check,
    CallableTypes,
    MappingType,
    MappingOrNoneTypes,
    NoneType,
    StrOrNoneTypes,
)
from betsee.util.app import guiappwindow

# ....................{ CALLERS                           }....................
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
    configured with the passed parameters if this user confirmed this dialog
    *or* ``None`` otherwise (i.e., if this user cancelled this dialog).

    Constraints
    ----------
    The type of path (e.g., directory, non-directory file) that this dialog
    permits the user to select is constrained *only* by the passed
    ``dialog_callable`` and ``dialog_options`` parameters.

    Similarly, whether the returned pathname is absolute or relative *and*
    whether the passed ``init_pathname`` parameter is required to be absolute
    or relative depends on which optional parameters are passed. Specifically:

    * If the ``parent_dirname`` parameter is non-``None``, the returned
      pathname will be either:

      * If this path resides in this parent directory or a subdirectory
        thereof, relative to the absolute dirname of this parent directory.
      * Else, absolute.

    * Else, the ``parent_dirname`` parameter is ``None``. In this case, the
      returned pathname will *always* be absolute.

    Likewise, if the ``init_pathname`` parameter is non-``None``:

    * If the ``parent_dirname`` parameter is also non-``None``, the
      ``init_pathname`` parameter may be either:

      * Relative, in which case ``init_pathname`` is interpreted as relative to
        the absolute dirname of this parent directory.
      * Absolute, in which case ``init_pathname`` is preserved as is.

    * Else, the ``parent_dirname`` parameter is ``None``. In this case, if the
      ``init_pathname`` parameter is:

      * A basename (i.e., contains no directory separator), ``init_pathname``
        is interpreted as relative to the absolute dirname of the **last
        selected directory** (i.e., the directory component of the pathname
        returned by the most recent call to this function; equivalently, the
        return value of the :func:`guipathsys.get_selected_prior_dirname`
        function).
      * Relative but *not* a basename (i.e., contains one or more directory
        separators), an exception is raised. While ``init_pathname`` could
        technically be interpreted as relative to the absolute dirname of the
        last selected directory as in the prior case, doing so would be
        unlikely to yield an existing directory and hence be practically
        guaranteed of raising an even less readable exception than this. Why?
        Since the last selected directory is an arbitrary directory,
        concatenating the arbitrary subdirectory defined by ``init_pathname``
        onto that directory is unlikely to yield a meaningful pathname.
      * Absolute, ``init_pathname`` is preserved as is.

    Parameters
    ----------
    dialog_callable : CallableTypes
        Static getter function of the :class:`QFileDialog` class to be called
        by this function (e.g., :func:`QFileDialog.getOpenFileName`).
    dialog_title : str
        Human-readable title of this dialog.
    dialog_options : (QFileDialog.Option, NoneType)
        **Bit field** (i.e., integer OR-ed together from mutually exclusive bit
        flags ala C-style enumeration types) of all :attr:`QFileDialog.Option`
        flags with which to configure this dialog. Defaults to ``None``, in
        which case this dialog defaults to the default configuration.
    init_pathname : StrOrNoneTypes
        Absolute or relative pathname of the path to initially display in this
        dialog. If this path is a directory, this directory is selected and the
        basename of the current selection is the empty string; else if this
        path is a file, this file is selected. If the directory component of
        this path does *not* exist, this directory component is implicitly
        reduced with a non-fatal warning to the last (i.e., most deeply nested)
        parent directory of this path that exists to ensure this dialog opens
        onto an existing directory. Defaults to ``None``, in which case the
        last selected directory is defaulted to. (**This is currently a lie.**
        See FIXME commentary preceding the
        :func:`guipathsys.get_selected_prior_dirname` function.)
    parent_dirname : StrOrNoneTypes
        Absolute pathname of the parent directory to select a path from.
        Defaults to ``None``, in which case no parental constraint is applied.
        See above for details.
    is_subpaths : bool
        ``True`` only if both the ``init_pathname`` parameter *and* the
        returned selected path are required to be children of the
        ``parent_dirname`` parameter (i.e., residing in either this directory
        itself *or* a subdirectory of this directory). Defaults to ``False``,
        in which case these paths may reside in any directory.
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

        * If this dialog was confirmed, the absolute or relative pathname of
          the path confirmed by the end user.
        * If this dialog was cancelled, ``None``.
    '''

    # Avoid circular import dependencies.
    from betsee.util.path import guipathsys

    # True only if this dialog is selecting one or more directories, as
    # indicated by the "QFileDialog.ShowDirsOnly" bit being enabled in the
    # "dialog_options" bit field if passed. Nice, eh?
    is_dir_selection = (
        dialog_options is not None and
        bits.is_bit_on(
            bit_field=dialog_options, bit_mask=QFileDialog.ShowDirsOnly)
    )

    # Absolute dirname of the last selected directory.
    prior_dirname = guipathsys.get_selected_prior_dirname()

    # If no initial pathname was passed, default to the absolute dirname of the
    # last selected directory. To avoid subtle edge cases, do so *BEFORE*
    # handling this parent directory if any.
    if init_pathname is None:
        init_pathname = prior_dirname

    #FIXME: This function is getting rather long in this tooth. Split this
    #function up into the following subfunctions:
    #
    #* A new subfunction implementing this if conditional.
    #* A new subfunction implementing the if conditional following this one.

    # If no parent directory was passed...
    if parent_dirname is None:
        # If this initial pathname is a pure basename, canonicalize this
        # pathname into an absolute pathname relative to the last selected
        # directory.
        if pathnames.is_basename(init_pathname):
            init_pathname = pathnames.join(prior_dirname, init_pathname)
        # Else, this initial pathname contains one or more directory
        # separators. In this case...
        else:
            # If this initial pathname is relative, raise an exception. Since
            # no parent directory was passed, canonicalizing this pathname into
            # an absolute pathname is effectively infeasible.
            pathnames.die_if_relative(init_pathname)
            # Else, this initial pathname is absolute. In this case, preserve
            # this pathname as is.
    # Else, a parent directory was passed. In this case...
    else:
        # If this parent directory is relative, raise an exception.
        pathnames.die_if_relative(parent_dirname)

        # If this parent directory does *NOT* exist, raise an exception.
        dirs.die_unless_dir(parent_dirname)

        # If this initial pathname is relative, canonicalize this pathname into
        # an absolute pathname relative to this parent directory.
        if pathnames.is_relative(init_pathname):
            init_pathname = pathnames.join(parent_dirname, init_pathname)
        # Else, this initial pathname is absolute.
        #
        # If this initial pathname is required to reside in this parent
        # directory but does *NOT*, raise an exception.
        elif is_subpaths:
            pathnames.die_unless_parent(
                parent_dirname=parent_dirname, child_pathname=init_pathname)

    # Ensure this dialog opens to an existing directory but *NOT* necessarily
    # an existing file in an existing directory, which cannot be guaranteed in
    # the general case (e.g., writing a new file in an existing directory).
    #
    # If this initial path does *NOT* exist...
    if not paths.is_path(init_pathname):
        # If this dialog is selecting one or more directories, reduce this
        # dirname to the dirname of the last (i.e., most deeply nested) parent
        # directory of this dirname that exists.
        if is_dir_selection:
            init_pathname = dirs.get_parent_dir_last(init_pathname)
        # Else, this dialog is selecting one or more files. In this case...
        else:
            # Absolute dirname and basename of the initial file to select.
            init_dirname  = pathnames.get_dirname (init_pathname)
            init_basename = pathnames.get_basename(init_pathname)

            # Reduce this dirname to an existing dirname as above.
            init_dirname = dirs.get_parent_dir_last(init_dirname)

            # Sanitize the initial file by concatenating this existing dirname
            # and the original basename of this file.
            init_pathname = pathnames.join(init_dirname, init_basename)

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

    # Display this dialog and localize the absolute pathname of the path
    # selected by the user if this dialog was not canceled *OR* the empty
    # string otherwise.
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
    # conveyed by this filetype, this substring is safely ignorable. (Bad API!)
    if sequences.is_sequence(pathname) and len(pathname) == 2:
        pathname = pathname[0]

    # If this dialog was canceled, silently reduce to a noop.
    if not pathname:
        return None
    # Else, this dialog was confirmed.

    # If a parent directory was passed...
    if parent_dirname is not None:
        # If this path resides in this parent directory, reduce this path to a
        # relative pathname relative to this parent directory.
        if pathnames.is_parent(
            parent_dirname=parent_dirname, child_pathname=pathname):
            pathname = pathnames.relativize(
                src_dirname=parent_dirname, trg_pathname=pathname)
        # ELse, this path resides outside this parent directory.
        #
        # If this path is instead required to reside in this parent directory,
        # raise an exception.
        elif is_subpaths:
            pathnames.die_unless_parent(
                parent_dirname=parent_dirname, child_pathname=init_pathname)

    # Return this pathname.
    return pathname

# ....................{ PRIVATE ~ makers                  }....................
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
