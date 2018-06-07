#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator runner** (i.e., :mod:`PySide2`-based thread performing
the equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

#FIXME: Implement the following:
#
#* A public "def make_queue(phases: SequenceTypes) -> deque" function accepting
#  the sequence of all possible phases (e.g., "self._phases" in the simulator)
#  and returning a "deque" of all "QBetseeSimmerWorkerABC" instances required
#  to run all currently queued phases. Naturally, this function will internally
#  leverage the aforementioned dictionary -- which, in theory, should trivially
#  generalize this function's implementation.

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication, QObject, QThread, Slot  # Signal
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phaseenum import SimPhaseKind
# from betse.util.io.log import logs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
# from betsee.gui.simtab.run.guisimrunstate import SimmerState
from betsee.gui.simtab.run.work.guisimrunworkenum import (
    SimmerPhaseSubkind)
from betsee.gui.simtab.run.work.guisimrunwork import (
    QBetseeSimmerSubcommandWorkerModelSeed,
    QBetseeSimmerSubcommandWorkerExportSeed,
)
from collections import deque

# ....................{ GLOBALS                           }....................
_PHASE_KIND_TO_SUBKIND_TO_WORKER_SUBCLASS = {
    #FIXME: Define all additional phases *AFTER* validating this to work.
    SimPhaseKind.SEED: {
        SimmerPhaseSubkind.MODELLING:
            QBetseeSimmerSubcommandWorkerModelSeed,
        SimmerPhaseSubkind.EXPORTING:
            QBetseeSimmerSubcommandWorkerExportSeed,
    },
}
'''
Dictionary mapping from each kind of simulation phase to a dictionary mapping
from each kind of simulator subcommand worker to the
:class:`QBetseeSimmerSubcommandWorkerABC` subclass running both kinds.

For example, the
:class:`QBetseeSimmerSubcommandWorkerModelSeed` subclass models the seed
simulation phase and hence is categorized within this dictionary as such.
'''

# ....................{ MAKERS                            }....................
