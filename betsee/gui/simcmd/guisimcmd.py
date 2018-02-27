#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation phase and subcommand (e.g.,
``betse sim``, ``betse plot init``) state.
'''

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
#progress bars. Nonetheless, this *DOES* appear to be circumventable by manually
#overlaying a "QLabel" widget over the "QProgressBar" widget in question. For
#details, see the following StackOverflow answer (which, now that I peer closely
#at it, appears to be quite incorrect... but, something's better than nothing):
#    https://stackoverflow.com/a/28816650/2809027

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.io.log import logs
from betse.util.type.enums import make_enum
from betse.util.type.types import type_check  #, StrOrNoneTypes
# from betsee.guiexception import BetseeSimConfException
from betsee.gui.window.guimainwindow import QBetseeMainWindow

# ....................{ ENUMS                              }....................
SimCmdState = make_enum(
    class_name='SimCmdState',
    member_names=(
        'UNQUEUED',
        'QUEUED',
        'MODELLING',
        'EXPORTING',
        'PAUSED',
        'HALTED',
        'DONE',
    ))
'''
Enumeration of all supported types of **simulator state** (i.e., mutually
exclusive combination of one or more booleans uniquely capturing the condition
of the currently queued simulation subcommand if any, analogous to a state in a
finite state automata).

Attributes
----------
UNQUEUED : enum
    Unqueued state, implying no subcommands to be queued.
QUEUED : enum
    Queued state, implying one or more subcommands to be queued but *not* yet
    run and hence neither paused, halted, nor done.
MODELLING : enum
    Modelling state, implying one or more queued subcommands specific to
    modelling (e.g., seed, initialization) to be currently running and hence
    neither paused, halted, nor done.
EXPORTING : enum
    Exporting state, implying one or more queued subcommands specific to
    exporting (e.g., seed exports, initialization exports) to be currently
    running and hence neither paused, halted, nor done.
PAUSED : enum
    Paused state, implying one or more queued subcommands to have been run but
    paused before completion.
HALTED : enum
    Halted state, implying one or more queued subcommands to have been run but
    halted before completion.
DONE : enum
    Completion state, implying all queued subcommands to have been run to
    completion.
'''

# ....................{ GLOBALS ~ dict                     }....................
_SIM_CMD_STATE_TO_STATUS = {
    SimCmdState.UNQUEUED: QCoreApplication.translate(
        'guisimcmd', 'Waiting for phase(s) to be queued...'),
    SimCmdState.QUEUED: QCoreApplication.translate(
        'guisimcmd', 'Waiting for queued phase(s) to be modelled...'),
    SimCmdState.MODELLING: QCoreApplication.translate(
        'guisimcmd',
        'Modelling <b>{phase_type}</b> '
        'step {step_curr} '
          '<i>of</i> {step_total}:'),
    SimCmdState.EXPORTING: QCoreApplication.translate(
        'guisimcmd',
        'Exporting <b>{phase_type}</b> '
        '{export_type} <pre>"{export_name}"</pre> '
        'step {step_curr} '
          '<i>of</i> {step_total}:'),
    SimCmdState.PAUSED: QCoreApplication.translate(
        'guisimcmd', 'Paused {cmd_prior}'),
    SimCmdState.HALTED: QCoreApplication.translate(
        'guisimcmd', 'Stopped {cmd_prior}'),
    SimCmdState.DONE: QCoreApplication.translate(
        'guisimcmd', 'Finished {cmd_prior}'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated, unformatted string templating a high-level synopsis of the action
being performed in that state.

Most such strings contain *no* format specifiers and are thus displayable as is.
Some such strings contain one or more format specifiers (e.g., ``{cmd_name}}`)
and are thus displayable *only* after interpolating the corresponding values.
'''


_MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS = {
    # Note that low-level details for the "SimPhaseKind.SEED" phase are specific
    # to the current action being performed and hence defined in the lower-level
    # BETSE codebase rather than here.

    SimPhaseKind.INIT: QCoreApplication.translate(
        'guisimcmd', 'Initializing {time_curr} <i>of</i> {time_total}...'),
    SimPhaseKind.SIM: QCoreApplication.translate(
        'guisimcmd', 'Simulating {time_curr} <i>of</i> {time_total}...'),
}
'''
Dictionary mapping from the initialization and simulation phases to a
human-readable, translated, unformatted string templating the low-level details
of the action being performed when modelling that phase.
'''


#FIXME: Create the "SimExportKind" enumeration with the members referenced
#below, presumably in a new "betse.science.export.expenum" submodule.

# _EXPORTING_KIND_TO_STATUS_DETAILS = {
#     SimExportKind.CSV: QCoreApplication.translate(
#         'guisimcmd',
#         'Exporting comma-separated value (CSV) file '
#         '<pre>"{filename}"</pre>...'),
#     SimExportKind.PLOT: QCoreApplication.translate(
#         'guisimcmd', 'Exporting image <pre>"{filename}"</pre>...'),
#     SimExportKind.ANIM: QCoreApplication.translate(
#         'guisimcmd',
#         'Exporting animation <pre>"{filename}"</pre> frame '
#         '{time_curr} <i>of</i> {time_total}...'),
# }
# '''
# Dictionary mapping from the initialization and simulation phases to a
# human-readable, translated, unformatted string templating the low-level details
# of the action being performed when modelling that phase.
# '''

