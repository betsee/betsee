#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **simulation configurator** (i.e., :mod:`PySide2`-based object
both displaying *and* modifying external YAML-formatted simulation configuration
files) functionality.
'''

#FIXME: Either this or a subordinate "QObject" should routinely detect
#simulation configuration desynchronization (i.e., external changes to the
#on-disk YAML file underlying the currently open simulation configuration if
#any) and interactively query the current user to eith:r
#
#* Discard all in-GUI changes to this configuration and reload this
#  configuration from disk.
#* Preserve all in-GUI changes to this configuration by ignoring these external
#  changes, thus overwriting these changes on the next save.
#
#To do so, we'll need to track the current mtime of this file with a
#"QFileSystemWatcher" instance as follows:
#
#* Define a new resync_file() slot of this class accepting a single "str"
#  argument: the absolute filename of the watched file that was modified. In
#  this case, that will be the top-level YAML file. Naturally, this slot will
#  perform the bulk of the logic pertaining to resynchronization. Note that
#  we'll need to explicitly test whether this file still exists or not in this
#  slot, as it may have been moved away or removed entirely.
#* In the __init__() and/or init() methods of this class:
#  * Create a new "_path_watcher" variable of type "QFileSystemWatcher".
#  * Connect the fileChanged() signal of this variable.
#* In the set_filename() slot:
#  * When a new simulation configuration is opened (i.e., "filename" is
#    non-empty), call the "self._path_watcher.addPath(filename)" method.
#  * When an open simulation configuration is closed (i.e., "filename" is
#    empty), call the "self._path_watcher.removePath(filename)" method.
#
#Note also that files can be moved and removed from disk. If the
#on-disk YAML file underlying the currently open simulation configuration no
#longer exists at any point (e.g., due to being externally removed), what is the
#sanest response? Should we simply ignore this case? Doing so will simply
#silently rewrite this file to disk on the next save, which seems reasonably
#sane. In other words, the noop-based lazy approach may be the correct approach.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal, Slot
from PySide2.QtWidgets import QMessageBox
from betse.science.config import confio
from betse.science.parameters import Parameters
from betse.util.io.log import logs
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.guiexception import BetseeSimConfException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.util.app import guiappstatus
from betsee.util.io import guimessage
from betsee.util.path import guifile
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ CLASSES                            }....................
class QBetseeSimConf(QBetseeControllerABC):
    '''
    High-level **simulation configurator** (i.e., :mod:`PySide2`-based object
    both displaying *and* modifying external YAML-formatted simulation
    configuration files).

    This configurator maintains all state required to manage these files,
    including:

    * Whether or not a simulation configuration is currently open.
    * Whether or not an open simulation configuration has unsaved changes.

    Attributes (Public)
    ----------
    p : Parameters
        High-level simulation configuration encapsulating a low-level dictionary
        parsed from an even lower-level YAML-formatted file.
    undo_stack : QBetseeUndoStackSimConf
        Undo stack for the currently open simulation configuration if any *or*
        the empty undo stack otherwise.

    Attributes (Private: Non-widgets)
    ----------
    _is_dirty : bool
        ``True`` only if a simulation configuration is currently open *and* this
        configuration is **dirty** (i.e., has unsaved changes).

    Attributes (Private: Widgets)
    ----------
    _action_make_sim : QAction
        Alias of the :attr:`QBetseeMainWindow.action_make_sim` action.
    _action_open_sim : QAction
        Alias of the :attr:`QBetseeMainWindow.action_open_sim` action.
    _action_close_sim : QAction
        Alias of the :attr:`QBetseeMainWindow.action_close_sim` action.
    _action_save_sim : QAction
        Alias of the :attr:`QBetseeMainWindow.action_save_sim` action.
    _action_save_sim_as : QAction
        Alias of the :attr:`QBetseeMainWindow.action_save_sim_as` action.
    _sim_conf_changed_signal : QSignal
        Alias of the :attr:`QBetseeMainWindow.sim_conf_changed_signal` signal.
    _sim_conf_stack : QBetseeSimConfStackedWidget
        Alias of the :attr:`QBetseeMainWindow.sim_conf_stack` widget.
    _sim_conf_tree : QBetseeSimConfTreeWidget
        Alias of the :attr:`QBetseeMainWindow.sim_conf_tree` widget.
    _sim_conf_tree_frame : QFrame
        Alias of the :attr:`QBetseeMainWindow.sim_conf_tree_frame` widget.
    _sim_tab : QBetseeSimmerTabWidget
        Alias of the :attr:`QBetseeMainWindow.sim_tab` widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this configurator.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._is_dirty = False
        self._action_make_sim = None
        self._action_open_sim = None
        self._action_close_sim = None
        self._action_save_sim = None
        self._action_save_sim_as = None
        self._sim_conf_stack = None
        self._sim_conf_tree = None
        self._sim_conf_tree_frame = None
        self._sim_tab = None
        self.undo_stack = None

        # High-level simulation configuration, defaulting to the unload state.
        self.p = Parameters()


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Finalize this configurator's initialization, owned by the passed main
        window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of this simulation configuration.

        Specifically:

        * When any such widget's content (e.g., editable text, selectable item)
          is modified, widgets elsewhere are notified of this simulation
          configuration modification via the
          :attr:`set_dirty_signal` signal.

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
        super().init(main_window)

        # Log this initialization.
        logs.log_debug('Sanitizing simulation configuration state...')

        # Initialize all widgets pertaining to the state of this simulation
        # configuration *BEFORE* connecting all relevant signals and slots
        # typically expecting these widgets to be initialized.
        self._init_widgets(main_window)
        self._init_connections(main_window)


    @type_check
    def _init_widgets(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all widgets owned directly by this object *and* initialize all
        other widgets (not necessarily owned by this object) whose internal
        state pertains to the high-level state of this simulation configuration.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Avoid circular import dependencies.
        from betsee.gui.simconf.guisimconfundo import (
            QBetseeUndoStackSimConf)

        # Classify all instance variables of this main window subsequently
        # required by this object. Since this main window owns this object,
        # since weak references are unsafe in a multi-threaded GUI context, and
        # since circular references are bad, this object intentionally does
        # *NOT* retain a reference to this main window.
        self._action_make_sim     = main_window.action_make_sim
        self._action_open_sim     = main_window.action_open_sim
        self._action_close_sim    = main_window.action_close_sim
        self._action_save_sim     = main_window.action_save_sim
        self._action_save_sim_as  = main_window.action_save_sim_as
        self._sim_conf_stack      = main_window.sim_conf_stack
        self._sim_conf_tree       = main_window.sim_conf_tree
        self._sim_conf_tree_frame = main_window.sim_conf_tree_frame
        self._sim_tab             = main_window.sim_tab

        # Undo stack for this simulation configuration.
        self.undo_stack = QBetseeUndoStackSimConf(
            main_window=main_window, sim_config=self)


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulation configuration.
        '''

        # Connect each such action to this object's corresponding slot.
        self._action_make_sim.triggered.connect(self._make_sim)
        self._action_open_sim.triggered.connect(self._open_sim)
        self._action_close_sim.triggered.connect(self._close_sim)
        self._action_save_sim.triggered.connect(self._save_sim)
        self._action_save_sim_as.triggered.connect(self._save_sim_as)

        # Connect this object's signals to all corresponding slots of *ALL*
        # objects across the codebase (including this object).
        #
        # Ideally, those objects would themselves (e.g., in their own init()
        # methods) connect these signals to these slots. In practice, subsequent
        # logic emits these signals and hence requires that these connections be
        # deterministically established *BEFORE* these signals are emitted.
        self.set_filename_signal.connect(main_window.set_sim_conf_filename)

        #FIXME: Uncomment this *AFTER* defining the slot connected to here.
        # self.set_filename_signal.connect(main_window.sim_cmd.set_sim_conf_filename)
        self.set_filename_signal.connect(self.set_filename)
        self.set_dirty_signal.connect(main_window.set_sim_conf_dirty)
        self.set_dirty_signal.connect(self.set_dirty)

        # Set the state of all widgets dependent upon this simulation
        # configuration state *AFTER* connecting all relavant signals and slots.
        # Initially, no simulation configuration has yet to be opened.
        #
        # Note that, as this slot only accepts strings, the empty string rather
        # than "None" is intentionally passed for safety.
        self.set_filename_signal.emit('')

    # ..................{ PROPERTIES ~ bool                  }..................
    @property
    def is_open(self) -> bool:
        '''
        ``True`` only if a simulation configuration file is currently open.
        '''

        return self.p.is_loaded

    # ..................{ PROPERTIES ~ str                   }..................
    @property
    def dirname(self) -> StrOrNoneTypes:
        '''
        Absolute path of the directory containing the currently open
        simulation configuration file if any *or* ``None`` otherwise.
        '''

        return self.p.conf_dirname


    @property
    def filename(self) -> StrOrNoneTypes:
        '''
        Absolute path of the currently open simulation configuration file if any
        *or* ``None`` otherwise.
        '''

        return self.p.conf_filename

    # ..................{ EXCEPTIONS                         }..................
    def die_unless_open(self) -> bool:
        '''
        Raise an exception unless a simulation configuration file is currently
        open.
        '''

        if not self.is_open:
            raise BetseeSimConfException(
                'No simulation configuration currently open.')

    # ..................{ SIGNALS                            }..................
    set_filename_signal = Signal(str)
    '''
    Signal passed either the absolute path of the currently open YAML-formatted
    simulation configuration file if any *or* the empty string otherwise.

    This signal is typically emitted on the user:

    * Opening a new simulation configuration.
    * Closing a currently open simulation configuration.
    '''


    set_dirty_signal = Signal(bool)
    '''
    Signal passed a single boolean on the currently open simulation
    configuration associated with the main window either receiving new unsaved
    changes (in which case this boolean is ``True``) *or* having just been saved
    (in which case this boolean is ``False``).

    This signal is typically emitted on each user edit of the contents of any
    widget owned by the top-level simulation configuration tree or stack
    widgets, implying a modification to this simulation configuration.
    '''

    # ..................{ SLOTS ~ state                      }..................
    @Slot(str)
    def set_filename(self, filename: str) -> None:
        '''
        Slot signalled on both the opening of a new simulation configuration
        and closing of an open simulation configuration.

        Parameters
        ----------
        filename : StrOrNoneTypes
            Absolute path of the currently open YAML-formatted simulation
            configuration file if any *or* the empty string otherwise (i.e., if
            no such file is open).
        '''

        # Notify all interested slots that no unsaved changes remain, regardless
        # of whether a simulation configuration has just been opened or closed.
        self.set_dirty_signal.emit(False)


    @Slot(bool)
    def set_dirty(self, is_dirty: bool) -> None:
        '''
        Slot signalled on each change of the **dirty state** (i.e., existence of
        unsaved in-memory changes) of the currently open simulation
        configuration if any.

        This slot internally updates the state (e.g., enabled or disabled,
        displayed or hidden) of all widgets owned or otherwise associated with
        this object.

        Parameters
        ----------
        is_dirty : bool
            ``True`` only if a simulation configuration is currently open *and*
            this configuration is **dirty** (i.e., has unsaved changes).
        '''

        # Classify this parameter.
        self._is_dirty = is_dirty

        # Enable or disable actions requiring an open simulation configuration.
        self._action_close_sim  .setEnabled(self.p.is_loaded)
        self._action_save_sim_as.setEnabled(self.p.is_loaded)

        # Enable or disable actions requiring an open simulation configuration
        # associated with an existing file and having unsaved changes.
        self._action_save_sim.setEnabled(self.p.is_loaded and is_dirty)

        # Show or hide widgets requiring an open simulation configuration.
        self._sim_conf_stack     .setEnabled(self.p.is_loaded)
        self._sim_conf_tree_frame.setEnabled(self.p.is_loaded)
        self._sim_tab            .setEnabled(self.p.is_loaded)

        # If no simulation configuration is open, clear the undo stack.
        if not self.p.is_loaded:
            self.undo_stack.clear()

    # ..................{ SLOTS ~ action                     }..................
    @Slot()
    def _make_sim(self) -> None:
        '''
        Slot invoked on the user requesting that the currently open simulation
        configuration if any be closed and a new simulation configuration with
        default settings be both created and opened.
        '''

        # Absolute path of a possibly non-existing YAML-formatted simulation
        # configuration file selected by the user.
        conf_filename = self._show_dialog_sim_conf_save()

        # If the user canceled this dialog, silently noop.
        if conf_filename is None:
            return
        # Else, the user did *NOT* cancel this dialog.

        # Close the currently open simulation configuration if any.
        self._close_sim()

        # Write the default simulation configuration to this file.
        confio.write_default(
            conf_filename=conf_filename,

            # Silently (over)write this file if this file already exists. Since
            # the guifile.select_file_save() function has already interactively
            # confirmed this overwrite in this case, doing so is safe to the
            # extent that the user has already accepted the consequences.
            is_conf_overwritable=True,

            # Preserve all external resources required by
            # this file with those contained in this default simulation
            # configuration. Since the guifile.select_file_save() function has
            # already interactively confirmed this overwrite when this file already
            # exists, doing so is safe to the extent that the user has accepted the
            # painful consequences.
        )

        # Deserialize this low-level file into a high-level configuration.
        self.load(conf_filename)

        # Update the status bar *AFTER* successfully completing this action.
        guiappstatus.show_status(QCoreApplication.translate(
            'QBetseeSimConf', 'Simulation created.'))


    @Slot()
    def _open_sim(self) -> None:
        '''
        Slot invoked on the user requesting that the currently open simulation
        configuration if any be closed and an existing external simulation
        configuration be opened.
        '''

        # Absolute path of an existing YAML-formatted simulation configuration
        # file selected by the user.
        conf_filename = self._show_dialog_sim_conf_open()

        # If the user canceled this dialog, silently noop.
        if conf_filename is None:
            return
        # Else, the user did *NOT* cancel this dialog.

        # Close the currently open simulation configuration if any.
        self._close_sim()

        # Deserialize this low-level file into a high-level configuration.
        self.load(conf_filename)

        # Update the status bar *AFTER* successfully completing this action.
        guiappstatus.show_status(QCoreApplication.translate(
            'QBetseeSimConf', 'Simulation opened.'))


    @Slot()
    def _close_sim(self) -> None:
        '''
        Slot invoked on the user attempting to close the currently open
        simulation configuration.

        If this configuration is dirty (i.e., has unsaved changes), the user
        will be interactively prompted to save this changes *before* this
        configuration is closed and these changes irrevocably lost.
        '''

        # If the user failed to interactively confirm saving all unsaved changes
        # if any for the currently open simulation configuration if any, noop.
        if not self.save_if_dirty():
            return
        # Else, these change have all been saved.

        # Revert this configuration to the unloaded state.
        self.p.unload()

        # Notify all interested slots of this event.
        self.set_filename_signal.emit('')

        # Update the status bar *AFTER* successfully completing this action.
        guiappstatus.show_status(QCoreApplication.translate(
            'QBetseeSimConf', 'Simulation closed.'))


    @Slot()
    def _save_sim(self) -> None:
        '''
        Slot invoked on the user requesting all unsaved changes to the currently
        open simulation configuration be written to the external YAML-formatted
        file underlying this configuration, overwriting the contents of this
        file.
        '''

        # Reserialize this configuration back to the same file.
        self.p.save_inplace()

        # Notify all interested slots of this event.
        self.set_dirty_signal.emit(False)

        # Update the status bar *AFTER* successfully completing this action.
        guiappstatus.show_status(QCoreApplication.translate(
            'QBetseeSimConf', 'Simulation saved.'))


    @Slot()
    def _save_sim_as(self) -> None:
        '''
        Slot invoked on the user requesting the currently open simulation
        configuration be written to an arbitrary external YAML-formatted file.
        '''

        # Absolute path of a possibly non-existing YAML-formatted simulation
        # configuration file selected by the user.
        conf_filename = self._show_dialog_sim_conf_save()

        # If the user canceled this dialog, silently noop.
        if conf_filename is None:
            return
        # Else, the user did *NOT* cancel this dialog.

        # Reserialize this configuration into this new file.
        self.p.save(conf_filename)

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(conf_filename)

        # Update the status bar *AFTER* successfully completing this action.
        guiappstatus.show_status(QCoreApplication.translate(
            'QBetseeSimConf', 'Simulation saved.'))

    # ..................{ LOADERS                            }..................
    @type_check
    def load(self, conf_filename: str) -> None:
        '''
        Deserialize the passed low-level YAML-formatted simulation configuration
        file into a high-level :class:`Parameters` object *and* signal all
        connected slots of this event.

        Design
        ----------
        Although low-level, this method is publicly accessible to permit the
        :class:`QBetseeMainWindow` class to handle the equally low-level
        ``--sim-conf-number`` command-line option.

        Note that, to avoid conflicts and confusion with ``open`` methods
        declared throughout the Qt API (e.g., :meth:`QDialog.open`,
        :meth:`QFile.open`), this method is intentionally *not* named ``open``.

        Parameters
        ----------
        conf_filename : str
            Absolute path of this file.
        '''

        # Deserialize this low-level file into a high-level configuration.
        self.p.load(conf_filename)

        # Signal all interested slots of this event.
        self.set_filename_signal.emit(conf_filename)

        # Focus the top-level tree widget *AFTER* signaling and hence populating
        # this tree widget to reflect the state of this configuration.
        self._sim_conf_tree.setFocus()

    # ..................{ SAVERS                             }..................
    def save_if_dirty(self) -> bool:
        '''
        Write all unsaved changes for the currently open simulation
        configuration to the external YAML-formatted file underlying this
        configuration if such a configuration is open, if this configuration is
        dirty (i.e., has unsaved changes), and if the user interactively
        confirms the overwriting of the existing contents of this file.

        Design
        ----------
        Although low-level, this method is publicly accessible to permit the
        :class:`QBetseeMainWindow` class to handle unsaved changes on window
        closure events.

        This method should typically be called immediately *before* the
        currently open simulation configuration (if any) is closed, preventing
        unsaved changes from being irrevocably lost.

        Returns
        ----------
        bool
            Either:
            * ``False`` only if a configuration is open, this configuration is
              dirty, and the user cancels the dialog prompting for confirmation.
              In this case, the caller should ideally abort the current
              operation (e.g., closure of either the current window or
              simulation configuration).
            * ``True`` in *all* other cases.
        '''

        # If this configuration is *NOT* dirty (i.e., has unsaved changes),
        # report success as no changes remain to be saved.
        if not self._is_dirty:
            return True
        # Else, this configuration is dirty.

        # Interactively prompt the user to save these changes and store the
        # bit value of the "QMessageBox.StandardButton" enumeration member
        # signifying the button clicked by the user.
        button_clicked = guimessage.show_warning(
            title=QCoreApplication.translate(
                'QBetseeSimConf', 'Unsaved Simulation Configuration'),
            synopsis=QCoreApplication.translate(
                'QBetseeSimConf',
                'The currently open simulation configuration has '
                'unsaved changes.'
            ),
            exegesis=QCoreApplication.translate(
                'QBetseeSimConf', 'Would you like to save these changes?'),
            buttons=(
                QMessageBox.Save |
                QMessageBox.Discard |
                QMessageBox.Cancel
            ),
            button_default=QMessageBox.Save,
        )

        # If the "Cancel" button was clicked, report failure.
        if button_clicked == QMessageBox.Cancel:
            return False

        # If the "Save" button was clicked, save these changes. Namely,
        # reserialize this configuration back to the same file.
        if button_clicked == QMessageBox.Save:
            self.p.save_inplace()
        # Else, the "Discard" button was clicked. Discard these changes by
        # doing absolutely nothing.

        # In either case, report success.
        return True

    # ..................{ SHOWERS                            }..................
    def _show_dialog_sim_conf_open(self) -> str:
        '''
        Display a dialog requiring the user to select an existing YAML-formatted
        file to be subsequently opened for reading (rather than overwriting) as
        the new simulation configuration, returning the absolute path of this
        file if this dialog was not canceled *or* ``None`` otherwise (i.e., if
        this dialog was canceled).
        '''

        return guifile.select_file_yaml_read(
            dialog_title=QCoreApplication.translate(
                'QBetseeSimConf', 'Open Simulation Configuration'))


    def _show_dialog_sim_conf_save(self) -> str:
        '''
        Display a dialog requiring the user to select a YAML-formatted file
        (either existing or non-existing) to be subsequently opened for in-place
        saving and hence overwriting as the new simulation configuration,
        returning the absolute path of this file if this dialog was not canceled
        *or* ``None`` otherwise (i.e., if this dialog was canceled).
        '''

        return guifile.select_file_yaml_save(
            dialog_title=QCoreApplication.translate(
                'QBetseeSimConf', 'New Simulation Configuration'))
