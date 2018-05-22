#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator worker** (i.e., :mod:`PySide2`-based thread performing the
equivalent of a simulation subcommand in a Qt-aware manner) functionality.
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
from betse.science.parameters import Parameters
from betse.science.phase.phaseenum import SimPhaseKind
from betse.science.simrunner import SimRunner
# from betse.util.io.log import logs
# from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.types import type_check
# from betsee.guiexception import BetseeSimmerException
# from betsee.gui.simtab.run.guisimrunphase import QBetseeSimmerPhase
# from betsee.gui.simtab.run.guisimrunstate import SimmerState
from betsee.gui.simtab.run.work.guisimrunworkenum import (
    SimmerWorkerPhaseSubkind)
from betsee.gui.simtab.run.work.guisimrunworksig import SimCallbacksSignaller
from betsee.util.thread.pool.guipoolwork import QBetseeThreadPoolWorker

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimmerWorkerABC(QBetseeThreadPoolWorker):
    '''
    Abstract base class of all low-level **simulator worker** (i.e., thread-safe
    object running a single startable, pausable, resumable, and haltable
    simulation subcommand in a multithreaded manner intended to be run by an
    arbitrary thread from a :class:`QThreadPool` container) subclasses.

    Attributes
    ----------
    _conf_filename : str
        Absolute path of the YAML-formatted simulation configuration file
        defining the simulation to be run by this worker.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, conf_filename: str) -> None:
        '''
        Initialize this simulator worker.

        Attributes
        ----------
        conf_filename : str
            Absolute path of the YAML-formatted simulation configuration file
            defining the simulation to be run by this worker.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__()

        # Classify all passed parameters.
        self._conf_filename = conf_filename

    # ..................{ PROPERTIES ~ abstract             }..................
    def _make_sim_runner(self) -> SimRunner:
        '''
        Create and return a new **simulation phase runner** (i.e., high-level
        object encapsulating the running of simulation phases as corresponding
        public methods commonly referred to as simulation subcommands), whose
        thread affinity is that of the caller.

        Caveats
        ----------
        To ensure that this runner is owned by the thread running the
        :meth:`run` and :meth:`_work` methods, this method should be called
        *only* from the :meth:`_work` method.

        This method is intentionally implemented to create and return a new
        runner whose thread affinity is that of the caller. If this method were
        instead implemented to classify this runner is an instance variable of
        this superclass (e.g., ``self._sim_runner``), the thread affinity of
        this runner would erroneously be that of the main event thread.
        '''

        # Simulation configuration whose thread affinity is that of the caller.
        p = self._make_p()

        # Simulation phase callbacks whose thread affinity is that of the
        # caller.
        callbacks = SimCallbacksSignaller(signals=self.signals)

        # Simulation phase runner whose thread affinity is that of the caller.
        sim_runner = SimRunner(p=p, callbacks=callbacks)

        # Return this runner.
        return sim_runner


    def _make_p(self) -> Parameters:
        '''
        Create and return a deep copy of the singleton simulation
        configuration (i.e., :attr:`QBetseeMainWindow.sim_conf.p`), whose
        thread affinity is that of the caller.

        This method bridges the critical gap between the low-level CLI-based
        simulation runner and this high-level GUI-based simulator, making this
        the most important callable in either codebase.

        Design
        ----------
        For thread-safety, this worker returns a deep copy of the singleton
        simulation configuration rather than a shallow reference to that
        simulation configuration; ergo, that object is guaranteed to remain
        unchanged by this worker.

        Doing so also permits this method to dynamically reconfigure this
        configuration in-memory to satisfy GUI requirements, including:

        * Disable all simulation configuration options either requiring
          interactive user input *or* displaying graphical output intended for
          interactive user consumption (e.g., plots, animations).
        * Enable all simulation configuration options exporting to disk.

        Returns
        ----------
        Parameters
            Deep copy of the singleton simulation configuration (i.e.,
            :attr:`QBetseeMainWindow.sim_conf.p`), whose thread affinity is
            that of the caller.
        '''

        # Simulation configuration newly deserialized from the passed original
        # Simulation configuration.
        p = Parameters.make(self._conf_filename)

        # Disable all simulation configuration options either requiring
        # interactive user input *OR* displaying graphical output intended for
        # interactive user consumption (e.g., plots, animations).
        p.anim.is_after_sim_show = False
        p.anim.is_while_sim_show = False
        p.plot.is_after_sim_show = False

        # Enable all simulation configuration options exporting to disk.
        p.anim.is_after_sim_save = True
        p.anim.is_while_sim_save = True
        p.plot.is_after_sim_save = True

        # Return this configuration.
        return p

    # ..................{ PROPERTIES ~ abstract             }..................
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

# ....................{ SUBCLASSES                        }....................
#FIXME: Define *NO* additional subclasses until this subclass has been shown to
#behave as expected. Why? Because copying-and-pasting says, "Do a right thing."
class QBetseeSimmerWorkerSeed(QBetseeSimmerWorkerABC):
    '''
    Low-level **seed-specific simulator worker** (i.e., thread-safe object
    running a single startable, pausable, resumable, and haltable "seed"
    simulation subcommand in a multithreaded manner intended to be run by an
    arbitrary thread from a :class:`QThreadPool` container).
    '''

    # ..................{ WORKERS                           }..................
    def _work(self) -> None:

        # Simulation phase runner whose thread affinity is that of the caller.
        sim_runner = self._make_sim_runner()

        #FIXME: Uncomment the plot_seed() call after pipelining that subcommand.

        # Run all simulation subcommands. Well, that was easy. (No, it really
        # wasn't.)
        sim_runner.seed()
        sim_runner.init()
        sim_runner.sim()
        # sim_runner.plot_seed()
        sim_runner.plot_init()
        sim_runner.plot_sim()
