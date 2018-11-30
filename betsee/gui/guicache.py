#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level caching functionality for this application's graphical user
interface (GUI), persisting external resources required by this GUI to
user-specific files on the local filesystem.
'''

#FIXME: Exceptions raised from *EXTERNAL* Python modules (e.g., the
#"pyside2uic" package) and commands (e.g., "pyside2-rcc") should be explicitly
#caught and logged as errors. Given the existence of precached files,
#user-specific caching is optional and hence should *NEVER* unexpectedly halt
#the current process unless either BETSE or BETSEE themselves are to blame.
#This implies that exception handling should be constrained to the specific
#invocations of external utilities rather than entire BETSEE methods.
#FIXME: Actually, *WAIT.* The above is certainly true when attempting to cache
#the "cache_py_qrc_filename" and "cache_py_ui_filename" files but *NOT* the
#"data_py_qrc_filename" and "data_py_ui_filename" files. Since the latter are
#mandatory, exceptions should absolutely continue to be raised on attempting to
#cache the latter.
#FIXME: The simplest approach might be as follows:
#
#* Refactor all non-fatal warnings currently emitted by low-level "guiqrc" and
#  "guiui" functions into fatal exceptions.
#* If under non-developer mode, explicitly catch *ALL* exceptions raised by the
#  calls to these functions below.

#FIXME: Still insufficient. Why? Because we need to automatically invalidate
#caches whenever any file in the BETSEE codebase changes. *sigh*

# ....................{ IMPORTS                           }....................
import PySide2
from betse import metaapp
from betse.util.io.log import logs
from betse.util.path import files, paths, pathnames
from betse.util.path.command import cmds, cmdpath
from betse.util.py import pymodule, pys
from betse.util.type.types import type_check, IterableTypes
from betsee.gui.simconf.stack.widget.guisimconfradiobtn import (
    QBetseeSimConfEnumRadioButtonGroup)
from betsee.lib import guilib
from betsee.util.io.xml import guiqrc, guiui

# ....................{ GLOBALS                           }....................
#FIXME: When upstream permits "QButtonGroup" widgets to be promoted via
#Qt (Creator|Designer), remove this ad-hack kludge.
_PROMOTE_OBJ_NAME_TO_CLASS = {
    # Manually promoto "QButtonGroup" widgets to application-specific types.
    'sim_conf_space_intra_lattice_type': QBetseeSimConfEnumRadioButtonGroup,
}
'''
Dictionary mapping from the name of each instance variable of the main window
to the application-specific widget subclass to declare that variable to be an
instance of.

