#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
*and* controlling the execution of simulation phases) functionality.
'''

#FIXME: When the application closure signal is emitted (e.g., from the
#QApplication.aboutToQuit() signal and/or QMainWindow.closeEvent() handler),
#the following logic should be performed (in order):
#
#1. In the QMainWindow.closeEvent() handler only:
#   * When the user attempts to close the application when one or more threads
#     are currently running, a warning dialog should be displayed to the user
#     confirming this action.

#FIXME: When the user attempts to run a dirty simulation (i.e., a simulation
#with unsaved changes), the GUI should prompt the user as to whether or not
#they would like to save those changes *BEFORE* running the simulation. In
#theory, we should be able to reuse existing "sim_conf" functionality to do so.

#FIXME: Note in a more appropriate docstring somewhere that the text overlaid
#onto the progress bar is only conditionally displayed depending on the current
#style associated with this bar. Specifically, the official documentation notes:
#
#    Note that whether or not the text is drawn is dependent on the style.
#    Currently CDE, CleanLooks, Motif, and Plastique draw the text. Mac, Windows
#    and WindowsXP style do not.
#
#For orthogonality with native applications, it's probably best to accept this
#constraint as is and intentionally avoid setting a misson-critical format on
#progress bars. Nonetheless, this *DOES* appear to be circumventable by
#manually overlaying a "QLabel" widget over the "QProgressBar" widget in
#question. For details, see the following StackOverflow answer (which, now that
#I peer closely at it, appears to be quite incorrect... but, something's better
#than nothing... maybe):
#    https://stackoverflow.com/a/28816650/2809027

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, Slot  #, QObject, Signal
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type.text import strs
from betse.util.type.types import type_check
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simtab.run.guisimrunact import QBetseeSimmerProactor
from betsee.gui.simtab.run.guisimrunstate import (
    SimmerState,
    SIM_PHASE_KIND_TO_NAME,
    SIMMER_STATE_TO_PROACTOR_STATUS,
    SIMMER_STATE_TO_PROACTOR_SUBSTATUS,
    SIMMER_STATES_HALTING,
)
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ CLASSES                           }....................
class QBetseeSimmer(QBetseeControllerABC):
    '''
    High-level **simulator** (i.e., :mod:`PySide2`-based object both displaying
    *and* controlling the execution of simulation phases).

    Attributes (Private)
    ----------
    _progress_status_text_prior : str
        Most recent textual contents of the
        :attr:`QBetseeMainWindow.sim_run_player_status` label, preserved so as
        to permit this text to be transparently reused without localization
        concerns (particularly on repeatedly switching between the paused,
        stopped, and finished simulator states).

    Attributes (Private: Controllers)
    ----------
    _proactor : QBetseeSimmerProactor
        **Simulator proactor** (i.e., lower-level :mod:`PySide2`-based
        delegate controlling but *not* displaying the execution of simulation
        phases). In standard model-view-controller (MVC) parlance:

        * BETSE itself is the model (M) that runs simulation phases.
        * This proactor is the controller (C) for running simulation phases.
        * This parent object is the view (V) into running simulation phases.

    Attributes (Private: Widgets)
    ----------
    _action_toggle_work : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_toggle_work`
        action.
    _action_stop_workers : QAction
        Alias of the :attr:`QBetseeMainWindow.action_sim_run_stop_workers`
        action.
    _player_toolbar : QFrame
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_toolbar_frame`
        frame containing only the :class:`QToolBar` controlling this
        simulation.
    _progress_bar : QProgressBar
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_progress` widget.
    _progress_status : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_status` label,
        synopsizing the current state of this simulator.
    _progress_substatus : QLabel
        Alias of the :attr:`QBetseeMainWindow.sim_run_player_substatus` label,
        detailing the current state of this simulator.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this simulator.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Simulator proactor.
        self._proactor = QBetseeSimmerProactor(self)

        # Nullify all remaining instance variables for safety.
        self._action_toggle_work = None
        self._action_stop_workers = None
        self._player_toolbar = None
        self._progress_bar = None
        self._progress_status = None
        self._progress_substatus = None
        self._progress_status_text_prior = None


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
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
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Log this initialization.
        logs.log_debug('Sanitizing simulator state...')

        # Initialize all widgets concerning simulator state.
        self._init_widgets(main_window)

        # Connect all relevant signals and slots *AFTER* initializing these
        # widgets, as the former typically requires the latter.
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (*not* always owned by this object) concerning this
        simulator.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow`
            widget.
        '''

        # Classify variables of this main window required by this simulator.
        self._action_toggle_work  = main_window.action_sim_run_toggle_work
        self._action_stop_workers = main_window.action_sim_run_stop_work
        self._player_toolbar      = main_window.sim_run_player_toolbar_frame
        self._progress_bar        = main_window.sim_run_player_progress
        self._progress_status     = main_window.sim_run_player_status
        self._progress_substatus  = main_window.sim_run_player_substatus
        self._progress_substatus_group = (
            main_window.sim_run_player_substatus_group)


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulator.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow`
            widget.
        '''

        # Connect each such action to this object's corresponding slot.
        self._action_toggle_work.triggered.connect(
            self._proactor.toggle_work)
        self._action_stop_workers.triggered.connect(
            self._proactor.stop_workers)

        # Update simulator widgets to reflect each change in proactor state.
        self._proactor.set_state_signal.connect(self._update_widgets)

        # Initialize the proactor *AFTER* establishing the prior signal-slot
        # connection, as the QBetseeSimmerProactor.init() method called here
        # internally changes the proactor state and hence requires that
        # simulator widgets be updated.
        self._proactor.init(
            main_window=main_window,
            progress_bar=self._progress_bar,
            progress_status=self._progress_status,
            progress_substatus=self._progress_substatus,
        )

    # ..................{ FINALIZERS                        }..................
    def halt_work(self) -> None:
        '''
        Schedule the currently running simulation phase if any for immediate
        and thus possibly non-graceful termination *or* silently reduce to a
        noop otherwise (i.e., if no simulation phase is currently running).

        Caveats
        ----------
        This method may induce data loss or corruption in simulation output.
        In theory, this should only occur in edge cases in which the current
        simulator worker fails to gracefully stop within a sensible window of
        time. In practice, this implies that this method should *only* be
        called when otherwise unavoidable (e.g., at application shutdown).

        See Also
        ----------
        :meth:`QBetseeSimmerProactor.halt_workers`
            Further details.
        '''

        # Transparently forward this request to our proactor.
        self._proactor.halt_workers()

    # ..................{ SLOTS ~ update                    }..................
    @Slot()
    def _update_widgets(self) -> None:
        '''
        Update the contents of widgets owned or controlled by this simulator to
        reflect the current state of this simulator.
        '''

        # Log this update.
        logs.log_debug('Updating simulator widgets from simulator state...')

        # Enable (in arbitrary order):
        #
        # * All widgets controlling the currently queued phase only if one or
        #   more phases are currently queued.
        # * All widgets halting the current worker only if some worker is
        #   currently working.
        #
        # To reduce the likelihood of accidental interaction with widgets
        # intended to be disabled, do so *BEFORE* subsequent slot logic.
        self._player_toolbar.setEnabled(self._proactor.is_queued)

        # Enable simulator starting, pausing, and resuming only if the
        # simulator is currently workable.
        self._action_toggle_work.setEnabled(self._proactor.is_workable)

        # Enable simulator pausing only if the simulator is currently running.
        self._action_toggle_work.setChecked(self._proactor.is_running)

        # Enable simulator stopping only if the simulator is currently working.
        # Note that:
        #
        # * Testing the "_is_running" property fails to suffice, as that
        #   property fails to yield "True" when the simulator is paused.
        # * While testing the "_is_worker" property alone could also
        #   theoretically suffice, doing so would desynchronize the UI from
        #   this simulator state; specifically, the button associated with this
        #   action would remain enabled for a non-deterministic window of time
        #   after the simulator is stopped. Why? Because the _stop_workers()
        #   slot sets this simulator state to stopped *BEFORE* the currently
        #   working worker successfully stops resulting in the "_is_worker"
        #   property yielding "False". Ergo, the simulator state takes
        #   precedence for UI purposes.
        self._action_stop_workers.setEnabled(self._proactor.is_working)

        # Update the status of this simulator.
        self._update_progress_status()
        self._update_progress_substatus()


    def _update_progress_status(self) -> None:
        '''
        Update the text displayed by the :attr:`_progress_status` label,
        synopsizing the current state of this simulator.
        '''

        # Unformatted template synopsizing the current state of this simulator.
        status_text_template = SIMMER_STATE_TO_PROACTOR_STATUS[
            self._proactor.state]

        # Text synopsizing the type of simulation phase run by the current
        # simulator worker if any *OR* an arbitrary placeholder otherwise. In
        # the latter case, this text is guaranteed to *NOT* be interpolated by
        # this template and is thus safely ignorable.
        phase_type_name = (
            SIM_PHASE_KIND_TO_NAME[self._proactor.worker.phase.kind]
            if self._proactor.is_worker else
            'the nameless that shall not be named')

        # If no prior progress status exists, this is the first call to this
        # method. In this case, the current state of the proactor is guaranteed
        # to either be the queued or unqueued states; in either case, the
        # progress status template under this state ignores the prior progress
        # status. This implies that this status could technically be
        # initialized to any string with no ill consequences. For simplicity,
        # default this status to the current progress status.
        if self._progress_status_text_prior is None:
            self._progress_status_text_prior = self._progress_status.text()

        # Unconditionally format this text with all possible format specifiers
        # expected by all possible instances of this text. (Note that Python
        # ignores format specifiers *NOT* expected by this exact text.)
        status_text = status_text_template.format(
            phase_type=phase_type_name,
            status_prior=self._progress_status_text_prior,
        )

        # If the proactor is *NOT* currently in a halting state (i.e., is
        # either running, queued, or unqueued)...
        if self._proactor.state not in SIMMER_STATES_HALTING:
            # Preserve this progress status for subsequent use when halting.
            self._progress_status_text_prior = status_text

            # Enable this text to be interpolated into arbitrary character
            # positions by (in arbitrary order):
            #
            # * Lowercasing the first character of this text.
            # * Stripping the trailing ellipses from this text if present.
            self._progress_status_text_prior = (
                strs.lowercase_char_first(
                    strs.remove_suffix_if_found(
                        text=self._progress_status_text_prior, suffix='...')))
        # Else, the proactor is currently in a halting state (i.e., is either
        # paused, stopped, or finished). In this case, preserve the prior
        # progress status for subsequent reuse when switching between halting
        # states. If this edge case were *NOT* explicitly detected here, then
        # switching from the stopped to finished states would, for example,
        # result in progress status resembling "Finished stopped modelling...".

        # Set the text of the label displaying this synopsis to this text.
        self._progress_status.setText(status_text)


    def _update_progress_substatus(self) -> None:
        '''
        Update the text displayed by the :attr:`_progress_substatus` label,
        detailing the current state of this simulator.
        '''

        # Arbitrary object detailing the current state of this simulator, whose
        # type is specific to this state.
        substatus_value = SIMMER_STATE_TO_PROACTOR_SUBSTATUS[
            self._proactor.state]

        # Unformatted template detailing the current state of this simulator,
        # conditionally defined below in a state-dependent manner.
        substatus_text_template = None

        # If the proactor is currently modelling...
        if self._proactor.state is SimmerState.MODELLING:
            # Type of simulaton phase currently being modelled.
            phase_kind = self._proactor.worker.phase.kind

            # If the proactor is currently modelling the seed phase, silently
            # reduce to a noop. Details of modelling the seed phase are already
            # displayed by the slot connected to the signal emitted by the
            # SimCallbacksSignaller.progress_stated() of the current simulator
            # worker in a push-driven manner.
            if phase_kind is SimPhaseKind.SEED:
                return

            # Else, the proactor is currently modelling either the
            # initialization or simulation phases. In either case, the details
            # of the proactor's current action reduce to the value of this
            # nested dictionary whose key is this phase.
            substatus_text_template = substatus_value[phase_kind]
        #FIXME: Implement this case... somehow. See pertinent FIXME comments in
        #the "guisimrunstate" submodule.
        # Else if the proactor is currently exporting...
        elif self._proactor.state is SimmerState.EXPORTING:
            substatus_text_template = (
                "Exported the ancient demesne of lost R'lyeh.")
        # Else, the proactor is neither modelling nor exporting. In this case,
        # the details of the proactor's current action reduce to a string.
        else:
            substatus_text_template = substatus_value

        # Text detailing the prior state of this simulator.
        substatus_text_prior = self._progress_substatus.text()

        # Metadata synopsizing the current state of this simulator.
        proactor_metadata = self._proactor.get_metadata()

        #FIXME: Interpolate the actual progress values expected by this
        #template. Doing so will be non-trivial, albeit mostly from a design
        #perspective. In particular, we'll need to improve the pooled thread
        #worker API to permit both the current state of numeric progress *AND*
        #the full range of numeric progress to be safely queryable in a
        #thread-safe manner by callers. *le_sigh*

        # Unconditionally format this text with all possible format specifiers
        # expected by all possible instances of this text. (Note that Python
        # ignores format specifiers *NOT* expected by this exact text.)
        substatus_text = substatus_text_template.format(
            progress_current=0,
            progress_total=100,
            queued_modelling=proactor_metadata.phases_queued_modelling_count,
            queued_exporting=proactor_metadata.phases_queued_exporting_count,
            substatus_prior=substatus_text_prior,
        )

        # Set the text of the label displaying these details to this text.
        self._progress_substatus.setText(substatus_text)
