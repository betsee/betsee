#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level caching functionality for this application's graphical user
interface (GUI), persisting external resources required by this GUI to
user-specific files on the local filesystem.
'''

#FIXME: O.K.; so, clearly, in the wake of recent issues surrounding cache
#descrynchronization, we need to significantly "improve our game" here.
#Specifically, we should cease raising "BetseFileException" exceptions from the
#_cache_py_qrc_file() and _cache_py_ui_file() functions when the destination
#cache files are unwritable by the current user. Instead, we note that there
#are actually two use cases that we've been largely ignoring:
#
#* Regardless of whether we are in developer or end user usage (see below),
#  perform the following behaviour immediately *AFTER* caching the
#  "data_py_qrc_filename" and "data_py_ui_filename" files:
#  * If the "dot_py_qrc_filename" file does *NOT* exist, copy from
#    "data_py_qrc_filename" to "dot_py_qrc_filename".
#  * If the "dot_py_ui_filename" file does *NOT* exist, copy from
#    "data_py_ui_filename" to "dot_py_ui_filename".
#* Change the following line found below:
#    # ...from this:
#    pys.add_import_dirname(app_meta.data_py_dirname)
#    # ...to this:
#    pys.add_import_dirname(app_meta.dot_py_dirname)
#* Developer usage, as indicated by the
#  betse.pathtree.get_git_worktree_dirname_or_none() function returning a
#  non-None value. Of course, this won't *QUITE* work as intended, as that
#  function applies only to BETSE. Generalizing that function to BETSEE as well
#  suggests that we may want to:
#  * Define a new betse.util.path.gits.get_module_worktree_dirname_or_none()
#    function accepting a single passed Python module or package object and
#    otherwise behaving similarly to the
#    betse.pathtree.get_git_worktree_dirname_or_none() function.
#  * Refactor the entire "betse.pathtree" submodule from a procedural to
#    object-oriented approach, in which case BETSEE could simply inherit
#    existing functionality. Actually, don't do this; we simply have no time.
#  In any case, when BETSEE is in "developer usage" mode:
#  * The official copies of these cached files residing under "betsee/data/"
#    should be written to. If any such file is unwritable, the existing
#    "BetseFileException" should be raised.
#* End user usage. In this case:
#  * The official copies of these cached files residing under "betsee/data/"
#    should be preserved as is rather than written to. Instead, new files
#    should be written into the "~/.betse/betsee" subdirectory (e.g.,
#    "~/.betse/betsee_ui.py"). If any such file is unwritable, the existing
#    "BetseFileException" should be raised.

#FIXME: Exceptions raised from *EXTERNAL* Python modules (e.g., the
#"pyside2uic" package) and commands (e.g., "pyside2-rcc") should be explicitly
#caught and logged as errors. Given the existence of precached files,
#user-specific caching is optional and hence should *NEVER* unexpectedly halt
#the current process unless either BETSE or BETSEE themselves are to blame.
#This implies that exception handling should be constrained to the specific
#invocations of external utilities rather than entire BETSEE methods.
#FIXME: Actually, *WAIT.* The above is certainly true when attempting to cache
#the "cache_py_qrc_filename" and "cache_py_ui_filename" files but *NOT*
#the "data_py_qrc_filename" and "data_py_ui_filename" files. Since
#the latter are mandatory, exceptions should absolutely continue to be raised
#on attempting to cache the latter.

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
    module required at runtime by this GUI, including all :mod:`PySide2`-based
    modules converted from XML-formatted files and binary resources exported by
    the external Qt Designer GUI.

    For efficiency, previously generated modules are regenerated *only* as
    needed (i.e., if older than the underlying XML files and other associated
    paths from which these modules are generated).
    '''

    # Application metadata singleton.
    app_meta = metaapp.get_app_meta()

    #FIXME: Generalize these functions to accept explicit "py_qrc_filename" and
    #"py_ui_filename" parameters.

    # Generate the requisite pure-Python modules (in any arbitrary order).
    _cache_py_qrc_file()
    _cache_py_ui_file()

    #FIXME: Avoid unconditionally overwriting user-specific files. Instead,
    #only do so conditionally if either:
    #
    #* The user-specific file in question does *NOT* exist.
    #* The application-wide file in question is newer than the corresponding
    #  user-specific file.

    # Copy each such module from its application-wide to user-specific
    # subdirectory.
    files.copy(
        src_filename=app_meta.data_py_qrc_filename,
        trg_filename=app_meta.dot_py_qrc_filename,
        is_overwritable=True,
    )
    files.copy(
        src_filename=app_meta.data_py_ui_filename,
        trg_filename=app_meta.dot_py_ui_filename,
        is_overwritable=True,
    )

    # Append the directory containing all generated user-specific modules to
    # the PYTHONPATH *AFTER* successfully generating these modules, enabling
    # these modules to be subsequently imported elsewhere in the codebase.
    pys.add_import_dirname(app_meta.dot_py_dirname)