This dictionary facilitates the manual "promotion" of widgets for which the
Qt (Creator|Designer) GUI currently provides no means of official promotion,
notably including :class:`QButtonGroup` widgets.
'''

# ....................{ CACHERS                           }....................
def cache_py_files() -> None:
    '''
    Either create and cache *or* reuse each previously cached pure-Python
    submodule required at runtime by this GUI, including :mod:`PySide2`-based
    submodules converted from XML-formatted files and binary resources exported
    by the external Qt (Creator|Designer) GUI.

    For efficiency, previously generated modules are regenerated *only* as
    needed (i.e., if older than the underlying XML files and other associated
    paths from which these modules are generated).
    '''

    # Application metadata singleton.
    app_meta = metaapp.get_app_meta()

    # If this application has a Git-based working tree, assume this application
    # to be under development by a non-end user developer. In this case,
    # (re)generate *ALL* pure-Python cached submodules (including both
    # application-wide *AND* user-specific) from their input XML files.
    if app_meta.is_git_worktree:
        _cache_py_files_dev()
        # _cache_py_files_user()
    # Else, this application has no such tree. In this case, assuming this
    # application to be in use by a non-developer end user, (re)generate only
    # user-specific pure-Python cached submodules from their input XML files.
    else:
        _cache_py_files_user()

    # Append the directory containing all generated user-specific submodules to
    # the ${PYTHONPATH} *AFTER* successfully making these submodules, enabling
    # these submodules to be subsequently imported elsewhere in the codebase.
    pys.add_import_dirname(app_meta.dot_py_dirname)


def _cache_py_files_dev() -> None:
    '''
    Either create and cache *or* reuse each previously cached pure-Python
    submodule required at runtime by this GUI, including both application-wide
    submodules bundled in this application's package *and* user-specific
    submodules residing in a dot directory under this user's home directory.

    Caveats
    ----------
    **This function should only be called if this application has a Git-based
    working tree,** in which case this application is assumed to be under
    development by a non-end user developer.
    '''

    # Log this caching.
    logs.log_info('Synchronizing Git-cached submodules...')

    # Application metadata singleton.
    app_meta = metaapp.get_app_meta()

    # (Re)cache *ALL* application-wide submodules (in arbitrary order).
    _cache_py_qrc_file(
        qrc_filename=app_meta.data_qrc_filename,
        py_filename=app_meta.data_py_qrc_filename)
    _cache_py_ui_file(
        ui_filename=app_meta.data_ui_filename,
        py_filename=app_meta.data_py_ui_filename)

    # (Re)cache *ALL* user-specific submodules (in arbitrary order). For
    # simplicity, simply replace these files with their application-wide
    # equivalents cached above.
    files.copy_overwritable(
        src_filename=app_meta.data_py_qrc_filename,
        trg_filename=app_meta.dot_py_qrc_filename)
    files.copy_overwritable(
        src_filename=app_meta.data_py_ui_filename,
        trg_filename=app_meta.dot_py_ui_filename)


def _cache_py_files_user() -> None:
    '''
    Either create and cache *or* reuse each previously cached pure-Python
    submodule required at runtime by this GUI, including only user-specific
    submodules residing in a dot directory under this user's home directory but
    *not* application-wide submodules bundled in this application's package.

    Caveats
    ----------
    For safety, this function only logs non-fatal warnings rather than raising
    exceptions. This function only creates optional user-specific submodules
    rather than mandatory application-wide submodules. While lamentable, any
    issues in this function (e.g., an inability to write user-specific
    submodules due to petty ownership or permission conflicts) should be
    confined to this function rather than halting the entire application.
    '''

    # Log this caching.
    logs.log_info('Synchronizing user-cached submodules...')

    # Application metadata singleton.
    app_meta = metaapp.get_app_meta()

    # Attempt to (re)cache the user-specific QRC submodule.
    try:
        _cache_py_qrc_file(
            qrc_filename=app_meta.data_qrc_filename,
            py_filename=app_meta.dot_py_qrc_filename)
    # If doing so fails for *ANY* reason whatsoever...
    except Exception as exception:
        # Log this exception as a non-fatal warning.
        logs.log_warning('Skipping! ' + str(exception))

        # Fallback to simply replacing this submodule with its application-wide
        # equivalent bundled with this application.
        files.copy_overwritable(
            src_filename=app_meta.data_py_qrc_filename,
            trg_filename=app_meta.dot_py_qrc_filename)

    # Attempt to (re)cache the user-specific UI submodule.
    try:
        _cache_py_ui_file(
            ui_filename=app_meta.data_ui_filename,
            py_filename=app_meta.dot_py_ui_filename)
    # If doing so fails for *ANY* reason whatsoever...
    except Exception as exception:
        # Log this exception as a non-fatal warning.
        logs.log_warning('Skipping! ' + str(exception))

        # Fallback to simply replacing this submodule with its application-wide
        # equivalent bundled with this application.
        files.copy_overwritable(
            src_filename=app_meta.data_py_ui_filename,
            trg_filename=app_meta.dot_py_ui_filename)

# ....................{ CACHERS ~ private                 }....................
@type_check
def _cache_py_qrc_file(qrc_filename: str, py_filename: str) -> None:
    '''
    Reuse the previously cached pure-Python :mod:`PySide2`-based submodule
    embedding all binary resources in this application's main Qt resource
    collection (QRC) with the passed filename if that submodule is sufficiently
    up-to-date (i.e., at least as new as all input paths required to regenerate
    that submodule) *or* regenerate this submodule from these input paths
    otherwise, principally including the input QRC file with the passed
    filename.

    Parameters
    ----------
    qrc_filename : str
        Absolute or relative filename of the input ``.qrc``-suffixed file.
    py_filename : str
        Absolute or relative filename of the output ``.py``-suffixed file.

    Raises
    ----------
    BetseCommandException
        If the ``pyside2-rcc`` command installed by the optional third-party
        dependency ``pyside2-tools`` is *not* in the current ``${PATH}``.

    See Also
    ----------
    :func:`guiqrc.convert_qrc_to_py_file`
        Further details.
    '''

    # List of the absolute pathnames of all input paths required to do so. For
    # efficiency, these paths are ordered according to the heuristic discussed
    # by the paths.is_mtime_recursive_older_than_paths() function.
    src_pathnames = [
        qrc_filename,
        pymodule.get_filename(guiqrc),
        cmdpath.get_filename('pyside2-rcc'),
    ]

    # If this output module is at least as new as *ALL* the following paths,
    # this output module is sufficiently up-to-date and need *NOT* be
    # regenerated:
    #
    # * The input "pyside2-rcc" executable run by the
    #   psdqrc.convert_qrc_to_py_file() function called below.
    # * Any file or subdirectory in the input directory containing both this
    #   input QRC file and all resource files referenced by this file.
    if not _is_trg_file_stale(
        src_pathnames=src_pathnames, trg_filename=py_filename):
        return

    # Else, this output module is older than at least one such path, in which
    # case this output module is outdated and must be regenerated.
    guiqrc.convert_qrc_to_py_file(
        qrc_filename=qrc_filename, py_filename=py_filename)


@type_check
def _cache_py_ui_file(ui_filename: str, py_filename: str) -> None:
    '''
    Reuse the previously cached pure-Python :mod:`PySide2`-based submodule
    implementing the superficial construction of this application's main window
    if that submodule is sufficiently up-to-date (i.e., at least as new as all
    input paths required to regenerate that submodule) *or* regenerate that
    submodule from these input paths otherwise, principally including the input
    UI file with the passed filename.

    Parameters
    ----------
    ui_filename : str
        Absolute or relative filename of the input ``.ui``-suffixed file.
    py_filename : str
        Absolute or relative filename of the output ``.py``-suffixed file.

    Raises
    ----------
    ImportError
        If the :mod:`pyside2uic` package installed by the optional third-party
        dependency ``pyside2-tools`` is *not* importable.

    See Also
    ----------
    :func:`guiui.convert_ui_to_py_file`
        Further details.
    '''

    # "pyside2uic" package installed by the "pyside2-tools" dependency.
    pyside2uic = guilib.import_runtime_optional('pyside2uic')

    # List of the absolute pathnames of all input paths required to do so. For
    # efficiency, these paths are ordered according to the heuristic discussed
    # by the paths.is_mtime_recursive_older_than_paths() function.
    src_pathnames = [
        ui_filename,
        pymodule.get_filename(guiui),
        pymodule.get_dirname(PySide2),
        pymodule.get_dirname(pyside2uic),
    ]

    # If this output module is at least as new as *ALL* the following paths,
    # this output module is sufficiently up-to-date and need *NOT* be
    # regenerated:
    #
    # * This input UI file.
    # * The file providing the submodule of this application converting this UI
    #   file into a Python module.
    # * Any file or subdirectory in the input directories containing the
    #   "PySide2" and "pyside2uic" packages required by the
    #   psdui.convert_ui_to_py_file() function called below.
    if not _is_trg_file_stale(
        src_pathnames=src_pathnames, trg_filename=py_filename):
        return

    # Else, this output module is older than at least one such path, in which
    # case this output module is outdated and must be regenerated.
    guiui.convert_ui_to_py_file(
        ui_filename=ui_filename,
        py_filename=py_filename,
        promote_obj_name_to_class=_PROMOTE_OBJ_NAME_TO_CLASS,
    )

# ....................{ TESTERS ~ private                 }....................
@type_check
def _is_trg_file_stale(
    src_pathnames: IterableTypes, trg_filename: str) -> bool:
    '''
    ``True`` only if the passed target file either does not exist, does exist
    but is a directory, does exist but is **empty** (i.e., zero-byte), *or*
    does exist but is older than all source paths in the passed iterable.

    If this function returns ``True``, the caller is expected to explicitly
    (re)create this target file from these source paths.

    Parameters
    ----------
    src_pathnames: IterableTypes[str]
        Iterable of the absolute or relative pathnames of all source paths
        required to (re)create this target file. For efficiency, these paths
        should be ordered according to the heuristic discussed by the
        :func:`paths.is_mtime_recursive_older_than_paths` function.
    trg_filename : str
        Absolute or relative filename of the target file.

    Returns
    ----------
    bool
        ``True`` only if this target file either:

        * Does *not* exist.
        * Does exist but is a directory.
        * Does exist but is an **empty file** (i.e., zero-byte).
        * Does exist but is older than all such source paths.
    '''

    # Log this inspection.
    logs.log_info(
        'Synchronizing cached submodule "%s"...',
        pathnames.get_basename(trg_filename))

    # Return true only if either...
    return (
        # This target file does not exist or does but is *NOT* a file *OR*...
        not files.is_file(trg_filename) or
        # This target file is empty.
        files.is_empty(trg_filename) or
        # This target file does exist but is older than at least one of these
        # source paths *OR*...
        paths.is_mtime_recursive_older_than_paths(trg_filename, src_pathnames)
    )
