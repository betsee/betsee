#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level :mod:`QMessageBox`-based error handling facilities.

See Also
----------
:mod:`betsee.util.widget.guimessage`
    Error-agnostic :class:`QMessageBox` facilities.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT* include
#   BETSE modules, which are *NOT* guaranteed to exist at this point. For
#   simplicity, however, all core PySide2 submodules are assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import re, sys, traceback
from PySide2.QtWidgets import QMessageBox

# ....................{ INSTALLERS                         }....................
def install_exception_hook() -> None:
    '''
    Install a global exception hook overriding :mod:`PySide2`\ 's default insane
    exception handling behaviour with sane exception handling.

    By default, :mod:`PySide2`:

    #. Catches **uncaught exceptions** (i.e., exceptions automatically
       propagated up the call stack without being caught) raised during the
       GUI's event loop processing.
    #. Prints the tracebacks for these exceptions to stderr.
    #. Ignores these exceptions by silently returning to GUI processing.

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

# ....................{ SHOWERS                            }....................
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
    message box in the current application widget, creating this widget if
    necessary.

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

    # Message box displaying this error.
    error_box = QMessageBox()
    error_box.setWindowTitle(title)
    error_box.setText(synopsis)
    error_box.setIcon(QMessageBox.Critical)
    error_box.setStandardButtons(QMessageBox.Ok)

    # If this exception provides optional metadata, display this metadata.
    if exegesis is not None:
        assert isinstance(exegesis, str), '"{}" not a string.'.format(exegesis)
        error_box.setInformativeText(exegesis)
    if details is not None:
        assert isinstance(details, str), '"{}" not a string.'.format(details)
        error_box.setDetailedText(details)

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

    # Implicitly create the root Qt widget containing the message box to be
    # subsequently displayed, if needed.
    from betsee.util.app import guiapp
    if False: guiapp  # squelch IDE warnings

    # Human-readable synopsis and exegesis of this exception if defined (e.g.,
    # if this exception is an instance of the "BetseeException" superclass) *OR*
    # this exception message and None otherwise.
    exception_synopsis = getattr(exception, 'synopsis', str(exception))
    exception_exegesis = getattr(exception, 'exegesis', None)

    # If this exception has a human-readable title, use this title as is.
    if hasattr(exception, 'title'):
        exception_title = exception.title
    # Else, synthesize this title from metadata associated with this exception.
    else:
        # Class name of this exception.
        exception_classname = type(exception).__name__

        # Human-readable title of this exception, synthesized from this
        # machine-readable class name by inserting spaces between all
        # boundaries between non-capitalized and capitalized letters (e.g., from
        # "ValueError" to "Value Error").
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
