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
from betsee.guiexception import BetseeSimmerException
from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhase
from betsee.gui.simtab.run.work.guisimrunworkenum import (
    SimmerPhaseSubkind)
from betsee.gui.simtab.run.work.guisimrunwork import (
    QBetseeSimmerSubcommandWorkerModelSeed,
    QBetseeSimmerSubcommandWorkerExportSeed,
)
from collections import deque

# ....................{ GLOBALS                           }....................
_PHASE_KIND_TO_SUBKIND_TO_WORKER_SUBCLASS = {
    SimPhaseKind.SEED: {
        SimmerPhaseSubkind.MODELLING:
            QBetseeSimmerSubcommandWorkerModelSeed,
        SimmerPhaseSubkind.EXPORTING:
            QBetseeSimmerSubcommandWorkerExportSeed,
    },

    #FIXME: Replace all "Seed" substrings below with the appropriate phase
    #substrings *AFTER* validating the seed worker to behave as expected.
    SimPhaseKind.INIT: {
        SimmerPhaseSubkind.MODELLING:
            QBetseeSimmerSubcommandWorkerModelSeed,
        SimmerPhaseSubkind.EXPORTING:
            QBetseeSimmerSubcommandWorkerExportSeed,
    },
    SimPhaseKind.SIM: {
        SimmerPhaseSubkind.MODELLING:
            QBetseeSimmerSubcommandWorkerModelSeed,
        SimmerPhaseSubkind.EXPORTING:
            QBetseeSimmerSubcommandWorkerExportSeed,
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
def make_queue(phases: SequenceTypes) -> QueueType:
    '''
    Create and return a **simulator worker queue** (i.e., double-ended queue of
    all simulator worker classes to be subsequently instantiated and run in a
    multithreaded manner by the simulator such that each worker performs a
    simulation subcommand whose corresponding checkbox is currently checked as
    specified by the passed sequence of all simulator phases).

    Ordering
    ----------
    Worker classes are queued in **simulation phase order** (i.e., the ordering
    defined by the :class:`betse.science.phase.phaseenum.SimPhaseKind`
    enumeration). Callers may safely run the simulation phases performed by
    these workers merely by sequentially instantiating each such class and
    assigning the resulting worker to a thread via the
    :func:`betsee.util.thread.pool.guipoolthread.run_worker` function.

    For example:

    #. The :class:`QBetseeSimmerSubcommandWorkerModelSeed` class is guaranteed
       to be queued *before*...
    #. The :class:`QBetseeSimmerSubcommandWorkerModelInit` class is guaranteed
       to be queued *before*...
    #. The :class:`QBetseeSimmerSubcommandWorkerModelSim` class.

    Parameters
    ----------
    phases : SequenceTypes
        Sequence of all simulator phases. This function iteratively queries
        each such phase to decide which simulation subcommands have checked
        checkboxes. For each such subcommand, this function queues a
        corresponding worker class in the returned queue.

    Returns
    ----------
    QueueType
        Queue of all simulator worker classes to be subsequently run by the
        simulator.
    '''

    # If any sequence item is *NOT* a simulator phase, raise an exception.
    iterables.die_unless_items_instance_of(
        iterable=phases, cls=QBetseeSimmerPhase)

    # Simulator worker queue to be returned.
    worker_queue = deque()

    # For each passed simulator phase...
    for phase in phases:
        # Dictionary mapping from each kind of work performed within this phase
        # to the simulator worker subclass implementing this kind of work.
        subkind_to_worker_subclass = (
            _PHASE_KIND_TO_SUBKIND_TO_WORKER_SUBCLASS[phase.kind])

        # If this phase is currently queued for modelling...
        if phase.is_queued_modelling:
            # Simulator worker subclass modelling this phase.
            worker_subclass = subkind_to_worker_subclass[
                SimmerPhaseSubkind.MODELLING]

            # Enqueue this subclass.
            worker_queue.append(worker_subclass)

        # If this phase is currently queued for exporting...
        if phase.is_queued_exporting:
            # Simulator worker subclass exporting this phase.
            worker_subclass = subkind_to_worker_subclass[
                SimmerPhaseSubkind.EXPORTING]

            # Enqueue this subclass.
            worker_queue.append(worker_subclass)

    # Return this queue.
    return worker_queue