# ....................{ CLASSES                            }....................
class QBetseeSimCmd(QObject):
    '''
    :mod:`PySide2`-based object encapsulating all high-level simulation
    phase and subcommand (e.g., ``betse sim``, ``betse plot init``) state.

    This state includes:

    * A queue of all simulation subcommands to be interactively run.
    * Whether or not a simulation subcommand is currently being run.
    * The state of the currently run simulation subcommand (if any), including:
      * Visualization (typically, Vmem animation) of the most recent step
        completed for this subcommand.
      * Textual status describing this step in human-readable language.
      * Numeric progress as a relative function of the total number of steps
        required by this subcommand.

    Attributes (Public)
    ----------

    Attributes (Private: Non-widgets)
    ----------

    Attributes (Private: Widgets)
    ----------
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, main_window: QBetseeMainWindow, *args, **kwargs) -> None:
        '''
        Initialize this object, owned by the passed main window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulation subcommander.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child widgets
        (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Log this initialization.
        logs.log_debug('Sanitizing simulation subcommand state...')

        # Nullify all stateful instance variables for safety. While the signals
        # subsequently emitted by this method also do so, ensure sanity if these
        # variables are tested in the interim.
        # self._is_dirty = False

        # Classify all instance variables of this main window subsequently
        # required by this object. Since this main window owns this object,
        # since weak references are unsafe in a multi-threaded GUI context, and
        # since circular references are bad, this object intentionally does
        # *NOT* retain a reference to this main window.
        # self._action_make_sim     = main_window.action_make_sim

        # Initialize all widgets concerning simulation subcommand state the
        # *BEFORE* connecting all relevant signals and slots typically expecting
        # these widgets to be initialized.
        self._init_widgets(main_window)
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (not necessarily owned by this object) whose internal
        state pertains to the high-level state of simulation subcommands.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Avoid circular import dependencies.
        # from betsee.gui.simconf.guisimconfundo import (
        #     QBetseeUndoStackSimConf)

        # Undo stack for this simulation configuration.
        # self.undo_stack = QBetseeUndoStackSimConf(
        #     main_window=main_window, sim_config=self)

        #FIXME: Conditionally enable this group of widgets as described here.

        # Enable all widgets controlling the state of the currently queued
        # subcommand only if one or more subcommands are currently queued.
        # main_window.sim_cmd_run_state.setEnabled(False)

        # main_window.sim_cmd_run_state_text.setText(QCoreApplication.translate(
        #     'QBetseeSimCmd', 'Simulation opened.'))


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of simulation subcommands.
        '''

        # Connect each such action to this object's corresponding slot.
        # self._action_make_sim.triggered.connect(self._make_sim)

        # Connect this object's signals to all corresponding slots.
        # self.set_filename_signal.connect(self.set_filename)

        # Set the state of all widgets dependent upon this simulation
        # subcommand state *AFTER* connecting all relavant signals and slots.
        # Initially, no simulation subcommands have yet to be queued or run.
        #
        # Note that, as this slot only accepts strings, the empty string rather
        # than "None" is intentionally passed for safety.
        # self.set_filename_signal.emit('')

        pass

    # ..................{ PROPERTIES ~ bool                  }..................
    # @property
    # def is_open(self) -> bool:
    #     '''
    #     ``True`` only if a simulation configuration file is currently open.
    #     '''
    #
    #     return self.p.is_loaded

    # ..................{ PROPERTIES ~ str                   }..................
    # @property
    # def dirname(self) -> StrOrNoneTypes:
    #     '''
    #     Absolute path of the directory containing the currently open
    #     simulation configuration file if any *or* ``None`` otherwise.
    #     '''
    #
    #     return self.p.conf_dirname

    # ..................{ EXCEPTIONS                         }..................
    # def die_unless_open(self) -> bool:
    #     '''
    #     Raise an exception unless a simulation configuration file is currently
    #     open.
    #     '''
    #
    #     if not self.is_open:
    #         raise BetseeSimConfException(
    #             'No simulation configuration currently open.')

    # ..................{ SIGNALS                            }..................
    # set_filename_signal = Signal(str)
    # '''
    # Signal passed either the absolute path of the currently open YAML-formatted
    # simulation configuration file if any *or* the empty string otherwise.
    #
    # This signal is typically emitted on the user:
    #
    # * Opening a new simulation configuration.
    # * Closing a currently open simulation configuration.
    # '''

    # ..................{ SLOTS ~ state                      }..................
    # @Slot(str)
    # def set_filename(self, filename: str) -> None:
    #     '''
    #     Slot signalled on both the opening of a new simulation configuration
    #     and closing of an open simulation configuration.
    #
    #     Parameters
    #     ----------
    #     filename : StrOrNoneTypes
    #         Absolute path of the currently open YAML-formatted simulation
    #         configuration file if any *or* the empty string otherwise (i.e., if
    #         no such file is open).
    #     '''
    #
    #     # Notify all interested slots that no unsaved changes remain, regardless
    #     # of whether a simulation configuration has just been opened or closed.
    #     self.set_dirty_signal.emit(False)

    # ..................{ SLOTS ~ action                     }..................
    # @Slot()
    # def _open_sim(self) -> None:
    #     '''
    #     Slot invoked on the user requesting that the currently open simulation
    #     configuration if any be closed and an existing external simulation
    #     configuration be opened.
    #     '''
    #
    #     # Absolute path of an existing YAML-formatted simulation configuration
    #     # file selected by the user.
    #     conf_filename = self._show_dialog_sim_conf_open()
    #
    #     # If the user canceled this dialog, silently noop.
    #     if conf_filename is None:
    #         return
    #     # Else, the user did *NOT* cancel this dialog.
    #
    #     # Close the currently open simulation configuration if any.
    #     self._close_sim()
    #
    #     # Deserialize this low-level file into a high-level configuration.
    #     self.load(conf_filename)
    #
    #     # Update the status bar *AFTER* successfully completing this action.
    #     self._status_bar.showMessage(QCoreApplication.translate(
    #         'QBetseeSimConf', 'Simulation opened.'))
