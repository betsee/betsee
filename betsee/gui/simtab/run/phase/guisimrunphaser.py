#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator phaser** (i.e., :mod:`PySide2`-based object containing
each simulator phase controller on behalf of higher-level parent controllers)
functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, QObject, Slot  #, Signal
from PySide2.QtWidgets import QProgressBar, QLabel
from betse.exceptions import BetseSimUnstableException
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.py import pythread
from betse.util.type import enums
from betse.util.type.iterable import tuples
from betse.util.type.obj import objects
from betse.util.type.types import type_check, CallableTypes, QueueType
from betsee.guiexception import (
    BetseeSimmerException, BetseeSimmerBetseException)
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState,
    SIMMER_STATES_INTO_FIXED,
    SIMMER_STATES_FROM_FLUID,
    SIMMER_STATES_RUNNING,
    SIMMER_STATES_WORKING,
    SIMMER_STATES_UNWORKABLE,
)
from betsee.gui.simtab.run.guisimrunabc import QBetseeSimmerStatefulABC
from betsee.gui.simtab.run.phase.guisimrunphase import QBetseeSimmerPhase
from betsee.gui.simtab.run.work.guisimrunwork import QBetseeSimmerPhaseWorker
from betsee.gui.simtab.run.work.guisimrunworkenum import SimmerPhaseSubkind
from betsee.util.thread import guithread
from betsee.util.thread.pool import guipoolthread
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC
from collections import deque

# ....................{ TYPES                             }....................
#FIXME: This submodule is, yet again, becoming long in the tooth. To rectify
#this, contemplate the following refactoring:
#
#* Define a new "guisimrunphases" submodule in this subpackage.
#* Define a new "QBetseeSimmerPhaser(QBetseeControllerABC)" subclass in this
#  submodule.
#* Shift most phase-specific functionality from the "QBetseeSimmerProactor"
#  class into this new "QBetseeSimmerPhaser" class. Ideally, the latter should
#  serve as a somewhat superficial container for phases. This includes:
#  * The "QBetseeSimmerProactor.PHASES" tuple, which should be renamed to
#    "QBetseeSimmerPhases.PHASES".
#  * The "QBetseeSimmerProactor._phase_seed", "_phase_init", and "_phase_sim"
#    controllers, whose names should probably remain as is.
#  * This "SimmerProactorMetadata" class.
#  * The QBetseeSimmerProactor.get_metadata() method.
#* Define a new "QBetseeSimmerProactor.phaser" instance variable in the
#  QBetseeSimmerProactor.__init__() method initialized to an instance of the
#  "QBetseeSimmerPhaser" class.
SimmerProactorMetadata = tuples.make_named_subclass(
    class_name='SimmerProactorMetadata',
    item_names=(
       'phases_queued_modelling_count',
       'phases_queued_exporting_count',
    ),
    doc='''
    Named tuple created and returned by the
    :meth:`QBetseeSimmerProactor.get_metadata` method, aggregating metadata
    synopsizing the current state of the simulator proactor.

    Attributes
    ----------
    phases_queued_modelling_count : int
        Number of simulator phases currently queued for modelling.
    phases_queued_exporting_count : int
        Number of simulator phases currently queued for exporting.
    '''
)

