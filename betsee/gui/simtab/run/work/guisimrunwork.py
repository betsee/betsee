#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator worker** (i.e., :mod:`PySide2`-based thread performing
the equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication  # Slot, Signal
from betse.science.parameters import Parameters
from betse.science.phase.phaseenum import SimPhaseKind
from betse.science.simrunner import SimRunner
# from betse.util.io.log import logs
from betse.util.type import enums
# from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.descriptor.descs import (
    abstractclassproperty_readonly, classproperty_readonly)
from betse.util.type.types import type_check, CallableTypes
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState, SIM_PHASE_KIND_TO_NAME)
from betsee.gui.simtab.run.work.guisimrunworkenum import SimmerPhaseSubkind
from betsee.gui.simtab.run.work.guisimrunworksig import SimCallbacksSignaller
# from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.util.thread.pool.guipoolwork import QBetseeThreadPoolWorker

# ....................{ SUPERCLASSES                      }....................
class QBetseeSimmerWorkerABC(QBetseeThreadPoolWorker):
    '''
    Abstract base class of all low-level **simulator worker** (i.e.,
    worker running one or more arbitrary simulation operations) subclasses.

    Attributes
    ----------
    _conf_filename : str
        Absolute path of the YAML-formatted simulation configuration file
        defining the simulation to be run by this worker.
    '''

    # ..................{ INITIALIZERS                      }..................
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

    # ..................{ MAKERS                            }..................
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

# ....................{ SUPERCLASSES ~ subcommand         }....................
class QBetseeSimmerSubcommandWorkerABC(QBetseeSimmerWorkerABC):
    '''
    Abstract base class of all low-level **simulator subcommand worker** (i.e.,
    simulator worker running an arbitrary simulation subcommand) subclasses.
    '''

    # ..................{ PROPERTIES                        }..................
    # Read-only concrete class methods.

    #FIXME: Cache the following class method(s), which remain constant
    #throughout the lifecycle of this application. To do so, we'll need to
    #implement a new
    #"betse.util.type.decorator.decmemo.classproperty_readonly_cached"
    #decorator -- which currently exceeds our budget for both time and sanity..

    @classproperty_readonly
    def simmer_state(cls) -> SimmerState:
        '''
        Type of work performed within the type of simulation phase run by this
        simulator worker as an equivalent member of the :class:`SimmerState`
        rather than :class:`SimmerPhaseSubkind` enumeration.
        '''

        return enums.get_member_from_value(
            enum_type=SimmerState, enum_member_value=cls.phase_subkind.value)

    # ..................{ PROPERTIES ~ abstract             }..................
    # Read-only abstract class methods required to be overridden by subclasses.

    @abstractclassproperty_readonly
    def phase_kind(cls) -> SimPhaseKind:
        '''
        Type of simulation phase run by this simulator worker.
        '''

        pass


    @abstractclassproperty_readonly
    def phase_subkind(cls) -> SimmerPhaseSubkind:
        '''
        Type of work performed within the type of simulation phase run by this
        simulator worker.
        '''

        pass

    # ..................{ PROPERTIES ~ abstract : private   }..................
    @abstractclassproperty_readonly
    def _sim_runner_subcommand(cls) -> CallableTypes:
        '''
        **Simulation subcommand** (i.e., public method of the
        :class:`SimRunner` class) to be run by this worker.

        The :meth:`_work` method internally invokes this subcommand with the
        local :class:`SimRunner` instance created and returned by the
        :meth:`_make_sim_runner` method.
        '''

        pass

    # ..................{ WORKERS                           }..................
    def _work(self) -> None:

        # Simulation phase runner whose thread affinity is that of the caller.
        sim_runner = self._make_sim_runner()

        # Run the subclass-specific simulation subcommand.
        self._sim_runner_subcommand(sim_runner)


class QBetseeSimmerSubcommandWorkerModelABC(QBetseeSimmerSubcommandWorkerABC):
    '''
    Abstract base class of all low-level **modelling simulator subcommand
    worker** (i.e., simulator worker running a simulation subcommand modelling
    rather than exporting a simulation phase) subclasses.
    '''

    # ..................{ PROPERTIES ~ superclass           }..................
    @classproperty_readonly
    def phase_subkind(cls) -> SimmerPhaseSubkind:
        return SimmerPhaseSubkind.MODELLING


class QBetseeSimmerSubcommandWorkerExportABC(QBetseeSimmerSubcommandWorkerABC):
    '''
    Abstract base class of all low-level **exporting simulator subcommand
    worker** (i.e., simulator worker running a simulation subcommand exporting
    rather than modelling a simulation phase) subclasses.
    '''

    # ..................{ PROPERTIES ~ superclass           }..................
    @classproperty_readonly
    def phase_subkind(cls) -> SimmerPhaseSubkind:
        return SimmerPhaseSubkind.EXPORTING

# ....................{ SUBCLASSES ~ subcommand : model   }....................
class QBetseeSimmerSubcommandWorkerModelSeed(
    QBetseeSimmerSubcommandWorkerModelABC):
    '''
    Low-level simulator worker simulating the seed phase.
    '''

    # ..................{ PROPERTIES                        }..................
    @classproperty_readonly
    def phase_kind(cls) -> SimPhaseKind:
        return SimPhaseKind.SEED

    @classproperty_readonly
    def _sim_runner_subcommand(cls) -> CallableTypes:
        return SimRunner.seed

# ....................{ SUBCLASSES ~ subcommand : export  }....................
#FIXME: Actually use this subclass elsewhere after pipelining the
#"betse plot seed" subcommand.
class QBetseeSimmerSubcommandWorkerExportSeed(
    QBetseeSimmerSubcommandWorkerABC):
    '''
    Low-level simulator worker exporting the seed phase.
    '''

    # ..................{ PROPERTIES                        }..................
    @classproperty_readonly
    def phase_kind(cls) -> SimPhaseKind:
        return SimPhaseKind.SEED

    @classproperty_readonly
    def _sim_runner_subcommand(cls) -> CallableTypes:
        return SimRunner.plot_seed
