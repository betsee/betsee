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
from betse.util.type.decorator.deccls import abstractmethod, abstractproperty
from betse.util.type.decorator.decmemo import property_cached
# from betse.util.type.descriptor.descs import (
#     abstractclassproperty_readonly, classproperty_readonly)
from betse.util.type.obj import objects
from betse.util.type.types import type_check, CallableTypes
from betsee.guiexception import BetseePySideThreadWorkerException
from betsee.gui.simtab.run.guisimrunstate import SimmerState
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
    _conf_filename : StrOrNoneTypes
        Absolute filename of the YAML-formatted simulation configuration file
        defining the simulation to be run by this worker if the :meth:`init`
        method of this worker has been called *or* ``None`` otherwise.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self) -> None:
        '''
        Initialize this simulator worker.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__()

        # Nullify all instance variables for safety.
        self._conf_filename = None


    @type_check
    def init(self, conf_filename: str, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this simulator worker.

        Parameters
        ----------
        conf_filename : str
            Absolute filename of the YAML-formatted simulation configuration
            file defining the simulation to be run by this worker.

        All remaining parameters are passed as is to the superclass
        :meth:`init` method.
        '''

        # Finalize our superclass initialization with all passed parameters.
        super().init(*args, **kwargs)

        # Classify all passed parameters.
        self._conf_filename = conf_filename

    # ..................{ EXCEPTIONS                        }..................
    def _die_unless_initted(self) -> None:
        '''
        Raise an exception unless the :meth:`init` method has been called.

        Raises
        ----------
        BetseePySideThreadWorkerException
            If the :attr:`_conf_filename` instance variable is ``None``,
            in which case the :meth:`init` method has yet to be called.
        '''

        # If the filename of this worker's simulation configuration file has
        # yet to be set, the init() method has yet to be called. In this case,
        # raise an exception.
        if self._conf_filename is None:
            raise BetseePySideThreadWorkerException(
                '"{}" uninitialized (i.e., init() method not called).'.format(
                    objects.get_class_name(self)))

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

        # Raise an exception unless the :meth:`init` method has been called.
        self._die_unless_initted()

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
class QBetseeSimmerSubcmdWorkerABC(QBetseeSimmerWorkerABC):
    '''
    Abstract base class of all low-level **simulator subcommand worker** (i.e.,
    simulator worker running an arbitrary simulation subcommand) subclasses.
    '''

    # ..................{ PROPERTIES                        }..................
    # Read-only concrete properties.

    @property_cached
    def simmer_state(self) -> SimmerState:
        '''
        Type of work performed within the type of simulation phase run by this
        simulator worker as an equivalent member of the :class:`SimmerState`
        rather than :class:`SimmerPhaseSubkind` enumeration.
        '''

        return enums.get_member_from_value(
            enum_type=SimmerState, enum_member_value=self.phase_subkind.value)

    # ..................{ PROPERTIES ~ abstract             }..................
    # Read-only abstract properties required to be overridden by subclasses.

    @abstractproperty
    def phase_kind(self) -> SimPhaseKind:
        '''
        Type of simulation phase run by this simulator worker.
        '''

        pass


    @abstractproperty
    def phase_subkind(self) -> SimmerPhaseSubkind:
        '''
        Type of work performed within the type of simulation phase run by this
        simulator worker.
        '''

        pass

    # ..................{ GETTERS ~ abstract                }..................
    # Abstract getter methods required to be overridden by subclasses.

    @abstractmethod
    def _get_sim_runner_subcommand(self) -> CallableTypes:
        '''
        **Simulation subcommand** (i.e., public method of the
        :class:`SimRunner` class) run by this worker's :meth:`work` method.

        The :meth:`_work` method internally invokes this subcommand with the
        local :class:`SimRunner` instance created and returned by the
        :meth:`_make_sim_runner` method.

        Design
        ----------
        This callable is intentionally implemented as an abstract getter rather
        than abstract property. Although properties have largely obsoleted
        getters, refactoring this getter into a property introduces awkward
        implicit calling semantics which invite spurious linter errors. Ergo,
        explicit is better than implicit in this edge case.
        '''

        pass

    # ..................{ WORKERS                           }..................
    def _work(self) -> None:

        # Simulation phase runner whose thread affinity is that of the caller.
        sim_runner = self._make_sim_runner()

        # Simulation subcommand to be run by this worker.
        sim_runner_subcommand = self._get_sim_runner_subcommand()

        # Run this subcommand on this runner.
        sim_runner_subcommand(sim_runner)

# ....................{ SUPERCLASSES ~ subcommand : phase }....................
class QBetseeSimmerSeedWorkerABC(QBetseeSimmerSubcmdWorkerABC):
    '''
    Abstract base class of all low-level **simulator seed subcommand worker**
    (i.e., worker running the seed simulation subcommand) subclasses.
    '''

    # ..................{ SUPERCLASS                        }..................
    @property
    def phase_kind(self) -> SimPhaseKind:
        return SimPhaseKind.SEED

    def _get_sim_runner_subcommand(self) -> CallableTypes:
        return SimRunner.seed

# ....................{ MIXINS ~ subkind                  }....................
class QBetseeSimmerModelWorkerMixin(object):
    '''
    Mixin of all low-level **modelling simulator subcommand worker** (i.e.,
    worker modelling rather than exporting a simulation phase) subclasses.
    '''

    # ..................{ SUPERCLASS                        }..................
    @property
    def phase_subkind(self) -> SimmerPhaseSubkind:
        return SimmerPhaseSubkind.MODELLING


class QBetseeSimmerExportWorkerMixin(object):
    '''
    Mixin of all low-level **exporting simulator subcommand worker** (i.e.,
    worker exporting rather than modelling a simulation phase) subclasses.
    '''

    # ..................{ SUPERCLASS                        }..................
    @property
    def phase_subkind(self) -> SimmerPhaseSubkind:
        return SimmerPhaseSubkind.EXPORTING

# ....................{ SUBCLASSES ~ model                }....................
class QBetseeSimmerSeedModelWorker(
    QBetseeSimmerModelWorkerMixin, QBetseeSimmerSeedWorkerABC):
    '''
    Low-level simulator worker simulating the seed phase.
    '''

    pass

# ....................{ SUBCLASSES ~ subcommand : export  }....................
class QBetseeSimmerSeedExportWorker(
    QBetseeSimmerExportWorkerMixin, QBetseeSimmerSeedWorkerABC):
    '''
    Low-level simulator worker exporting the seed phase.
    '''

    pass
