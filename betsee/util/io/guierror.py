#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level :mod:`QMessageBox`-based error handling facilities.

See Also
----------
:mod:`betsee.util.widget.guimessage`
    Error-agnostic :class:`QMessageBox` facilities.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT*
#   include BETSE modules, which are *NOT* guaranteed to exist at this point.
#   For simplicity, however, all core PySide2 submodules are assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import re, sys, traceback
from PySide2.QtWidgets import QMessageBox
from betse.util.type.obj import objects
from betsee.util.app import guiapp

# ....................{ INSTALLERS                        }....................
def install_exception_hook() -> None:
    '''
    Install a global exception hook overriding :mod:`PySide2`'s default insane
    exception handling behaviour with sane exception handling.

    By default, :mod:`PySide2`:

    #. Catches **uncaught exceptions** (i.e., exceptions automatically
       propagated up the call stack without being caught) raised during the
       GUI's event loop processing.
    #. Prints the tracebacks for these exceptions to standard error.
    #. Ignores these exceptions by silently returning control back to the main
       event handling loop.

    This behaviour is entirely invisible to end users and hence insane. This
    function addresses this by installing a new handler both interactively
    displaying *and* non-interactively logging exceptions.

    Caveats
    ----------
    Ideally, this function should be called *before* entering this event loop
    (i.e., calling the :meth:`betsee.util.app.guiapp.GUI_APP._exec` method).
    '''

    # Default insane global exception hook, preserved in case of catastrophe.
    default_exception_handler = sys.excepthook

    # Custom sane global exception hook implemented as a closure requiring this
    # default insane global exception hook as a fallback.
    def exception_hook(exception_type, exception, exception_traceback):
        '''
        Application-specific global exception hook.

        See Also
        ----------
        :func:`install_handler`
            Further details.
        '''

        # Attempt to...
        try:
            # Import from BETSE. Since this hook should only ever be installed
            # *AFTER* BETSE is validated to be importable, this should succeed.
            from betse.util.io.log import logs

            # Log this exception.
            logs.log_exception(exception)

            # Display a PySide2-based message box displaying this exception.
            show_exception(exception)
        # If this exception handling itself raises an exception...
        except Exception as exception_exception:
            # Defer to the default global exception hook, presumably printing
            # both this new and the prior exception to stderr.
            default_exception_handler(
                type(exception_exception),
                exception_exception,
                traceback.extract_stack(exception_exception))

            # Exit the current application with failure status.
            sys.exit(1)

    # Replace the default global exception hook with this handler.
    sys.excepthook = exception_hook

# ....................{ SHOWERS                           }....................
def show_error(
    # Mandatory parameters.
    title: str,
    synopsis: str,

    # Optional parameters.
    exegesis: str = None,
    details: str = None,
) -> None:
    '''
    Display the passed error message(s) as a :mod:`QMessageBox`-driven modal
    message box of the :class:`QApplication` singleton for this application.

    Caveats
    ----------
    This function necessarily instantiates and initializes this singleton if
    needed. Doing so commonly invites chicken-and-egg issues between the
    :func:`init` and :func:`betse.lib.libs.reinit` methods and hence is
    inadvisable; in this case, however, the need to instantiate this singleton
    to display critical errors subsumes the need to instantiate this singleton
    in a more controlled manner.

    Parameters
    ----------
    title : str
        Title of this error to be displayed as the title of this message box.
    synopsis : str
        Synopsis of this error to be displayed as the text of this message box.
    exegesis : optional[str]
        Exegesis (i.e., explanation) of this error to be displayed as the
        so-called "informative text" of this message box below the synopsis of
        this error. Defaults to ``None``, in which case no such text is
        displayed.
    details : optional[str]
        Technical details of this error to be displayed as the so-called
        "detailed text" of this message box in monospaced font below both the
        synopsis and exegesis of this error in a discrete fold-down text area.
        Defaults to ``None``, in which case no such text is displayed.
    '''

    # Type check manually.
    assert isinstance(title,    str), '"{}" not a string.'.format(title)
    assert isinstance(synopsis, str), '"{}" not a string.'.format(synopsis)

    # Maximum number of characters to which each passed string is truncated
    # prior to display. Attempting to display untruncated long strings
    # typically induces non-human-readable application failure (e.g.,
    # segmentation faults, infinite loops) under Qt, which is bad.
    TITLE_MAX_LEN    = 80     # standard UNIX terminal line length
    SYNOPSIS_MAX_LEN = 80*8   # sensible number of sentences of that length
    EXEGESIS_MAX_LEN = 80*16
    DETAILS_MAX_LEN  = 80*32

    # Instantiate and initialize the "QApplication" singleton for this
    # application if needed *BEFORE* creating children widgets of this
    # singleton. Failure to do so typically results in non-human-readable
    # segmentation faults from Qt itself resembling:
    #
    #    QWidget: Must construct a QApplication before a QWidget
    #    [1]    30475 abort      betsee -v
    guiapp.init()

    # For safety, truncate this title and synopsis to lengths defined above.
    title_truncated    = _truncate(text=title,    max_len=TITLE_MAX_LEN)
    synopsis_truncated = _truncate(text=synopsis, max_len=SYNOPSIS_MAX_LEN)

    # Message box displaying this error.
    error_box = QMessageBox()
    error_box.setWindowTitle(title_truncated)
    error_box.setText(synopsis_truncated)
    error_box.setIcon(QMessageBox.Critical)
    error_box.setStandardButtons(QMessageBox.Ok)

    # If this exception provides an optional exegesis...
    if exegesis is not None:
        assert isinstance(exegesis, str), '"{}" not a string.'.format(exegesis)

        # For safety, truncate this metadata as above.
        exegesis_truncated = _truncate(text=exegesis, max_len=EXEGESIS_MAX_LEN)

        # Display this metadata.
        error_box.setInformativeText(exegesis_truncated)

    # If this exception provides optional details...
    if details is not None:
        assert isinstance(details, str), '"{}" not a string.'.format(details)

        # For safety, truncate this metadata as above.
        details_truncated = _truncate(text=details, max_len=DETAILS_MAX_LEN)

        # Display this metadata.
        error_box.setDetailedText(details_truncated)

    # Finalize this message box *AFTER* setting all widget proporties above.
    error_box.show()

    # Run this application's event loop, displaying this message box.
    error_box.exec_()


