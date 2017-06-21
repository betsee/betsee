#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-specific logging handler subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Signal
from betse.util.type import type_check
from logging.handlers import Handler

# ....................{ CLASSES                            }....................
#FIXME: Post as an answer to the following StackOverflow question:
#    https://stackoverflow.com/questions/14349563/how-to-get-non-blocking-real-time-behavior-from-python-logging-module-output-t
class LogHandlerSignal(Handler):
    '''
    :class:`Signal`-based handler, redirecting each log record sent to this
    handler to each slot connected to the signal with which this handler was
    initialized.

    Parameters
    ----------
    _signal : Signal
        Signal to redirect log records with.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, signal: Signal, *args, **kwargs) -> None:
        '''
        Initialize this handler to log with the passed signal.

        Parameters
        ----------
        signal : Signal
            Signal to redirect log records with.

        All remaining parameters are passed as is to our superclass method.
        '''

        # Initialize our superclass with all remaining passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all explicitly specified parameters.
        self._signal = signal

    # ..................{ EMITTERS                           }..................
    def emit(self, record) -> None:

        # Log messaged formatted from this log record via this handler's current
        # log message formatter.
        record_message = self.format(record)

        # Redirect this log message to all slots connected to this handler's
        # previously initialized signal.
        self._signal.emit(record_message)
