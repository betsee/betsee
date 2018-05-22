#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **signals-based simulation phase callbacks** (i.e., collection of all
simulation phase callbacks whose methods emit queued Qt signals) classes.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication  # Slot, Signal
from betse.science.phase.phasecallbacks import SimCallbacksABC
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.thread.pool.guipoolworksig import (
    QBetseeThreadPoolWorkerSignals)

# ....................{ SUBCLASSES ~ callbacks             }....................
class SimCallbacksSignaller(SimCallbacksABC):
    '''
    **Signals-based simulation phase callbacks** (i.e., caller-defined object
    whose methods emit signals on the :class:`QBetseeThreadPoolWorkerSignals`
    object with which this :class:`SimCallbacksSignaller` object is
    initializedare on being periodically called while simulating one or more
    simulation phases).

    This object effectively glues low-level simulation subcommands to
    high-level simulator widgets, converting callbacks called by the former
    into signals emitted on slots defined by the latter.

    Attributes
    ----------
    _signals : QBetseeThreadPoolWorkerSignals
        Collection of all signals emittable by simulator workers.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, signals: QBetseeThreadPoolWorkerSignals) -> None:
        '''
        Initialize this callbacks collection.

        Parameters
        ----------
        signals : QBetseeThreadPoolWorkerSignals
            Collection of all signals emittable by simulator workers.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__()

        # Classify all passed parameters.
        self._signals = signals

    # ..................{ CALLBACKS ~ progress               }..................
    @type_check
    def progress_ranged(
        self, progress_max: int, progress_min: int = 0) -> None:

        # Perform all superclass callback handling first.
        super().progress_ranged(
            progress_min=progress_min, progress_max=progress_max)

        # Forward these callback parameters to the corresponding worker signal.
        self._signals.emit_progress_range(
            progress_min=progress_min, progress_max=progress_max)


    @type_check
    def progressed(self, progress: int) -> None:

        # Perform all superclass callback handling first.
        super().progressed(progress=progress)

        # Forward these callback parameters to the corresponding worker signal.
        self._signals.emit_progress(progress=progress)
