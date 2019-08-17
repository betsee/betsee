#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-specific logging handler subclasses.
'''

#FIXME: Tragically, our recent improvements to guarantee closure of all open
#logfile handles has invited a spurious segmentation fault at BETSEE closure:
#
#    [betsee] Deinitializing singleton logging configuration...
#    free(): invalid pointer
#    Fatal Python error: Aborted
#
#    Current thread 0x00007fc68dd89680 (most recent call first):
#      File "/home/leycec/py/betsee/betsee/util/io/log/guiloghandle.py", line 59 in emit
#      File "/usr/lib64/python3.6/logging/__init__.py", line 863 in handle
#      File "/usr/lib64/python3.6/logging/__init__.py", line 1514 in callHandlers
#      File "/usr/lib64/python3.6/logging/__init__.py", line 1452 in handle
#      File "/usr/lib64/python3.6/logging/__init__.py", line 1442 in _log
#      File "/usr/lib64/python3.6/logging/__init__.py", line 1294 in debug
#      File "/usr/lib64/python3.6/logging/__init__.py", line 1910 in debug
#      File "/home/leycec/py/betse/betse/util/io/log/logs.py", line 169 in log_debug
#      File "<string>", line 14 in __log_debug_type_checked__
#      File "/home/leycec/py/betse/betse/util/io/log/conf/logconf.py", line 126 in deinit
#      File "<string>", line 4 in __deinit_type_checked__
#      File "/home/leycec/py/betse/betse/util/app/meta/appmetaabc.py", line 319 in deinit
#      File "/home/leycec/py/betse/betse/util/app/meta/appmetaone.py", line 297 in deinit
#      File "/home/leycec/py/betse/betse/util/cli/cliabc.py", line 207 in run
#      File "<string>", line 14 in __run_type_checked__
#      File "/home/leycec/py/betsee/betsee/__main__.py", line 102 in main
#      File "/usr/bin/betsee", line 87 in <module>
#    zsh: abort      betsee -v
#
#Clearly, this issue *MUST* be resolved as soon as feasible. To do so, we'll
#probably need to override the default AppMetaABC.deinit() method as follows:
#
#1. Disconnect all slots connected to the "signal" parameter passed to the
#   "LogHandlerSignal" instance *BEFORE* calling super().deinit().
#1. Ensure the "LogHandlerSignal" instance previously added to our root logger
#   has been removed. This is probably already implicitly handled by the
#   subsequent super().deinit() call, but let's be rather sure of that.
#2. Call super().deinit(), thus closing this logfile.
#FIXME: Ah-ha! A superior alternative presents itself. Rather than do any of
#the above, it *SHOULD* theoretically suffice to simply do the following:
#
#* Override the Handler.close() method in the "LogHandlerSignal" subclass
#  defined below, whose implementation should either:
#  * Nullify the "_signal" instance variable. This is probably the ideal
#    approach, as doing so avoids modifying external caller-defined objects.
#    Note, however, that this approach then requires slightly generalizing the
#    emit() method to test for whether "_signal" is "None" and, if so, silently
#    reduce to a noop. Lastly, note that there exists no corresponding open()
#    or _open() methods in the "Handler" superclass; ergo, there exist no
#    concerns about needing to reopen a previously closed handler, implying
#    that permanently nullifying the "_signal" instance variable on the first
#    call to the close() method is indeed the optimal approach. (Indeed, the
#    superclass close() method itself behaves irreversibly destructively.)
#  * Disconnect all slots connected to the "_signal" instance variable... or
#    perhaps not, as doing so would modify external caller-defined objects in a
#    possibly unexpected manner?

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
    _signal : Signal
        Signal to redirect log records to.
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def __init__(self, signal: Signal, *args, **kwargs) -> None:
        '''
        Initialize this handler to log with the passed signal.

        Parameters
        ----------
        signal : Signal
            Signal to redirect log records to.

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

        # Redirect this log message to all slots connected to this handler's
        # previously initialized signal.
        self._signal.emit(record_message)