# ....................{ CACHERS ~ private                 }....................
def _cache_py_qrc_file() -> None:
    '''
    Reuse the previously cached pure-Python :mod:`PySide2`-based module
    embedding all binary resources in this application's main Qt resource
    collection (QRC) if this module is sufficiently up-to-date (i.e., at least
    as new as all input paths required to regenerate this module) *or*
    regenerate this module from these input paths otherwise.

    Parameters
    ----------
    Raises
    ----------
    BetseFileException
        If this module is outdated (i.e., older than at least one input path
        required to regenerate this module) but is unwritable by the current
        user, in which case this module is *NOT* updateable and is thus
        desynchronized from the remainder of the codebase. Because this
        desynchronization is liable to induce subtle non-human-readable issues,
        a fatal exception is raised rather than a non-fatal warning logged.

    See Also
    ----------
    :func:`_is_output_path_outdated`
        Further details.
    '''

    # Application metadata singleton.
    app_meta = metaapp.get_app_meta()

    # List of the absolute pathnames of all input paths required to do so. For
    # efficiency, these paths are ordered according to the heuristic discussed
    # by the paths.is_mtime_recursive_older_than_paths() function.
    input_pathnames = [app_meta.data_qrc_filename,]

    # If the optional third-party dependency "pyside2-tools" is installed,
    # append the "pyside2-rcc" executable for testing as well.
    if cmds.is_command('pyside2-rcc'):
        input_pathnames.append(cmdpath.get_filename('pyside2-rcc'))

    # If this output module is at least as new as *ALL* the following paths,
    # this output module is sufficiently up-to-date and need *NOT* be
    # regenerated:
    #
    # * The input "pyside2-rcc" executable run by the
    #   psdqrc.convert_qrc_to_py_file() function called below.
    # * Any file or subdirectory in the input directory containing both this
    #   input QRC file and all resource files referenced by this file.
    if not _is_output_path_outdated(
        input_pathnames=input_pathnames,
        output_filename=app_meta.data_py_qrc_filename):
        return

    # Else, this output module is older than at least one such path, in which
    # case this output module is outdated and must be regenerated.
    guiqrc.convert_qrc_to_py_file_if_able(
        qrc_filename=app_meta.data_qrc_filename,
        py_filename=app_meta.data_py_qrc_filename)


def _cache_py_ui_file() -> None:
    '''
    Reuse the previously cached pure-Python :mod:`PySide2`-based module
    implementing the superficial construction of this application's main window
    if this module is sufficiently up-to-date (i.e., at least as new as all
    input paths required to regenerate this module) *or* regenerate this module
    from these input paths otherwise.

    Raises
    ----------
    BetseFileException
        If this module is outdated (i.e., older than at least one input path
        required to regenerate this module) but is unwritable by the current
        user, in which case this module is *NOT* updateable and is thus
        desynchronized from the remainder of the codebase. Because this
        desynchronization is liable to induce subtle non-human-readable issues,
        a fatal exception is raised rather than a non-fatal warning logged.

    See Also
    ----------
    :func:`_is_output_path_outdated`
        Further details.
    '''

    # Application metadata singleton.
    app_meta = metaapp.get_app_meta()

    # List of the absolute pathnames of all input paths required to do so. For
    # efficiency, these paths are ordered according to the heuristic discussed
    # by the paths.is_mtime_recursive_older_than_paths() function.
    input_pathnames = [
        app_meta.data_ui_filename,
        pymodule.get_filename(guiui),
        pymodule.get_dirname(PySide2),
    ]

    # If the optional third-party dependency "pyside2-tools" is installed...
    if guilib.is_runtime_optional('pyside2uic'):
        # Package installed by this dependency.
        pyside2uic = guilib.import_runtime_optional('pyside2uic')

        # Append this package's directory for testing as well.
        input_pathnames.append(pymodule.get_dirname(pyside2uic))

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
    if not _is_output_path_outdated(
        input_pathnames=input_pathnames,
        output_filename=app_meta.data_py_ui_filename):
        return

    # Else, this output module is older than at least one such path, in which
    # case this output module is outdated and must be regenerated.
    guiui.convert_ui_to_py_file_if_able(
        ui_filename=app_meta.data_ui_filename,
        py_filename=app_meta.data_py_ui_filename,
        promote_obj_name_to_class=_PROMOTE_OBJ_NAME_TO_CLASS,
    )

# ....................{ TESTERS ~ private                 }....................
@type_check
def _is_output_path_outdated(
    input_pathnames: IterableTypes, output_filename: str) -> bool:
    '''
    ``True`` only if the output path either does not exist, does but is older
    than all input paths in the passed iterable, *or* does but is an empty
    (i.e., zero-byte) file.

    If this function returns ``True``, the caller is expected to explicitly
    (re)create this output path from these input paths.

    Parameters
    ----------
    input_pathnames: IterableTypes[str]
        Iterable of the absolute or relative pathnames of all input paths
        required to (re)create this output path. For efficiency, these paths
        should be ordered according to the heuristic discussed by the
        :func:`paths.is_mtime_recursive_older_than_paths` function.
    output_filename : str
        Absolute or relative pathname of the output path.
    '''

    # Log this inspection.
    logs.log_info(
        'Synchronizing cached submodule "%s"...',
        pathnames.get_basename(output_filename))

    # Return true only if either...
    return (
        # This output module does not exist *OR*...
        not paths.is_path(output_filename) or
        # This output module does exist but is older than at least one of these
        # output paths *OR*...
        paths.is_mtime_recursive_older_than_paths(
            output_filename, input_pathnames) or
        # This output module is a zero-byte file.
        files.get_size(output_filename) == 0
    )