# ....................{ CLASSES                           }....................
class QBetseeSimmerPhaser(QBetseeControllerABC):
    '''
    High-level **simulator proactor phaser** (i.e., :mod:`PySide2`-based
    object containing each simulator phase controller on behalf of
    higher-level parent controllers).

    Attributes (Public)
    ----------
    PHASES : SequenceTypes
        Immutable sequence of all simulator phase controllers (e.g.,
        :attr:`_phase_seed`), needed for iteration over these controllers. For
        sanity, these phases are ordered is simulation order such that:

        * The seed phase is listed *before* the initialization phase.
        * The initialization phase is listed *before* the simulation phase.

    Attributes (Private)
    ----------
    _phase_seed : QBetseeSimmerPhase
        Controller for all simulator widgets pertaining to the seed phase.
    _phase_init : QBetseeSimmerPhase
        Controller for all simulator widgets pertaining to the initialization
        phase.
    _phase_sim : QBetseeSimmerPhase
        Controller for all simulator widgets pertaining to the simulation
        phase.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator proactor phaser.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Simulator phase controllers.
        self._phase_seed = QBetseeSimmerPhase(self)
        self._phase_init = QBetseeSimmerPhase(self)
        self._phase_sim  = QBetseeSimmerPhase(self)

        # Sequence of all simulator phases, intentionally listed in simulation
        # order to ensure sane iterability.
        self.PHASES = (self._phase_seed, self._phase_init, self._phase_sim)


    @type_check
    def init(
        self,
        main_window: QBetseeMainWindow,
        set_state_from_phase: CallableTypes,
    ) -> None:
        '''
        Finalize this phaser's initialization, owned by the passed main window
        widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulator.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        set_state_from_phase : CallableTypes
            Slot of the parent proactor setting the current state of the
            proactor to the current state of the passed simulator phase. For
            simplicity, this method iteratively for all simulator phases:

            * Connects the queueing signal emitted by this phase to this slot.
            * Calls this slot with this phase, ensuring that the proactor
              derive its initial state from the initial state of each phase.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Log this finalization.
        logs.log_debug('Sanitizing simulator proactor phaser state...')

        # Initialize all phases (in arbitrary order).
        self._phase_seed.init(kind=SimPhaseKind.SEED, main_window=main_window)
        self._phase_init.init(kind=SimPhaseKind.INIT, main_window=main_window)
        self._phase_sim .init(kind=SimPhaseKind.SIM , main_window=main_window)

        # For each possible phase...
        for phase in self.PHASES:
            # Connect the queueing signal emitted by this phase to the
            # corresponding slot of the parent proactor.
            phase.set_state_queued_signal.connect(set_state_from_phase)

            # Set the proactor's initial state from this phase's initial state.
            set_state_from_phase(phase)

    # ..................{ GETTERS                           }..................
    def get_metadata(self) -> SimmerProactorMetadata:
        '''
        Named tuple aggregating metadata synopsizing the current state of this
        proactor, typically for displaying this metadata to the end user.

        Design
        ----------
        This method is intentionally designed as a getter rather than read-only
        property to inform callers of the non-negligible cost of each call to
        this getter, whose return value should thus be stored in a
        caller-specific variable rather than recreated silently on each access
        of such a property.
        '''

        # Number of simulator phases queued for modelling and exporting.
        phases_queued_modelling_count = 0
        phases_queued_exporting_count = 0

        # For each such phase...
        for phase in self.PHASES:
            # If this phase is queued for modelling, note this fact.
            if phase.is_queued_modelling:
                phases_queued_modelling_count += 1

            # If this phase is queued for exporting, note this fact.
            if phase.is_queued_exporting:
                phases_queued_exporting_count += 1

        # Create and return a named tuple aggregating this metadata.
        return SimmerProactorMetadata(
            phases_queued_modelling_count=phases_queued_modelling_count,
            phases_queued_exporting_count=phases_queued_exporting_count,
        )

    # ..................{ ENQUEUERS                         }..................
    def enqueue_phase_workers(self) -> QueueType:
        '''
        Create and return a new **simulator worker queue** (i.e., double-ended
        queue of each simulator worker to be subsequently run in a
        multithreaded manner by the parent proactor to run a simulation
        subcommand whose corresponding checkbox was checked at the time this
        method was called).

        This method enqueues (i.e., pushes onto this queue) workers in
        simulation phase order, defined as the ordering of the members of the
        :class:`betse.science.phase.phaseenum.SimPhaseKind` enumeration.
        Callers may safely run the simulation phases performed by these workers
        merely by sequentially assigning each worker enqueued in this queue to
        a thread via the
        :func:`betsee.util.thread.pool.guipoolthread.start_worker` function.

        For example:

        #. The :class:`QBetseeSimmerSubcommandWorkerModelSeed` worker (if any)
           is guaranteed to be queued *before*...
        #. The :class:`QBetseeSimmerSubcommandWorkerModelInit` worker (if any)
           is guaranteed to be queued *before*...
        #. The :class:`QBetseeSimmerSubcommandWorkerModelSim` worker (if any).

        Caveats
        ----------
        **This queue is double- rather than single-ended.** Why? Because the
        Python stdlib fails to provide the latter. Since the former generalizes
        the latter, however, leveraging the former in a single-ended manner
        replicates the behaviour of the latter. Ergo, a double-ended queue
        remains the most space- and time-efficient data structure for doing so.

        Returns
        ----------
        QueueType
            If either:

            * No simulator phase is currently queued.
            * Some simulator phase is currently running (i.e.,
              :attr:`_workers_queued` is already defined to be non-``None``).
        '''

        # Log this action.
        guithread.log_debug_thread_main('Enqueueing simulator workers...')

        # If this controller is *NOT* currently queued, raise an exception.
        self._die_unless_queued()

        # If some simulator worker is currently working, raise an exception.
        self._die_if_working()

        #FIXME: Refactor all of the following logic into a new
        #phaser.enqueue_phase_workers() method.

        # Simulator worker queue to be classified *AFTER* creating and
        # enqueuing all workers.
        workers_queued = deque()

        # For each simulator phase...
        for phase in self.phaser.PHASES:
            # If this phase is currently queued for modelling...
            if phase.is_queued_modelling:
                # Simulator worker modelling this phase.
                worker = QBetseeSimmerPhaseWorker(
                    phase=phase, phase_subkind=SimmerPhaseSubkind.MODELLING)

                # Enqueue a new instance of this subclass.
                workers_queued.append(worker)

            # If this phase is currently queued for exporting...
            if phase.is_queued_exporting:
                # Simulator worker subclass exporting this phase.
                worker = QBetseeSimmerPhaseWorker(
                    phase=phase, phase_subkind=SimmerPhaseSubkind.EXPORTING)

                # Enqueue a new instance of this subclass.
                workers_queued.append(worker)

        # Classify this queue *AFTER* successfully creating and enqueuing all
        # workers, thus reducing the likelihood of desynchronization.
        self._workers_queued = workers_queued
