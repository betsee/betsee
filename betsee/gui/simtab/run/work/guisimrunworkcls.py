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
from betsee.util.thread.guiworkercls import QBetseeThreadWorkerThrowawayABC

# ....................{ SUPERCLASSES                       }....................
#FIXME: Shift the "_sim_runner" documentation below elsewhere, please.
class QBetseeSimmerWorkerABC(QBetseeThreadWorkerThrowawayABC):
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

        # Set this object's name to this subclass' munged name (e.g., from
        # "QBetseeSimmerWorkerSeed" to "simmer_worker_seed").
        self.set_obj_name_from_class_name()


    #FIXME: *UGH.* Remove the QBetseeSimmerWorkerABC.init() method -- which,
    #in hindsight, was an atrocious idea. Document why: notably, the fact
    #that any passed objects owned by the parent thread (presumably, all of
    #them) will continue to be owned by this thread even after this worker
    #is adopted into its parent thread. Which, of course, entirely defeats
    #the point of multithreading in the first place.
    #
    #Explicitly document this as a caveat somewhere. *WE MUST NEVER MAKE
    #THIS AWFUL MISTAKE AGAIN.*

    # @type_check
    # def init(self, sim_runner: SimRunner) -> None:
    #     '''
    #     Finalize the initialization of this simulator worker.
    #
    #     Parameters
    #     ----------
    #     sim_runner : SimRunner
    #         Simulation runner run by this simulator worker, encapsulating both
    #         the simulation configuration file to be run *and* all low-level
    #         logic required to do so.
    #     '''
    #
    #     # Initialize our superclass.
    #     super().init()
    #
    #     # Classify this simulation runner.
    #     self._sim_runner = sim_runner

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

    # ..................{ PROPERTIES ~ concrete              }..................
    # Settable concrete properties required by all subclasses.

    #FIXME: Excise us up.
    # @property
    # def sim_runner(self) -> SimRunner:
    #     '''
    #     Simulation runner run by this simulator worker, encapsulating both the
    #     simulation configuration file to be run *and* all low-level logic
    #     required to do so.
    #
    #     This property elegantly bridges the gap between the low-level CLI-based
    #     BETSE simulator and this high-level GUI-based BETSEE wrapper. Arguably,
    #     this property is the most important attribute in either codebase.
    #     '''
    #
    #     pass
    #
    #
    # @sim_runner.setter
    # @type_check
    # def sim_runner(self, sim_runner: SimRunner) -> None:
    #     '''
    #     Type of work performed within the type of simulation phase run by this
    #     simulator worker.
    #     '''
    #
    #     pass

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
    #FIXME: Obviously, forcing "str" usage is awful. See "guiworkercls" for
    #demonstrably superior alternatives.
    def _work(self, conf_filename: str) -> None:

        # Well, that was easy. (No, it really wasn't.)
        # sim_runner = SimRunner(conf_filename=conf_filename)
        # sim_runner.seed()

        #FIXME: Let's try sleeping. Something absolutely isn't right here.
        #FIXME: O.K.; it absolutely is the GIL that's killing us. Iteratively
        #calling self._halt_work_if_requested() dramatically improves matters,
        #which is horrible. Note that calling QThread.yieldCurrentThread()
        #slightly improves GUI responsiveness even more, but (presumably) at a
        #dramatic performance penalty that we absolutely shouldn't pay. The call
        #to self._halt_work_if_requested() should suffice to at least permit the
        #pause and stop buttons to be meaningfully responded to. *sigh*
        from betse.util.io.log import logs
        import time
        for _ in range(8):
            logs.log_debug('Sleeping for one second...')
            # QThread.sleep(1)
            time.sleep(1)
            self._halt_work_if_requested()
            # QThread.yieldCurrentThread()
        # QThread.msleep(1024**2)
        # QThread.msleep(4096*2)
