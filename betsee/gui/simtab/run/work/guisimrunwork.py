#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator worker** (i.e., :mod:`PySide2`-based thread performing the
equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

#FIXME: Implement the following:
#
#* The "QBetseeSimmerWorkerABC" superclass. Presumably empty for now, but we'll
#  definitely be filling this up with core functionality... as we go.
#* One "QBetseeSimmerWorkerABC" subclass for each of the five possible
#  simulation subcommands to be run (e.g., "QBetseeSimmerWorkerSeed"). Each such
#  subclass should *AT LEAST* redefine the start() slot.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, QThread, Slot  # Signal
# from betse.science.export.expenum import SimExportType
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.text import strs
from betse.util.type.types import type_check  #, StrOrNoneTypes
from betsee.guiexception import BetseeSimmerException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhase
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState,
    SIMMER_STATE_TO_STATUS_VERBOSE,
    SIMMER_STATES_FIXED,
    SIMMER_STATES_FLUID,
    # MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS,
    # EXPORTING_TYPE_TO_STATUS_DETAILS,
)
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.util.thread.guiworker import QBetseeWorkerABC
from collections import deque

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimmerWorkerABC(QBetseeWorkerABC):
    '''
    Low-level **simulator worker** (i.e., thread-safe object running a single
    startable, pausable, resumable, and haltable simulation subcommand in a
    multithreaded manner intended to be moved to the thread encapsulated by a
    :class:`QThread` object).

    Attributes (Private: Non-widgets)
    ----------
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator worker.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        # self._action_toggle_playing = None

    # ..................{ PROPERTIES                         }..................
    #FIXME: We probably at least need to define a gettable and settable kind()
    #property. See the simulator phase class for the exact same logic. (Don't
    #bother attempting to generalize it. Workers are *NOT* controllers.)
    #
    #Note that, as these properties will be accessed in a cross-thread manner,
    #they absolutely need to leverage "QMutexLocker". For safety, please. *sigh*
    #FIXME: Oh! Wait. Nevermind. All we need to do is statically define a
    #read-only getter property in each subclass ala:
    #
    #    @property
    #    def kind(self) -> SimPhaseKind:
    #        return SimPhaseKind.SEED
    #
    #Yeah. That was kinda obvious. No need for "QMutexLocker". Yay!

# ....................{ SUBCLASSES                         }....................
