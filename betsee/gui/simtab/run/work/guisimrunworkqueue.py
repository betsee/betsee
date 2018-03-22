#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator runner** (i.e., :mod:`PySide2`-based thread performing the
equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

#FIXME: Implement the following:
#
#* A private "_PHASE_KIND_TO_SIMMER_STATE_TO_WORKER" dictionary-of-dictionaries
#  mapping each "SimPhaseKind" member to *ONLY* the "SimmerState.MODELLING" and
#  "SimmerState.EXPORTING" members (yes, slightly janky -- but should
#  substantially save us time and effort, given that doing so should
#  substantially simplify the setting of simulator phase state from the
#  simulator) to the corresponding "QBetseeSimmerWorkerABC" subclass (e.g.,
#  "QBetseeSimmerWorkerSeed"). For example:
#
#     _PHASE_KIND_TO_SIMMER_STATE_TO_WORKER = {
#         SimPhaseKind.SEED: {
#             SimmerState.MODELLING: QBetseeSimmerWorkerSeed, ...
#         }, ...
#     }
#
#* A public "def make_queue(phases: SequenceTypes) -> deque" function accepting
#  the sequence of all possible phases (e.g., "self._phases" in the simulator)
#  and returning a "deque" of all "QBetseeSimmerWorkerABC" instances required to
#  run all currently queued phases. Naturally, this function will internally
#  leverage the aforementioned dictionary -- which, in theory, should trivially
#  generalize this function's implementation.

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication, QObject, QThread, Slot  # Signal
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phaseenum import SimPhaseKind
# from betse.util.io.log import logs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState)
from betsee.gui.simtab.run.work.guisimrunwork import (
    SimmerState)
from collections import deque

# ....................{ GLOBALS                            }....................

# ....................{ MAKERS                             }....................
