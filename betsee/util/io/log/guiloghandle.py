#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-specific logging handler subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import Signal
from betse.util.type.types import type_check
from logging import Handler

# ....................{ CLASSES                           }....................
#FIXME: Post as an answer to the following StackOverflow question:
#    https://stackoverflow.com/questions/14349563/how-to-get-non-blocking-real-time-behavior-from-python-logging-module-output-t
class LogHandlerSignal(Handler):
    '''
    :class:`Signal`-based handler, redirecting each log record sent to this
    handler to each slot connected to the signal with which this handler was
    initialized.

    Parameters
    ----------
    _signal : SignalOrNoneTypes
        Either:

        * If the :meth:`close` method has yet to be called, the signal to
          forward log records to.
        * Else (i.e., if the :meth:`close` method has already been called),
          ``None``.
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def __init__(self, signal: Signal, *args, **kwargs) -> None:
        '''
        Initialize this handler to log with the passed signal.

        Parameters
        ----------
        signal : Signal
            Signal to forward log records to.

        All remaining parameters are passed as is to our superclass method.
        '''

        # Initialize our superclass with all remaining passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all explicitly specified parameters.
        self._signal = signal

    # ..................{ EMITTERS                          }..................
    def emit(self, record) -> None:

        # Log messaged formatted from this log record via this handler's
        # current log message formatter.
        record_message = self.format(record)

        # If this handler is still open (i.e., the close() method has yet to be
        # called), forward this message to all slots connected to this signal.
        if self._signal is not None:
            self._signal.emit(record_message)

    # ..................{ CLOSERS                           }..................
    def close(self) -> None:

        # Close our superclass.
        super().close()

        # Nullify the signal to forward log messages to, silently reducing the
        # emit() method (and hence this entire handler) to a noop.
        #
        # Note that there exists *NO* corresponding open() or _open() methods
        # in the "Handler" superclass and hence *NO* concerns about reopening a
        # previously closed handler. Indeed, the superclass close() method
        # itself behaves irreversibly destructively, making closure permanent.
        # Ergo, nullifying this instance variable on the first call to this
        # method is the optimal solution.
        self._signal = None
