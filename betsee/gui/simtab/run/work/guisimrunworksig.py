#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **signals-based simulation phase callbacks** (i.e., collection of all
simulation phase callbacks whose methods emit queued Qt signals) classes.
'''

#FIXME: Wire up the "self._signals.progress_ranged" and
#"self._signals.progressed" signals to the corresponding slots of the
#simulator progress bar. Perhaps a new
#"SimCallbacksSignaller.init(main_window: QMainWindow)" method may be defined?
#FIXME: Err, probably not, actually. Instances of this class are only locally
#defined to preserve thread affinity; ergo, the parent
#"QBetseeSimmerWorkerABC" class will need to establish these signal-slot
#connections that in a new
#"QBetseeSimmerWorkerABC.init(main_window: QMainWindow)" method, probably.

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
        self._signals.progress_ranged.emit(progress_min, progress_max)

        #FIXME: This requires that this object maintain at least a weak
        #reference to the parent worker, Alternately, for generality, that
        #reference could instead be passed to the
        #QBetseeThreadPoolWorkerSignals.__init__() method and then classified
        #as a public "worker" weak reference. The latter probably makes more
        #sense, actually, as *ALL* "QBetseeThreadPoolWorkerSignals" instances
        #will need to call the self._worker._halt_work_if_requested() in every
        #callback. Either way, the end result is the same, of course.
        #FIXME: Since *ALL* "QBetseeThreadPoolWorkerSignals" instances will
        #need to call the self._worker._halt_work_if_requested() in every
        #callback, we'd might as well codify that by defining helper methods in
        #the "QBetseeThreadPoolWorkerSignals" class resembling:
        #
        #    @type_check
        #    def emit_progress_ranged(progress_min: int, progress_max: int) -> None:
        #
        #        # Signal all slots connected to this signal with these parameters.
        #        self.progress_ranged.emit(progress_min, progress_max)
        #
        #        Temporarily or permanently halt all worker-specific business logic
        #        when requested to do so by external callers in other threads.
        #        self._worker._halt_work_if_requested()
        #
        #It's better to centralize that boilerplate rather than distribute it
        #throughout the codebase.

        #FIXME: Perform similar logic in the progressed() callback.

        # Temporarily or permanently halt all worker-specific business logic
        # when requested to do so by external callers in other threads.
        # self._worker._halt_work_if_requested()


    @type_check
    def progressed(self, progress: int) -> None:

        # Perform all superclass callback handling first.
        super().progressed(progress=progress)

        # Forward these callback parameters to the corresponding worker signal.
        self._signals.progressed.emit(progress)
