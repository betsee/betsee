#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

from PySide2.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget)
from PySide2.QtCore import (
    QObject, QRunnable, QThreadPool, QTimer, Signal, Slot)

import traceback, sys

#FIXME: Obsolete this entire submodule by the "guipoolworker" submodule. *sigh*

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    '''


    finished = Signal()
    '''
    Signal emitted by the :meth:`run` method on completing this worker,
    regardless of whether this method successfully returned or raised an
    exception.
    '''

    error = Signal(tuple)
    '''
    Signal emitting a 3-tuple ``(exctype, value, traceback.format_exc())`` when
    an exception is raised by this worker.
    '''

    result = Signal(object)
    '''
    Signal emitting the arbitrary value returned by the :meth:`run` method on
    successfully completing this worker if this method returned a value *or*
    ``None`` otherwise (i.e., if this method returned no value).
    '''

    progress = Signal(int)
    '''
    Signal emitting an integer in the range ``[0, 100]`` indicating the current
    percentage of progress currently completed by this worker.
    '''


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        # kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
