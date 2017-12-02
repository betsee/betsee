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
from betse.util.io.log import logconfig, logs
from betse.util.io.log.logenum import LogLevel
from betse.util.io.log.logfilter import LogFilterThirdPartyDebug
from betse.util.type.types import type_check
from betsee.util.io.log.guiloghandle import LogHandlerSignal
from betsee.util.widget.stock.guitextedit import QBetseePlainTextEdit

# ....................{ INITIALIZERS                       }....................
@type_check
def log_to_text_edit(text_edit: QBetseePlainTextEdit) -> None:
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

    # Log a single-line sentence synopsizing the state of this application
    # *AFTER* finalizing logging reconfiguration.
    logs.log_info('Initializing GUI...')
