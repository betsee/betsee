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
from betse.science.phase.phasecallabc import SimCallbacksABC
# from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.thread.pool.guipoolworksig import (
    QBetseeThreadPoolWorkerSignals)

# ....................{ SUBCLASSES ~ callbacks             }....................
class SimCallbacksSignaller(SimCallbacksABC):
    '''
    **Signals-based simulation phase callbacks** (i.e., collection of all
    simulation phase callbacks whose methods emit signals on the
    :class:`QBetseeThreadPoolWorkerSignals` object with which this object is
    initialized).

    This object effectively glues low-level simulation subcommands to high-level
    simulator widgets, converting callbacks called by the former into signals
    emitted on slots defined by the latter.

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
    def progress_ranged(self, progress_min: int, progress_max: int) -> None:

        # Convert these callback parameters into simulator worker signals.
        self._signals.progress_ranged.emit(progress_min, progress_max)


    def progressed(self, progress: int) -> None:

        # Convert these callback parameters into simulator worker signals.
        self._signals.progressed.emit(progress)
