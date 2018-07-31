#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator runner** (i.e., :mod:`PySide2`-based thread performing
the equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

# ....................{ IMPORTS                           }....................
from betse.science.phase.phaseenum import SimPhaseKind
# from betse.util.io.log import logs
from betse.util.type import iterables
from betse.util.type.types import type_check, QueueType, SequenceTypes
# from betsee.guiexception import BetseeSimmerException
from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhaseABC
from betsee.gui.simtab.run.work.guisimrunworkenum import (
    SimmerPhaseSubkind)
from betsee.gui.simtab.run.work.guisimrunwork import (
    QBetseeSimmerPhaseModelWorker, QBetseeSimmerPhaseExportWorker)
from collections import deque

# ....................{ GLOBALS                           }....................
#FIXME: Dramatically simplify. Now that we have phase-generic rather than
#subcommand-specific workers, this doubly-nested dictionary can be flattened
#into a single simple dictionary resembling:
#
#    _PHASE_SUBKIND_TO_WORKER_SUBCLASS = {
#        SimmerPhaseSubkind.MODELLING: QBetseeSimmerPhaseModelWorker,
#        SimmerPhaseSubkind.EXPORTING: QBetseeSimmerPhaseExportWorker,
#    }
#FIXME: Actually, after refactoring the "guisimrunwork" submodule as documented
#there, it should be feasible to entirely remove this dictionary. Red flagons!

_PHASE_KIND_TO_SUBKIND_TO_WORKER_SUBCLASS = {
    SimPhaseKind.SEED: {
        SimmerPhaseSubkind.MODELLING: QBetseeSimmerPhaseModelWorker,
        SimmerPhaseSubkind.EXPORTING: QBetseeSimmerPhaseExportWorker,
    },
    SimPhaseKind.INIT: {
        SimmerPhaseSubkind.MODELLING: QBetseeSimmerPhaseModelWorker,
        SimmerPhaseSubkind.EXPORTING: QBetseeSimmerPhaseExportWorker,
    },
    SimPhaseKind.SIM: {
        SimmerPhaseSubkind.MODELLING: QBetseeSimmerPhaseModelWorker,
        SimmerPhaseSubkind.EXPORTING: QBetseeSimmerPhaseExportWorker,
    },
}
'''
Dictionary mapping from each kind of simulation phase to a dictionary mapping
from each kind of work performed within that phase to the
:class:`QBetseeSimmerSubcommandWorkerABC` subclass running both kinds.

For example, the
:class:`QBetseeSimmerSubcommandWorkerModelSeed` subclass models the seed
simulation phase and hence is categorized within this dictionary as such.
'''

# ....................{ MAKERS                            }....................
@type_check
def enqueue_workers(phases: SequenceTypes) -> QueueType:
    '''
    Create and return a **simulator worker queue** (i.e., double-ended queue of
    all simulator workers to be subsequently run in a multithreaded manner by
    the simulator, such that each worker performs a simulation subcommand whose
    corresponding checkbox is currently checked) as specified by the passed
    sequence of all simulator phases.

    This function returns a double- rather than single-ended queue, as the
    Python stdlib only provides the former. Since the former generalizes the
    latter, however, leveraging the former in a single-ended manner replicates
    the behaviour of the latter. Ergo, a double-ended queue remains the most
    space- and time-efficient data structure for doing so.

    Ordering
    ----------
    Worker classes are queued in **simulation phase order** (i.e., the ordering
    defined by the :class:`betse.science.phase.phaseenum.SimPhaseKind`
    enumeration). Callers may safely run the simulation phases performed by
    these workers merely by sequentially instantiating each such class and
    assigning the resulting worker to a thread via the
    :func:`betsee.util.thread.pool.guipoolthread.run_worker` function.

    For example:

    #. The :class:`QBetseeSimmerSubcommandWorkerModelSeed` worker (if any) is
       guaranteed to be queued *before*...
    #. The :class:`QBetseeSimmerSubcommandWorkerModelInit` worker (if any) is
       guaranteed to be queued *before*...
    #. The :class:`QBetseeSimmerSubcommandWorkerModelSim` worker (if any).

    Parameters
    ----------
    phases : SequenceTypes
        Sequence of all simulator phases. This function iteratively queries
        each such phase to decide which simulation subcommands have checked
        checkboxes. For each such subcommand, this function queues a
        corresponding worker in the returned queue.

    Returns
    ----------
    QueueType
        Queue of all simulator workers (i.e., :class:`QBetseeSimmerWorkerABC`
        instances) to be subsequently run by the simulator,
    '''

    # If any sequence item is *NOT* a simulator phase, raise an exception.
    iterables.die_unless_items_instance_of(
        iterable=phases, cls=QBetseeSimmerPhaseABC)

    # Simulator worker queue to be returned.
    workers_queued = deque()

    # For each passed simulator phase...
    for phase in phases:
        # Dictionary mapping from each kind of work performed within this phase
        # to the simulator worker subclass implementing this kind of work.
        subkind_to_worker_subclass = (
            _PHASE_KIND_TO_SUBKIND_TO_WORKER_SUBCLASS[phase.kind])

        # If this phase is currently queued for modelling...
        if phase.is_queued_modelling:
            # Simulator worker modelling this phase.
            worker_subclass = subkind_to_worker_subclass[
                SimmerPhaseSubkind.MODELLING]
            worker = worker_subclass(phase=phase)

            # Enqueue a new instance of this subclass.
            workers_queued.append(worker)

        # If this phase is currently queued for exporting...
        if phase.is_queued_exporting:
            # Simulator worker subclass exporting this phase.
            worker_subclass = subkind_to_worker_subclass[
                SimmerPhaseSubkind.EXPORTING]
            worker = worker_subclass(phase=phase)

            # Enqueue a new instance of this subclass.
            workers_queued.append(worker)

    # Return this queue.
    return workers_queued
