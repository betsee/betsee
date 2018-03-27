#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator worker** (i.e., :mod:`PySide2`-based thread performing the
equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

#FIXME: In the _work() method of each worker subclass defined below, we need to
#periodically call the superclass _halt_work_if_requested() method. Doing so
#will probably necessitate:
#
#* Defining a new QBetseeSimmerWorkerABC._sim_callback() method. The initial
#  trivial implementation of this method should probably resemble:
#
#      def _periodic_callback(self, *args, **kwargs) -> None:
#          self._halt_work_if_requested()
#
#  In time, we expect each worker subclass to override this method with
#  subclass-specific callback handling. For now, the above should suffice as the
#  bare minimum needed to ensure sanity.
#* Augmenting the "SimRunner" class with a new public settable
#  "sampled_callback" property, whose value is required to be a callable
#  accepting no arguments (or perhaps a "SimPhase" object?) and which the
#  "SimRunner" class is expected to unconditionally call if non-"None" without
#  arguments on *EVERY* sampled time step.
#  *WAIT.* While we certainly could do that, we're fairly certain that we'll
#  need to have different types of callbacks for different subcommands. Ergo, a
#  single uniform "sampled_callback" property fails to suffice. Instead, we
#  should:
#  * Refactor each simulation subcommand (e.g., the SimRunner.seed() method) to
#    accept an optional "periodic_callback" argument. Each such subcommand will
#    then be expected to respect this callback. It's conceivable that we'll need
#    additional callback arguments in the future -- but that should suffice for
#    now.
#  *WAIT.* Hmm. Curiously, we now suspect that defining a public settable
#  "generic_callback" property is the approprate solution, but *ONLY* for this
#  specific callback. Why? Because this callback is, as its named implies,
#  intended to be generically and hence uniformly applicable to all simulation
#  subcommands regardless of type. In all likelihood, all this callback will
#  ever do is call the self._halt_work_if_requested() method. When we require
#  additional subcommand-specific callbacks (and we will), those will need to be
#  passed as optional subcommand-specific method arguments. Yeah!
#  *WAIT.* We had it right the second-to-last time, actually. Since one
#  "SimRunner" object is shared amongst multiple workers, a single callback
#  property fails to suffice. Instead, here's *EXACTLY* what we want to do:
#  * Refactor each simulation subcommand (e.g., the SimRunner.seed() method) to
#    accept an optional "periodic_callback" argument. Each such subcommand will
#    then be expected to:
#    * Routinely this callback (e.g., on every sampled time step, on every
#      animation frame, after writing every CSV file or plotted image).
#    * Pass this callback an arbitrary number of simple pure-Python scalar
#      objects (e.g., booleans, integers, strings) specific to the current
#      subcommand. In particular:
#      * The seed() subcommand should pass periodic_callback() (in non-keyworded
#        and hence positional order):
#        1. A raw, unformatted, untranslated string as a single human-readable
#           sentence (e.g., "Optimizing mesh step {0}..."). Non-ideal, but
#           unavoidable for now.
#        2. Zero or more format objects to be interpolated into this sentence.
#      * The init() and sim() subcommands should pass periodic_callback() (in
#        keyworded and hence arbitrary order):
#        * "step_curr", the current sampled time step.
#        * "step_total", the total number of sampled time steps.
#      Note that periodic_callback() should *NEVER* be passed anything other
#      than simple pure-Python scalars. When this fails to suffice (as it
#      certainly will for displaying animation frames), a second
#      subcommand-specific callback performing higher-order logic should be
#      passed. For now, periodic_callback() suffices.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, QThread, Slot  # Signal
from betse.science.simrunner import SimRunner
from betse.science.phase.phaseenum import SimPhaseKind
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.types import type_check
# from betsee.guiexception import BetseeSimmerException
# from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhase
# from betsee.gui.simtab.run.guisimrunstate import SimmerState
from betsee.gui.simtab.run.work.guisimrunworkenum import (
    SimmerWorkerPhaseSubkind)
from betsee.util.thread.guiworkercls import QBetseeThreadWorkerABC

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimmerWorkerABC(QBetseeThreadWorkerABC):
    '''
    Abstract base class of all low-level **simulator worker** (i.e., thread-safe
    object running a single startable, pausable, resumable, and haltable
    simulation subcommand in a multithreaded manner intended to be adopted by
    the thread encapsulated by a :class:`QBetseeWorkerThread` object)
    subclasses.

    Attributes
    ----------
    _sim_runner : SimRunner
        Simulation runner run by this simulator worker, encapsulating both the
        simulation configuration file to be run *and* all low-level logic
        required to do so. This variable tidely bridges the gap between the
        low-level CLI-based BETSE simulator and this high-level GUI-based BETSEE
        application -- and is arguably the most important attribute in either
        codebase.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator worker.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        self._sim_runner = None


    @type_check
    def init(self, sim_runner: SimRunner) -> None:
        '''
        Finalize the initialization of this simulator worker.

        Parameters
        ----------
        sim_runner : SimRunner
            Simulation runner run by this simulator worker, encapsulating both
            the simulation configuration file to be run *and* all low-level
            logic required to do so.
        '''

        self._sim_runner = sim_runner

    # ..................{ PROPERTIES ~ abstract              }..................
    # Read-only abstract properties required to be overridden by subclasses.

    @abstractproperty
    def phase_kind(self) -> SimPhaseKind:
        '''
        Type of simulation phase run by this simulator worker.
        '''

        pass


    @abstractproperty
    def phase_subkind(self) -> SimmerWorkerPhaseSubkind:
        '''
        Type of work performed within the type of simulation phase run by this
        simulator worker.
        '''

        pass

# ....................{ SUBCLASSES                         }....................
#FIXME: Define *NO* additional subclasses until this subclass has been shown to
#behave as expected. Why? Because copying-and-pasting says, "Do a right thing."
class QBetseeSimmerWorkerSeed(QBetseeSimmerWorkerABC):
    '''
    Low-level **seed-specific simulator worker** (i.e., thread-safe object
    running a single startable, pausable, resumable, and haltable "seed"
    simulation subcommand in a multithreaded manner intended to be adopted by
    the thread encapsulated by a :class:`QBetseeWorkerThread` object).
    '''

    # ..................{ METHODS                            }..................
    def _work(self) -> None:

        # Well, that was easy.
        self._sim_runner.seed()
