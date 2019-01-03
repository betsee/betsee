#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator worker** (i.e., :mod:`PySide2`-based thread performing
the equivalent of a simulation subcommand in a Qt-aware manner) functionality.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication  # Slot, Signal
from betse.science.parameters import Parameters
from betse.science.simrunner import SimRunner
# from betse.util.io.log import logs
from betse.util.type import enums
from betse.util.type.cls import classes
from betse.util.type.decorator.decmemo import property_cached
from betse.util.type.obj import objects
from betse.util.type.types import type_check, CallableTypes
from betsee.guiexception import BetseePySideThreadWorkerException
from betsee.gui.simtab.run.guisimrunenum import SimmerState
from betsee.gui.simtab.run.phase.guisimrunphase import QBetseeSimmerPhase
from betsee.gui.simtab.run.work.guisimrunworkenum import SimmerPhaseSubkind
from betsee.gui.simtab.run.work.guisimrunworksig import SimCallbacksSignaller
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

        # Initialize our superclass.
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
                    objects.get_class_name_unqualified(self)))

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

# ....................{ SUBCLASSES                        }....................
class QBetseeSimmerPhaseWorker(QBetseeSimmerWorkerABC):
    '''
    Low-level **simulator phase worker** (i.e., simulator worker running an
    arbitrary simulation phase).

    Attributes
    ----------
    _phase : QBetseeSimmerPhase
        Simulator phase run by this worker.
    _phase_subkind : SimmerPhaseSubkind
        Type of work performed within this phase by this worker.
    '''

    # ..................{ INITIALIZERS                      }..................
    @type_check
    def __init__(
        self,
        phase: QBetseeSimmerPhase,
        phase_subkind: SimmerPhaseSubkind,
    ) -> None:
        '''
        Initialize this simulator phase worker.

        Parameters
        ----------
        phase : QBetseeSimmerPhase
            Simulator phase run by this worker.
        phase_subkind : SimmerPhaseSubkind
            Type of work performed within this phase by this worker.
        '''

        # Initialize our superclass.
        super().__init__()

        # Classify all passed parameters.
        self._phase = phase
        self._phase_subkind = phase_subkind

    # ..................{ PROPERTIES                        }..................
    # Read-only concrete properties.

    @property
    def phase(self) -> QBetseeSimmerPhase:
        '''
        Simulator phase run by this worker.
        '''

        return self._phase


    @property
    def phase_subkind(self) -> SimmerPhaseSubkind:
        '''
        Type of work performed within the simulator phase run by this worker.
        '''

        return self._phase_subkind


    @property_cached
    def simmer_state(self) -> SimmerState:
        '''
        Type of work performed within the simulator phase run by this worker as
        a member of the :class:`SimmerState` rather than
        :class:`SimmerPhaseSubkind` enumeration.
        '''

        return enums.get_member_from_value(
            enum_type=SimmerState,
            enum_member_value=self._phase_subkind.value)

    # ..................{ GETTERS                           }..................
    def _get_sim_runner_subcommand(self) -> CallableTypes:
        '''
        **Simulation subcommand** (i.e., public method of the
        :class:`SimRunner` class) run by this worker's :meth:`work` method.

        The :meth:`_work` method internally invokes this subcommand with the
        local :class:`SimRunner` instance created and returned by the
        :meth:`_make_sim_runner` method.

        Design
        ----------
        This callable is intentionally implemented as a getter rather than
        property. Although properties do largely obsolete getters, refactoring
        this getter into a property introduces awkward implicit calling
        semantics inviting spurious linter errors. Ergo, explicit is better
        than implicit in this edge case.
        '''

        # "_"-suffixed substring prefixing the name of the unbound "SimRunner"
        # method called by this worker if any *OR* the empty string otherwise.
        method_name_prefix = (
            'plot_' if self.phase_subkind is SimmerPhaseSubkind.EXPORTING else
            '')

        # Name of this method.
        method_name = method_name_prefix + self.phase.name

        # Return this method.
        return classes.get_method(cls=SimRunner, method_name=method_name)

    # ..................{ WORKERS                           }..................
    def _work(self) -> None:

        # Simulation phase runner whose thread affinity is that of the caller.
        sim_runner = self._make_sim_runner()

        # Simulation subcommand to be run by this worker.
        sim_runner_subcommand = self._get_sim_runner_subcommand()

        # Run this subcommand on this runner.
        sim_runner_subcommand(sim_runner)
