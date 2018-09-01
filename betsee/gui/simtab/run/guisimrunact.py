#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator proactor** (i.e., :mod:`PySide2`-based object
controlling but *not* displaying the execution of simulation phases)
functionality.
'''

#FIXME: Improve the underlying exporting simulation subcommands in BETSE (e.g.,
#"betse plot seed") to perform routine progress callbacks.

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, QObject, Slot  #, Signal
from PySide2.QtWidgets import QProgressBar, QLabel
from betse.exceptions import BetseSimUnstableException
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.py import pythread
from betse.util.type import enums
from betse.util.type.obj import objects
from betse.util.type.types import type_check
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
from betsee.gui.simtab.run.phase.guisimrunphaser import QBetseeSimmerPhaser
from betsee.gui.simtab.run.work.guisimrunwork import QBetseeSimmerPhaseWorker
from betsee.gui.simtab.run.work.guisimrunworkenum import SimmerPhaseSubkind
from betsee.util.thread import guithread
from betsee.util.thread.pool import guipoolthread
from collections import deque

# ....................{ CLASSES                           }....................
class QBetseeSimmerProactor(QBetseeSimmerStatefulABC):
    '''
    High-level **simulator proactor** (i.e., :mod:`PySide2`-based object
    controlling but *not* displaying the execution of simulation phases).

    This proactor maintains all state needed to manage these phases, including:

    * A queue of all simulation subcommands to be interactively run.
    * Whether or not a simulation subcommand is currently being run.
    * The state of the currently run simulation subcommand (if any), including:

      * Visualization (typically, Vmem animation) of the most recent step
        completed for this subcommand.
      * Textual status describing this step in human-readable language.
      * Numeric progress as a relative function of the total number of steps
        required by this subcommand.

    Design
    ----------
    This proactor implements the well-known `proactor design pattern`_, whereby
    each simulation subcommand is asynchronously run by a simulator worker
    assigned to a pooled thread dedicated to that worker. This pattern is
    effectively an asynchronous variant of the `reactor design pattern`_.

    For maintainability, this proactor subsumes *all* roles defined by this
    pattern except the core role of the **asynchronous operation** (e.g., work
    performed by each worker), including the following roles:

    * **Proactive initiator** (i.e., the highest-level parent object
      responsible for governing all asynchronous activity).
    * **Asynchronous operation processor** (i.e., the second-highest-level
      parent object responsible for starting the asynchronous activity and
      forwarding responsibility for handling its completion to the completion
      dispatcher).
    * **Completion dispatcher** (i.e., the second-lowest-level child object
      responsible for receiving control from the asynchronous operation
      processor on the completion of the asynchronous activity and forwarding
      responsibility for handling its completion to the completion handler).
    * **Completion handler** (i.e., the lowest-level child object responsible
      for handling the actual completion of the asynchronous activity).

    .. _proactor design pattern:
       https://en.wikipedia.org/wiki/Proactor_pattern
    .. _reactor design pattern:
       https://en.wikipedia.org/wiki/Reactor_pattern

    Caveats
    ----------
    For simplicity, this proactor internally assumes the active Python
    interpreter to prohibit Python-based multithreading via a Global
    Interpreter Lock (GIL). Specifically, all worker-centric attributes (e.g.,
    :attr:`_worker`, :attr:`_workers_queued`) are assumed to be implicitly
    synchronized despite access to these attributes *not* being explicitly
    locked behind a Qt-based mutual exclusion primitive.

    GIL-less Python interpreters violate this simplistic assumption. For
    example, the :meth:`stop_workers` and :meth:`_handle_worker_completion`
    slots suffer obvious (albeit unlikely) race conditions under GIL-less
    interpreters due to competitively deleting the same underlying worker in a
    desynchronized and hence non-deterministic manner.

    Yes, this is assuredly a bad idea. Yes, this is us nonchalantly shrugging.

    Attributes (Public)
    ----------
    phaser : QBetseeSimmerPhaser
        Container containing all simulator phase controllers.

    Attributes (Private)
    ----------
    _p : Parameters
        Simulation configuration singleton.

    Attributes (Private: Thread)
    ----------
    _thread : QBetseeWorkerThread
        Thread controller owning all simulator workers (i.e.,
        :class:`QBetseeSimmerWorkerABC` instances responsible for running
        queued simulation subcommands in a multithreaded manner).
    _workers_queued : {QueueType, NoneType}
        **Simulator worker queue** (i.e., double-ended queue of each simulator
        worker to be subsequently run in a multithreaded manner by the parent
        proactor to run a simulation subcommand whose corresponding checkbox
        was checked at the time this queue was instantiated) if this simulator
        has started one or more such workers *or* ``None`` otherwise (i.e., if
        no such workers have been started).

    Attributes (Private: Widgets)
    ----------
    _progress_bar : QProgressBar
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_progress` widget.
    _progress_status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_status` label.
    _progress_substatus : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_substatus` label.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        #FIXME: Yeah... fix this, please. PyPy will probably make the GIL
        #optionally go away at some point. (At least, it certainly should.)

        # Raise an exception unless the active Python interpreter has a GIL, as
        # foolishly required by methods defined by this class.
        pythread.die_unless_gil()

        # Nullify all remaining instance variables for safety.
        self._p = None
        self._progress_bar = None
        self._progress_status = None
        self._workers_queued = None

        # Container of allsSimulator phase controllers.
        self.phaser = QBetseeSimmerPhaser(self)


    @type_check
    def init(
        self,
        main_window: QBetseeMainWindow,
        progress_bar: QProgressBar,
        progress_status: QLabel,
        progress_substatus: QLabel,
    ) -> None:
        '''
        Finalize this simulator's initialization, owned by the passed main
        window widget.

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
        progress_bar : QProgressBar
            Alias of the :attr:`QBetseeMainWindow.sim_run_player_progress`
            widget.
        progress_status : QLabel
            Alias of the :attr:`QBetseeMainWindow.sim_run_player_status` label.
        progress_substatus : QLabel
            Alias of the :attr:`QBetseeMainWindow.sim_run_player_substatus`
            label.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Log this finalization.
        logs.log_debug('Sanitizing simulator proactor state...')

        # Classify variables of this main window required by this simulator.
        self._p = main_window.sim_conf.p

        # Classify all remaining passed parameters.
        self._progress_bar       = progress_bar
        self._progress_status    = progress_status
        self._progress_substatus = progress_substatus

        # Initialize the container of all simulator phase controllers.
        self.phaser.init(
            main_window=main_window,
            set_state_from_phase=self._set_state_from_phase,
        )

    # ..................{ FINALIZERS                        }..................
    def halt_workers(self) -> None:
        '''
        Coercively (i.e., non-gracefully) halt the current simulator worker if
        any *and* dequeue all subsequently queued workers in a thread-safe
        manner, reverting the simulator to the idle state... **by any means
        necessary.**

        This high-level method subsumes the lower-level :meth:`stop_workers`
        slot by (in order):

        #. If no worker is currently working, silently reducing to a noop.
        #. Attempting to gracefully halt the currently working worker, dequeue
           all subsequently queued workers if any, and unblock this worker's
           parent thread if currently blocked.
        #. If this worker fails to gracefully halt within a reasonable window
           of time (e.g., 30 seconds), coerce this worker to immediately halt.

        Design
        ----------
        This method *must* called at application shutdown (e.g., by the parent
        main window). If this is not done *and* a previously running simulator
        worker is currently paused and hence indefinitely blocking its parent
        thread, this application will itself indefinitely block rather than
        actually shutdown. Which, of course, would be catastrophic.

        Caveats
        ----------
        This method may induce data loss or corruption in simulation output.
        In theory, this should only occur in edge cases in which the current
        simulator worker fails to gracefully stop within a sensible window of
        time. In practice, this implies that this method should *only* be
        called when otherwise unavoidable (e.g., at application shutdown).
        '''

        # Maximum number of milliseconds to block the current thread waiting
        # for the currently working worker (if any) to gracefully halt.
        WAIT_MAX_MILLISECONDS = 30000  # 30 seconds

        # Log this shutdown.
        logs.log_debug('Finalizing simulator workers...')

        # If no worker is currently working, silently reduce to a noop.
        if not self.is_worker:
            return
        # Else, some worker is currently working.

        # Currently working simulator worker. For safety, this property is
        # localized *BEFORE* this worker's stop() pseudo-slot (which
        # internally dequeues this worker and hence implicitly modifies the
        # worker returned by the "_worker" property) is called.
        worker = self.worker

        # Attempt to gracefully halt this worker, dequeue all subsequently
        # queued workers if any, and unblock this worker's parent thread if
        # currently blocked.
        self.stop_workers()

        # If this worker fails to gracefully halt within a reasonable window
        # of time (e.g., 30 seconds), coerce this worker to immediately halt.
        guipoolthread.halt_workers(
            workers=(worker,), milliseconds=WAIT_MAX_MILLISECONDS)

    # ..................{ PROPERTIES ~ bool                 }..................
    @property
    def is_queued(self) -> bool:

        # Return true only if one or more phases are queued.
        return any(phase.is_queued for phase in self.phaser.PHASES)


    @property
    def is_worker(self) -> bool:
        '''
        ``True`` only if one or more simulator workers currently exist.

        Equivalently, this property returns ``True`` only if the simulator
        worker queue is currently non-empty.

        Design
        ----------
        For safety, this property should be tested *before* attempting to
        access the :meth:`worker` property, which raises an exception when no
        simulator workers currently exist.
        '''

        # Return true only if a non-empty queue of all phases to be run
        # currently exists. The lifecycle of this queue is managed in a just in
        # time (JIT) manner corresponding exactly to whether or not the
        # simulator and hence a simulator worker is currently working.
        # Specifically:
        #
        # * This queue defaults to "None".
        # * The toggle_work() slot instantiates this queue on initially
        #   starting a new queue of simulator workers.
        # * The stop_workers() slot reverts this queue back to "None".
        #
        # For efficiency, return this queue reduced to a boolean -- equivalent
        # to this less efficient (but more readable) pair of tests:
        #
        #    return self._workers_cls is not None and len(self._workers_cls)
        return bool(self._workers_queued)

    # ..................{ PROPERTIES ~ bool : state         }..................
    @property
    def is_workable(self) -> bool:
        '''
        ``True`` only if this proactor is **workable** (i.e., currently capable
        of performing work).

        This property returns ``True`` only if this proactor is guaranteed to
        be safely startable, resumable, or pausable and hence "workable."
        Equivalently, this property returns ``True`` only if the current state
        of this proactor is neither of the following states:

        * Unqueued. In this state, this proactor is required to wait until the
          user queues at least one simulation subcommand.
        * Stopping. In this state, this proactor is required to wait until the
          currently stopping worker does so gracefully.

        In either case, this proactor is incapable of performing work until its
        state changes to any other state -- all of which support work.
        '''

        return self.state not in SIMMER_STATES_UNWORKABLE


    @property
    def is_working(self) -> bool:
        '''
        ``True`` only if the simulator is **working** (i.e., some proactor
        worker is either running or paused from running some queued proactor
        phase and hence is *not* finished).

        If this fine-grained property is ``True``, note that it is necessarily
        the case that the coarse-grained :attr:`is_workable` property is also
        ``True`` but that the reverse is *not* necessarily the case.
        Equivalently, this proactor is *always* workable when it is working but
        *not* necessarily working when it is workable (e.g., due to currently
        being queued but unstarted).
        '''

        return self.state in SIMMER_STATES_WORKING


    @property
    def is_running(self) -> bool:
        '''
        ``True`` only if the simulator is **running** (i.e., some simulator
        worker is currently modelling or exporting some queued simulator phase
        and hence is neither paused nor finished).

        If this fine-grained property is ``True``, note that it is necessarily
        the case that the coarse-grained :attr:`is_working` and
        :attr:`is_workable` properties are also ``True`` but that the reverse
        is *not* necessarily the case.  Equivalently, the simulator is *always*
        working when it is running but *not* necessarily running when it is
        working (e.g., due to currently being paused).
        '''

        return self.state in SIMMER_STATES_RUNNING

    # ..................{ PROPERTIES ~ worker               }..................
    @property
    def worker(self) -> QBetseeSimmerPhaseWorker:
        '''
        **Currently working worker** (i.e., :class:`QRunnable` instance
        currently modelling or exporting a previously queued simulation phase
        in another thread) if any *or* raise an exception otherwise (i.e., if
        no workers are currently working).

        Raises
        ----------
        BetseeSimmerException
            If no worker is currently working.
        '''

        # If no worker is working, raise an exception.
        self._die_unless_working()

        # Return the head worker of the worker queue.
        return self._workers_queued[0]

    # ..................{ PROPERTIES ~ private : bool       }..................
    @property
    def _is_paused(self) -> bool:
        '''
        ``True`` only if the simulator is **paused** (i.e., some simulator
        worker is currently paused while previously modelling or exporting some
        queued simulator phase and hence is neither running nor finished).
        '''

        return self.state is SimmerState.PAUSED

    # ..................{ PROPERTIES ~ private : phase      }..................
    @property
    def _worker_phase_state(self) -> SimmerState:
        '''
        State of the queued simulator phase that is currently **running**
        (i.e., either being modelled or exported by this simulator) if any *or*
        raise an exception otherwise.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`is_worker` property
        is ``True``).

        Design
        ----------
        This property getter trivially reduces to a direct access of the
        :attr:`_worker.phase.state` instance variable, but exists to define the
        corresponding non-trivial property setter.

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
            :attr:`_workers_cls` is either ``None`` or empty).
        '''

        return self.worker.phase.state


    @_worker_phase_state.setter
    @type_check
    def _worker_phase_state(self, state: SimmerState) -> None:
        '''
        Set the state of the queued simulator phase that is currently
        **running** (i.e., either being modelled or exported by this simulator)
        if any to the passed state *or* raise an exception otherwise.

        This property setter may additionally set the state of this simulator
        to the passed state (depending on the current state of this simulator
        and the passed state). Doing so avoids subtle desynchronization issues
        between the state of this phase and this simulator. In particular, if a
        queued simulator phase is currently running, this simulator's state is
        guaranteed to be *always* the state of that phase.

        Caveats
        ----------
        For safety, this property should *only* be accessed when this queue is
        guaranteed to be non-empty (i.e., when the :meth:`is_worker` property
        is ``True``).

        Parameters
        ----------
        state : SimmerState
            New state to set this phase to.

        Raises
        ----------
        BetseeSimmerException
            If no simulator phase is currently running (i.e.,
            :attr:`_workers_cls` is either ``None`` or empty).
        '''

        # Currently working phase, localized purely for negligible efficiency.
        worker_phase = self.worker.phase

        # Log this setting.
        logs.log_debug(
            'Updating simulator phase "%s" state from "%s" to "%s"...',
            worker_phase.name,
            enums.get_member_name_lowercase(worker_phase.state),
            enums.get_member_name_lowercase(state))

        # Set the state of the currently running phase to this state.
        worker_phase.state = state

        # Possibly set the state of this simulator to the same state.
        self._set_state_from_phase(worker_phase)


    @Slot(QObject)
    def _set_state_from_phase(self, phase: QBetseeSimmerPhase) -> None:
        '''
        Context-sensitively set the current state of this proactor to the
        current state of the passed simulator phase.

        Parameters
        ----------
        phase : QBetseeSimmerPhase
            Simulator phase whose current state has been previously set.
        '''

        # New state to change this proactor to if any *OR* "None" otherwise.
        state_new = None

        # If the current state of either:
        #
        # * This phase is fixed (i.e., high-priority) and hence superceding the
        #   current state of this proactor...
        # * This proactor is fluid (i.e., low-priority) and hence superceded
        #   by the current state of this phase...
        if (
            phase.state in SIMMER_STATES_INTO_FIXED or
             self.state in SIMMER_STATES_FROM_FLUID
        ):
            # If this phase's new state is unqueued...
            if phase.state is SimmerState.UNQUEUED:
                # If one or more *OTHER* phases are still queued, ignore this
                # phase's change. Unqueueing is minimally low priority.
                if self.is_queued:
                    pass
                # Else, all phases are unqueued. Set the current state of this
                # simulator to also be unqueued.
                else:
                    state_new = SimmerState.UNQUEUED
            # Else, this phase's new state unconditionally takes precedence.
            # Set this proactor's current state to this phase's new state.
            else:
                state_new = phase.state
        # Else, silently preserve this proactor's current state as is.

        # If preserving the state of this proactor...
        if state_new is None:
            # Log this preservation.
            logs.log_debug(
                'Preserving simulator state as "%s"...',
                enums.get_member_name_lowercase(self.state))

            # Preserve the state of this proactor below. As "None" is *NOT* a
            # valid state, reuse the existing state as is.
            state_new = self.state
        # Else, the state of this simulator is being changed. In this case...
        else:
            # Log this change.
            logs.log_debug(
                'Updating simulator proactor state from "%s" to "%s"...',
                enums.get_member_name_lowercase(self.state),
                enums.get_member_name_lowercase(state_new))

        # Unconditionally change the state of this proactor to this new state,
        # regardless of whether this state is already this new state. Why?
        # Because the superclass state() setter internally signals all slots
        # connected to the "set_state_signal" for this proactor -- including
        # the QBetseeSimmer._update_widgets() slot.
        #
        # The question then reduces to: "Do widgets require updating even when
        # the current state of this proactor remains unchanged?" The answer, of
        # course, is: "Absolutely." Proactor state is a lossy coarse-grained
        # abstraction at best that fails to capture all possible simulator
        # state. In particular, proactor state remains unchanged on dequeueing
        # exactly one but *NOT* all queued simulator phases -- a common case
        # clearly requiring widgets (e.g., progress substatus) to be updated.
        # (Good luck debugging this, new hire!)
        self.state = state_new

    # ..................{ EXCEPTIONS                        }..................
    def _die_unless_workable(self) -> None:
        '''
        Raise an exception unless the simulator is **workable** (i.e.,
        currently capable of performing work).

        Raises
        ----------
        BetseeSimmerException
            If the simulator is unworkable.

        See Also
        ----------
        :meth:`is_workable`
            Further details.
        '''

        if not self.is_workable:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmerProactor',
                'Simulator not workable '
                '(i.e., not currently working and no phases queued).'))

    # ..................{ EXCEPTIONS ~ state                }..................
    def _die_unless_running(self) -> None:
        '''
        Raise an exception unless the simulator is **running** (i.e., some
        simulator worker is currently modelling or exporting some queued
        simulation phase and hence is neither paused nor finished).

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* running, in which case the simulator is
            either paused or finished.

        See Also
        ----------
        :meth:`is_running`
            Further details.
        '''

        if not self.is_running:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmerProactor',
                'Simulator not running '
                '(i.e., either paused, finished, or not started).'))


    def _die_unless_paused(self) -> None:
        '''
        Raise an exception unless the simulator is **paused** (i.e., some
        simulator worker is currently paused while previously modelling or
        exporting some queued simulation phase and hence is neither running nor
        finished).

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* paused, in which case the simulator is
            either running or finished.

        See Also
        ----------
        :meth:`_is_paused`
            Further details.
        '''

        if not self._is_paused:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmerProactor',
                'Simulator not paused '
                '(i.e., either running, finished, or not started).'))

    # ..................{ EXCEPTIONS ~ working              }..................
    def _die_if_working(self) -> None:
        '''
        Raise an exception if some simulator worker is currently working.

        Raises
        ----------
        BetseeSimmerException
            If some simulator worker is currently working.

        See Also
        ----------
        :meth:`is_worker`
            Further details.
        '''

        if self.is_worker:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmerProactor', 'Simulation currently working.'))


    def _die_unless_working(self) -> None:
        '''
        Raise an exception unless some simulator worker is currently working.

        Raises
        ----------
        BetseeSimmerException
            If no simulator worker is currently working.

        See Also
        ----------
        :meth:`is_worker`
            Further details.
        '''

        if not self.is_worker:
            raise BetseeSimmerException(QCoreApplication.translate(
                'QBetseeSimmerProactor', 'No simulation currently working.'))

    # ..................{ SLOTS ~ action : work             }..................
    # Slots connected to signals emitted by "QAction" objects specific to the
    # currently running simulator worker if any.

    #FIXME: Rewrite documentation to note the considerably changed behaviour.
    @Slot(bool)
    def toggle_work(self, is_playing: bool) -> None:
        '''
        Slot signalled on either the user interactively *or* the codebase
        programmatically pushing the :class:`QPushButton` widget corresponding
        to the :attr:`_action_toggle_work` variable.

        This slot runs the currently queued phase by either:

        * If this phase is currently paused, resuming this phase.
        * Else, starting this phase.

        Parameters
        ----------
        is_playing : bool
            ``True`` only if the corresponding :class:`QPushButton` widget is
            toggled, implying the user to have requested that the simulator be
            either started or resumed, contextually depending on the current
            state of the simulator; conversely, ``False`` implies a request
            that the simulator be paused.
        '''

        # Log this slot.
        guithread.log_debug_thread_main(
            'Toggling simulator work by user request...')

        # If the simulator is unworkable, raise an exception.
        self._die_unless_workable()

        # If the user requested the simulator be started or unpaused...
        if is_playing:
            # If the simulator is currently working, some simulator worker was
            # previously working before being paused by a prior call to this
            # slot. In this case, resume this worker.
            if self.is_worker:
                self._resume_worker()
            # Else, the simulator is *NOT* currently working. In this case,
            # enqueue all currently queued simulation phases as simulator
            # workers and start the first such worker.
            else:
                self._start_workers()
        # Else, the user requested the simulator be paused. Do so.
        else:
            self._pause_worker()


    def _start_workers(self) -> None:
        '''
        Enqueue one simulator worker for each simulation subcommand whose
        corresponding checkbox in a simulator phase is currently checked *and*
        iteratively start each such worker in a thread-safe manner.

        Raises
        ----------
        BetseeSimmerException
            If either:

            * No simulator phase is currently queued (i.e., no such checkboxes
              are currently checked).
            * One or more workers are already working.
        '''

        # Log this action.
        guithread.log_debug_thread_main(
            'Starting simulator work by user request...')

        # If no simulator phase is currently queued, raise an exception.
        self._die_unless_queued()

        # If one or more workers are already working, raise an exception.
        guipoolthread.die_if_working()

        # Initialize the queue of simulator phases to be run.
        self._enqueue_workers()

        # Initiate iteration by starting the first enqueued worker and
        # connecting the stop signal emitted by that worker to a slot
        # iteratively repeating this process.
        self._loop_worker()


    def _pause_worker(self) -> None:
        '''
        Pause the currently running simulator.

        This method temporarily pauses the current simulator worker in a
        thread-safe manner safely resumable at any time by calling the
        :meth:`_resume_worker` method.

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* currently running.
        '''

        # Log this action.
        guithread.log_debug_thread_main(
            'Pausing simulator work by user request...')

        # If the simulator is *not* currently running, raise an exception.
        self._die_unless_running()

        # Set both this proactor and the currently working phase to the paused
        # state *BEFORE* successfully pausing this worker. See the
        # stop_workers() method for related commentary on this order of logic.
        self._worker_phase_state = SimmerState.PAUSED

        # Pause the currently running proactor worker.
        self.worker.pause()


    def _resume_worker(self) -> None:
        '''
        Resume the currently paused simulator.

        This method resumes the current simulator worker in a thread-safe
        manner after having been previously paused by a call to the
        :meth:`_pause_worker` method.

        Raises
        ----------
        BetseeSimmerException
            If the simulator is *not* currently paused.
        '''

        # Log this action.
        guithread.log_debug_thread_main(
            'Resuming simulator work by user request...')

        # If the simulator is *not* currently paused, raise an exception.
        self._die_unless_paused()

        # Revert both this proactor and the currently working phase to the
        # worker-specific running state *BEFORE* successfully resuming this
        # worker. See the stop_workers() method for related commentary on this
        # order of logic.
        self._worker_phase_state = self.worker.simmer_state

        # Resume the currently paused simulator worker.
        self.worker.resume()

    # ..................{ SLOTS ~ action : stop             }..................
    @Slot()
    def stop_workers(self) -> None:
        '''
        Slot signalled on the user interactively (but *not* the codebase
        programmatically) clicking the :class:`QPushButton` widget associated
        with the :attr:`_actionstop_workers` action.

        This method effectively reverts the simulator to the idle state in a
        thread-safe manner by (in order):

        #. Unpausing the current simulator worker if currently paused, thus
           unblocking this worker's parent thread if currently blocked.
        #. Gracefully halting this worker.
        #. Dequeueing all subsequently queued workers.

        Raises
        ----------
        BetseeSimmerException
            If no simulator worker is currently working.
        '''

        # Log this slot.
        guithread.log_debug_thread_main(
            'Stopping simulator work by user request...')

        # If no worker is currently working, raise an exception.
        self._die_unless_working()

        # Currently working simulator worker. For safety, this property is
        # localized *BEFORE* this worker's stop() pseudo-slot (which
        # implicitly signals the _handle_worker_completion() slot, which
        # internally dequeues this worker and hence implicitly modifies the
        # worker returned by the "_worker" property) is called.
        worker = self.worker

        # Set both this proactor and the currently working phase to the
        # stopping state *BEFORE* successfully stopping this worker.
        #
        # Doing so enforces mutual exclusivity from the end user perspective
        # with respect to proactor state. Specifically, setting this state
        # prior to all subsequent logic forces the UI to immediately reflect
        # this request to stop all work and hence prevents the user from
        # issuing any subsequent actions at odds with that request (e.g., to
        # pause or re-stop work) -- regardless of whether that request is
        # successfully fulfilled. If the order of these operations were
        # reversed (i.e., if this worker was stopped prior to setting this
        # state), a window of time would exist in which the UI failed to
        # reflect this request to stop and hence permitted the user to issue
        # subsequent actions at odds with that request. In short, this is sane.
        self._worker_phase_state = SimmerState.STOPPING

        # Dequeue *ALL* currently enqueued simulator workers scheduled to work
        # following the currently working worker. While the latter could
        # theoretically be dequeued as well, doing so would prevent the
        # _handle_worker_completion() slot transitively called by the call to
        # the stop() pseudo-slot below from setting the state of the phase
        # associated with the currently working worker. In short, this works.
        #
        # For negligible efficiency, this queue is recreated from scratch to
        # contain only this worker rather than iteratively popping all items
        # except the first from this queue (e.g., by calling the
        # queues.pop_left() function).
        self._workers_queued = deque((worker,))

        # Stop this worker *AFTER* dequeueing all currently enqueued workers
        # and setting this simulator state.
        #
        # While feasible, reversing this order of operations invites subtle
        # race conditions between this slot and the _handle_worker_completion()
        # slot signalled by this call, which calls the _loop_worker() method,
        # which calls the _dequeue_workers() method. Since the stop() method
        # called here signals the _handle_worker_completion() slot in a
        # multithreaded and hence non-deterministic manner, badness ensues.
        worker.stop()

    # ..................{ QUEUERS                           }..................
    def _enqueue_workers(self) -> None:
        '''
        Create the **simulator worker queue** (i.e., :attr:`_workers_queued`
        variable) as specified by the pair of checkboxes associated with each
        simulator phase.

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

        Raises
        ----------
        BetseeSimmerException
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


    def _dequeue_workers(self) -> None:
        '''
        Revert the :attr:`_workers_queued` to ``None``, effectively dequeueing
        (i.e., popping) all previously queued simulator workers.
        '''

        # Log this action.
        guithread.log_debug_thread_main('Dequeueing simulator workers...')

        # If no simulator worker is currently working, raise an exception.
        self._die_unless_working()

        # Clear this queue, implicitly scheduling all previously queued workers
        # for garbage collection *AND* disconnecting all external slots
        # previously connected to signals defined by these workers.
        self._workers_queued = None

    # ..................{ WORKERS ~ loop                    }..................
    def _loop_worker(self) -> None:
        '''
        Iteratively run the next enqueued simulator worker if any *or* cleanup
        after this iteration otherwise (i.e., if no workers remain to be run).

        This method perform the equivalent of the body of the abstract loop
        iteratively starting and running all enqueued simulator workers.
        Specifically, this method iteratively starts the next simulator worker
        (i.e., head item of the :attr:`_workers_queued`) enqueued by a prior call
        to the :meth:`_enqueue_workers` method if this queue is non-empty
        *or* garbage-collects this queue otherwise (i.e., if already empty).

        Design
        ----------
        Ideally, the body of this method would be the body of a simple loop
        over all enqueued simulator workers. Since the
        :meth:`_handle_worker_completion` slot calling this method is only
        iteratively signalled by Qt on the completion of each worker, however,
        "rolling" this method into a loop is effectively infeasible.

        Technically, refactoring this method into a continuation-based
        generator would probably suffice to "roll" this method into a loop.
        Doing so, however, would require the use of an asynchronous
        Python-based event loop *and* a heavyweight architectural redesign. In
        short, the current approach stands as the most reasonable.
        '''

        # If no workers remain to be run, gracefully halt this iteration by
        # silently reducing to a noop.
        if not self.is_worker:
            # Log this halt.
            guithread.log_debug_thread_main(
                'Ceasing simulator worker iteration...')

            # Reduce to a noop.
            return
        # Else, one or more workers remain to be run.

        # Next worker to be run, localized for negligible efficiency.
        worker = self.worker

        # Log this work attempt.
        guithread.log_debug_thread_main('Iterating simulator worker...')

        # Set the state of both this proactor and the currently working phase
        # *BEFORE* successfully starting this worker. See the stop_workers()
        # method for related commentary on this order of logic.
        self._worker_phase_state = worker.simmer_state

        # Finalize this worker's initialization.
        worker.init(
            conf_filename=self._p.conf_filename,
            progress_bar=self._progress_bar,
            progress_label=self._progress_substatus,
            handler_failed=self._handle_worker_exception,
            handler_finished=self._handle_worker_completion,
        )

        # Start this worker *AFTER* establishing all signal-slot connections.
        guipoolthread.start_worker(worker)

    # ..................{ WORKERS ~ slot                    }..................
    # Slots connected to signals emitted by "QRunnable" workers.

    @Slot(Exception)
    def _handle_worker_exception(self, exception: Exception) -> None:
        '''
        Slot signalled on the currently running simulator worker erroneously
        raising an unexpected exception.

        This slot trivially handles this exception by re-raising this
        exception.  Since the only means of explicitly re-raising an exception
        exposed by Python 3.x is to encapsulate that exception inside another
        exception, this slot unconditionally raises a
        :class:`BetseeSimmerBetseException` exception encapsulating the passed
        exception.

        Parameters
        ----------
        exception : Exception
            Exception raised by this worker.

        Raises
        ----------
        BetseeSimmerBetseException
            Unconditionally encapsulates the passed exception.
        '''

        # Log this slot.
        guithread.log_debug_thread_main(
            'Catching simulator worker exception "%s"...',
            objects.get_class_name(exception))

        # If this exception signifies an instability, raise a human-readable
        # translated exception synopsizing this fact. This error is
        # sufficiently common to warrant a special case improving the user
        # experience (UX).
        if isinstance(exception, BetseSimUnstableException):
            raise BetseeSimmerBetseException(
                synopsis=QCoreApplication.translate(
                    'QBetseeSimmerProactor',
                    'Simulation halted prematurely '
                    'due to computational instability.'),
            ) from exception
        # Else, fallback to raising a human-readable translated exception
        # synopsizing an unrecognized fatal error.
        #
        # Note that this case embeds an exegesis (i.e., detailed message) *NOT*
        # embedded in the prior case and hence requires unique handling.
        else:
            raise BetseeSimmerBetseException(
                synopsis=QCoreApplication.translate(
                    'QBetseeSimmerProactor',
                    'Simulation halted prematurely with unexpected error:'),
                exegesis=str(exception),
            ) from exception


    @Slot(bool)
    def _handle_worker_completion(self, is_success: bool) -> None:
        '''
        Handle the completion of the most recently working simulator worker.

        Specifically, this method:

        * Sets the state of the corresponding simulator phase to finished.
        * Pops this worker from the :attr:`_workers_queued`.
        * If this queue is non-empty, starts the next enqueued worker.

        Parameters
        ----------
        is_success : bool
            ``True`` only if this worker completed successfully.
        '''

        # If the most recently working worker is no longer working, silently
        # reduce to a noop. Ideally, a worker would *ALWAYS* be working when
        # this slot is signalled. In practice, edge cases resulting from the
        # non-determinism implicit in multithreaded logic can induce this. For
        # example, the stop_workers() slot dequeueing all workers *BEFORE*
        # calling the QBetseeSimmerPhaseWorker.stop() pseudo-slot signalling
        # this slot reliably induces this case.
        if not self.is_worker:
            # Log this edge case.
            guithread.log_debug_thread_main(
                'Ignoring simulator worker closure...')

            # Reduce to a noop.
            return
        # Else, one or more workers remain to be run.

        # Log this slot.
        guithread.log_debug_thread_main('Handling simulator worker closure...')

        # If this worker is still technically working, set the state of both
        # this simulator *AND* the previously working phase to finished. This
        # ensures that the simulator reliably returns to the finished state on
        # completing all possible work, regardless of whether that worker
        # halted gracefully or prematurely (e.g., due to the user prematurely
        # stopping all work).
        #
        # For safety, do so *BEFORE* this method dequeues this worker and hence
        # internally modifies the worker yielded by the "_worker" property.
        self._worker_phase_state = SimmerState.FINISHED

        # Schedule this worker for immediate deletion. On doing so, all signals
        # owned by this worker will be disconnected from connected slots.
        #
        # In theory, doing so *SHOULD* be unnecessary. The subsequent
        # nullification of the worker owning these signals should already
        # signal this deletion. As doing so has no harmful side effects,
        # however, do so regardless for additional safety.
        self.worker.delete_later()

        # Dequeue this worker (i.e., remove this worker's subclass from
        # the queue of worker subclasses to be instantiated and run).
        self._workers_queued.popleft()

        # Start the next worker in the current queue of workers to be run
        # if any or reduce to a noop otherwise.
        self._loop_worker()
