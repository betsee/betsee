#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-specific logging configuration.
'''

#FIXME: Consider colourizing redirected log records. Doing so will be slightly
#non-trivial, however, as we would then need to use a rich text edit widget
#rather than a plain text edit widget.

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logconfig
from betse.util.io.log.logenum import LogLevel
from betse.util.io.log.logfilter import LogFilterThirdPartyDebug
from betsee.util.io.log.psdloghandle import LogHandlerSignal
from betsee.util.type.psdstr import QBetseePlainTextEdit

# ....................{ INITIALIZERS                       }....................
#FIXME: Actually call this during application ignition. For safety, this must
#obviously be delayed until *AFTER* the main window is constructed (but ideally
#before the main window is made visible).
#FIXME: To do so, this function should probably accept the main window widget.
#Or perhaps this function should accept an instance of :class:`QPlainTextEdit`
#as its only parameter. Or... perhaps not. Instead, consider:
#
#* Defining a new "betsee.util.type.psdstr.QBetseePlainTextEdit" class subclassing
#  the "PySide2.QtWidget.QPlainTextEdit" base class implementing thread-safe
#  text appending complete with auto-scrolling, containing:
#  * A new append_text_signal() signal class variable passed a "str".
#  * A new append_text() slot method passed a "str", whose
#    implementation (in order):
#
#    @QtCore.Slot(str)
#    def append_text(text: str) -> None:
#        super().appendPlainText(text)
#        super().ensureCursorVisible()
#  * A custom __init__() method connecting this signal to this slot.
#* Refactor this function to accept an instance of the
#  "betsee.util.type.str.QBetseePlainTextEdit" class, which our main window
#  widget should pass to this function.
#* This function should then resemble:
#
#    @type_check
#    def init(text_edit: QBetseePlainTextEdit) -> None:
#        log_config = logconfig.get()
#
#        # Root logger handler redirecting to all slots connected to a signal.
#        logger_root_handler_signal = SignalHandler(
#            signal=text_edit.append_text_signal)
#        logger_root_handler_signal.setLevel(
#            LogLevel.ALL if log_config.is_verbose else LogLevel.INFO)
#
#        # Prevent third-party debug messages from being printed to the terminal.
#        logger_root_handler_signal.addFilter(LoggerFilterDebugNonBetse())
#
#        #FIXME: See the _init_logger_root_handler_std() method for the rest!
#
#To actually use this custom class in Qt Creator, see the following insanity:
#    https://stackoverflow.com/a/19622817/2809027

def init(text_edit: QBetseePlainTextEdit) -> None:
    '''
    Append all unfiltered log records to the passed text widget in an
    autoscrolling, non-blocking, thread-safe manner.

    This function integrates the default logging configuration for the active
    Python process with the current :mod:`PySide2` application. Specifically,
    this function reconfigures logging to additionally forward all relevant log
    records logged to the root handler onto the relevant slot connected to the
    relevant signal of the passed text widget, where "relevant log records"
    means:

    * If verbosity is enabled (e.g., via the ``--verbose`` command-line option),
      all log records.
    * Else, all log records with level ``LogLevel.INFO`` and higher.

    Parameters
    ----------
    text_edit : QBetseePlainTextEdit
        Text widget to append relevant log records to.
    '''

    # Global logging configuration.
    log_config = logconfig.get()

    # Root logger handler redirecting to all slots connected to a signal.
    logger_root_handler_signal = LogHandlerSignal(
        signal=text_edit.append_text_signal)

    # If verbosity is enabled, redirect all log records; else, only redirect log
    # records with level "INFO" and higher.
    logger_root_handler_signal.setLevel(
        LogLevel.ALL if log_config.is_verbose else LogLevel.INFO)

    # Avoid redirecting third-party debug messages.
    logger_root_handler_signal.addFilter(LogFilterThirdPartyDebug())

    # Register this handler with the root logger.
    log_config.logger_root.addHandler(logger_root_handler_signal)
