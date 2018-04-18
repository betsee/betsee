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
# from PySide2.QtCore import QCoreApplication  # Slot, Signal
from betse.science.parameters import Parameters
from betse.science.phase.phaseenum import SimPhaseKind
from betse.science.simrunner import SimRunner
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.types import type_check
# from betsee.guiexception import BetseeSimmerException
# from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhase
# from betsee.gui.simtab.run.guisimrunstate import SimmerState
from betsee.gui.simtab.run.work.guisimrunworkenum import (
    SimmerWorkerPhaseSubkind)
from betsee.util.thread.pool.guipoolworker import QBetseeThreadPoolWorker

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimmerWorkerABC(QBetseeThreadPoolWorker):
    '''
    Abstract base class of all low-level **simulator worker** (i.e., thread-safe
    object running a single startable, pausable, resumable, and haltable
    simulation subcommand in a multithreaded manner intended to be run by an
    arbitrary thread from a :class:`QThreadPool` container) subclasses.

    Attributes
    ----------
    _p : Parameters
        Simulation configuration to be run by this simulator worker.
    '''

    # ..................{ INITIALIZERS                       }..................
    #FIXME: Ensure that the passed "Parameters" object is a copy of the
    #GUI-specific "main_window.sim_conf.p" singleton.
    @type_check
    def __init__(self, p: Parameters) -> None:
        '''
        Initialize this simulator worker.

        Attributes
        ----------
        p : Parameters
            Simulation configuration to be run by this simulator worker. For
            thread-safety, this worker internally retains only a deep copy of
            rather than shallow reference to this object; ergo, the original
            simulation configuration passed by the caller is guaranteed to
            remain unchanged by this worker. This object bridges the critical
            gap between the low-level CLI-based simulator and this high-level
            GUI, making this the most important attribute in either codebase.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__()

        # Initialize a worker-specific configuration from this configuration.
        self._init_p(p)


    @type_check
    def _init_p(self, p: Parameters) -> None:
        '''
        Initialize a worker-specific simulation configuration from the passed
        simulation configuration by classifying a deep copy of the latter for
        thread-safety into the :attr:`_p` instance variable of this worker.

        Attributes
        ----------
        p : Parameters
            Simulation configuration to be run by this simulator worker.
        '''

        # Simulation configuration newly deserialized from the passed original
        # Simulation configuration.
        self._p = Parameters().load(p.conf_filename)

        # Disable all simulation configuration options either requiring
        # interactive user input *OR* displaying graphical output intended for
        # interactive user consumption (e.g., plots, animations).
        self._p.anim.is_after_sim_show = False
        self._p.anim.is_while_sim_show = False
        self._p.plot.is_after_sim_show = False

        # Enable all simulation configuration options exporting to disk.
        self._p.anim.is_after_sim_save = True
        self._p.anim.is_while_sim_save = True
        self._p.plot.is_after_sim_save = True

        #FIXME: This must go. The above changes must absolutely *NOT* be
        #reserialized back to disk, as doing so now desynchronizes the already
        #deserialized "main_window.sim_conf.p" object from these changes. See
        #the QBetseeSimmerWorkerSeed._work() method for the full commentary.

        # Reserialize these changes back to this file.
        self._p.save_inplace()

    # ..................{ PROPERTIES ~ abstract              }..................
    # Read-only abstract properties required to be overridden by subclasses.

    #FIXME: Uncomment the following @abstractproperty decorators *AFTER*
    #properly disaggregating the "QBetseeSimmerWorkerSeed" subclass into
    #separate subclass implementations.

    # @abstractproperty
    def phase_kind(self) -> SimPhaseKind:
        '''
        Type of simulation phase run by this simulator worker.
        '''

        pass


    # @abstractproperty
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
    simulation subcommand in a multithreaded manner intended to be run by an
    arbitrary thread from a :class:`QThreadPool` container).
    '''

    # ..................{ METHODS                            }..................
    def _work(self) -> None:

        #FIXME: Non-ideal for the following obvious reasons:
        #
        #* The "main_window.sim_conf" object already has a Parameters() object
        #  in-memory. The changes performed here will *NOT* be propagated back
        #  into that object. That is bad.
        #* We shouldn't need to manually modify this file, anyway. Or should we?
        #  Should the GUI just assume absolute control over this file? That
        #  doesn't quite seem right, but it certainly would be simpler to do so.
        #  Well, at least for now.
        #FIXME: Ah-ha! The simplest means of circumventing the need to write
        #these changes back out to disk would be to refactor the
        #SimRunner.__init__() method to optionally accept a "Parameters" object
        #classified into a "_p" instance variable. Doing so, however, would mean
        #refactoring most methods of that class to reuse "_p" rather than
        #instantiate a new "Parameters" object each call. Of course, we arguably
        #should be doing that *ANYWAY* by unconditionally creating "_p" in
        #SimRunner.__init__() regardless of whether a "Parameters" object is
        #passed or not. We'll need to examine this further, of course.
        #FIXME: Pass the actual "self._p" object as is after refactoring the
        #SimRunner.__init__() method to accept such objects.

        #FIXME: Uncomment the plot_seed() call after pipelining that subcommand.

        # Run all simulation subcommands. Well, that was easy. (No, it really
        # wasn't.)
        sim_runner = SimRunner(conf_filename=self._p.conf_filename)
        sim_runner.seed()
        sim_runner.init()
        sim_runner.sim()
        # sim_runner.plot_seed()
        sim_runner.plot_init()
        sim_runner.plot_sim()