def show_exception(exception: Exception) -> None:
    '''
    Display the passed exception as a :mod:`QMessageBox`-driven modal message
    box in the current application widget, creating this widget if necessary.

    Parameters
    ----------
    exception : Exception
        Exception to be displayed.
    '''

    # Type check manually.
    assert isinstance(exception, Exception), (
        '"{}" not an exception.'.format(exception))

    # Human-readable synopsis and exegesis of this exception if defined (e.g.,
    # if this exception is an instance of the "BetseeException" superclass)
    # *OR* "None" otherwise.
    exception_synopsis = getattr(exception, 'synopsis', None)
    exception_exegesis = getattr(exception, 'exegesis', None)

    # If this exception defines no synopsis...
    if exception_synopsis is None:
        # Default this synopsis to the contents of this exception.
        exception_synopsis = str(exception)

        # If this exception has no contents, default this synopsis to the type
        # of this exception. While non-ideal, something is better than nothing;
        # moreover, this edge case is rather rare.
        if not exception_synopsis:
            exception_synopsis = objects.get_class_name_unqualified(exception)

    # If this exception has a human-readable title, use this title as is.
    if hasattr(exception, 'title'):
        exception_title = exception.title
    # Else, synthesize this title from metadata associated with this exception.
    else:
        # Class name of this exception.
        exception_classname = type(exception).__name__

        # Human-readable title of this exception, synthesized from this
        # machine-readable class name by inserting spaces between all
        # boundaries between non-capitalized and capitalized letters (e.g.,
        # from "ValueError" to "Value Error").
        exception_title = re.sub(
            r'([a-z])([A-Z])', r'\1 \2', exception_classname,)

    # Attempt to obtain an exception traceback via BETSE, which is *NOT*
    # guaranteed to exist at this point.
    try:
        from betse.util.io import ioexceptions
        _, exception_traceback = ioexceptions.get_metadata(exception)
    # If BETSE is unimportable, ignore this exception traceback.
    except ImportError:
        exception_traceback = None

    # Display this exception as a message box.
    show_error(
        title=exception_title,
        synopsis=exception_synopsis,
        exegesis=exception_exegesis,
        details=exception_traceback,
    )

# ....................{ TRUNCATERS                        }....................
def _truncate(text: str, max_len: int) -> str:
    '''
    Passed string truncated to the passed maximum length by replacing the
    substring of this string exceeding that length with the conventional ASCII
    ellipses (i.e., ``...``).

    Parameters
    ----------
    text : str
        String to be truncated.
    max_len : int
        Maximum number of characters to truncate this string to.

    Returns
    ----------
    str
        Passed string truncated to this maximum length, as detailed above.

    See Also
    ----------
    :func:`betse.util.type.text.strs.truncate`
        General-purpose truncater from which this error-specific equivalent is
        derived. As the top-level of this submodule suggests, BETSE modules are
        *not* guaranteed to exist at this point. Ergo, this function pastes the
        :func:`betse.util.type.text.strs.truncate` function into this codebase.
    '''

    # Substring to replace the truncated portion of this string with.
    replacement = '...'

    # If this string does *NOT* exceed this maximum, return this string as is.
    if len(text) <= max_len:
        return text
    # Else, this string exceeds this maximum. In this case...
    else:
        # Number of characters to truncate from the end of this string.
        # Dismantled, this is:
        #
        # * "len(text) - max_len", the number of characters that this string
        #   exceeds this maximum length by.
        # * "... + len(replacement)", truncating an additional number of
        #   characters equal to the length of this replacement so as to make
        #   sufficient room for this replacement at the end of this string
        #   without exceeding this maximum length.
        #
        # Note that this number is guaranteed to be non-negative (i.e., greater
        # than zero), as "len(text) > max_len" and "len(replacement) >= 0".
        truncate_chars_count = len(text) - max_len + len(replacement)

        # If more characters are to be truncated from this string than exist in
        # this string, then it can be shown by trivial algebraic equivalency
        # that "len(replacement) > max_len" (i.e., the length of the
        # replacement substring exceeds the maximum length). In this uncommon
        # edge case, return the replacement truncated to this maximum.
        if truncate_chars_count > len(text):
            return replacement[:max_len]
        # Else, fewer characters are to be truncated from this string than
        # exist in this string. This is the common case.

        # Return this string truncated to this number of characters appended by
        # this replacement substring.
        return text[:-truncate_chars_count] + replacement
