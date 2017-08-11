#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
from PySide2.QtWidgets import QMessageBox
from betse.lib.yaml import yamls
from betse.science.config import confio
from betse.science.parameters import Parameters
from betse.util.io.log import logs
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.gui.widget.guimainwindow import QBetseeMainWindow
from betsee.util.path import guifile
from betsee.util.widget import guimessage

# ....................{ CLASSES                            }....................
class QBetseeSimConf(QObject):
    '''
    :mod:`PySide2`-based object encapsulating all high-level simulation
    configuration state.

    This state includes:

    * Whether or not a simulation configuration is currently open.
    * Whether or not an open simulation configuration has unsaved changes.

    Attributes (Non-widgets: Public)
    ----------
    p : Parameters
        High-level simulation configuration encapsulating a low-level dictionary
        parsed from an even lower-level YAML-formatted file.
    undo_stack : QBetseeUndoStackSimConf
        Undo stack for the currently open simulation configuration if any *or*
        the empty undo stack otherwise.

    Attributes (Non-widgets: Private)
    ----------
    _is_dirty : bool
        ``True`` only if a simulation configuration is currently open *and* this
        configuration is **dirty** (i.e., has unsaved changes).

    Attributes (widgets)
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
    _sim_conf_tree_frame : QFrame
        Alias of the :attr:`QBetseeMainWindow.sim_conf_tree_frame` widget.
    _sim_phase_tabs : QTabWidget
        Alias of the :attr:`QBetseeMainWindow.sim_phase_tabs` widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, main_window: QBetseeMainWindow, *args, **kwargs) -> None:
        '''
        Initialize this object, owned by the passed main window widget.

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
        super().__init__(*args, **kwargs)

        # Log this initialization.
        logs.log_debug('Sanitizing simulation configuration state...')

        # High-level simulation configuration, defaulting to the unread state.
        self.p = Parameters()

        # Nullify all stateful instance variables for safety. While the signals
        # subsequently emitted by this method also do so, ensure sanity if these
        # variables are tested in the interim.
        self.undo_stack = None
        self._is_dirty = False

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
        self._sim_conf_tree_frame = main_window.sim_conf_tree_frame
        self._sim_phase_tabs      = main_window.sim_phase_tabs

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
        from betsee.gui.widget.sim.config.guisimconfundo import (
            QBetseeUndoStackSimConf)

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

        # Connect this object's signals to all corresponding slots.
        self.set_filename_signal.connect(main_window.set_sim_conf_filename)
        self.set_filename_signal.connect(self.set_filename)
        self.set_dirty_signal.connect(main_window.set_sim_conf_dirty)
        self.set_dirty_signal.connect(self.set_dirty)

        # Set the state of all widgets dependent upon this simulation
        # configuration state *AFTER* connecting all relavant signals and slots.
        # Since this slot only accepts strings, pass the empty string rather
        # than "None" for safety.
        self.set_filename_signal.emit('')

    # ..................{ PROPERTIES ~ read-only             }..................
    # Read-only properties, preventing callers from resetting these attributes.

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
        # Since this implicitly calls the _update_widget_state() method to set the
        # state of all widgets owned by this object, this method is
        # intentionally *NOT* called again here.
        #
        # Note that, as this slot is already connected to the
        # "set_filename_signal", this signal must *NOT* be re-emitted here;
        # doing so would provoke infinite recursion.
        self.set_dirty_signal.emit(False)


    @Slot(bool)
    def set_dirty(self, is_dirty: bool) -> None:
        '''
        Slot signalled on each change of the **dirty state** (i.e., existence of
        unsaved in-memory changes) of the currently open simulation
        configuration if any.

        Parameters
        ----------
        is_dirty : bool
            ``True`` only if a simulation configuration is currently open *and*
            this configuration is **dirty** (i.e., has unsaved changes).
        '''

        # Classify this parameter.
        self._is_dirty = is_dirty

        # Set the state of all widgets owned by this object.
        self._update_widget_state()

    # ..................{ SLOTS ~ action                     }..................
    @Slot()
    def _make_sim(self) -> None:
        '''
        Slot invoked on the user requesting that the currently open simulation
        configuration if any be closed and a new simulation configuration with
        default settings be both created and opened.
        '''

        # Close the currently open simulation configuration if any.
        self._close_sim()

        # Absolute path of a possibly non-existing YAML-formatted simulation
        # configuration file selected by the user.
        conf_filename = self._show_dialog_sim_conf_save()

        # If the user canceled this dialog, silently noop.
        if conf_filename is None:
            return
        # Else, the user did *NOT* cancel this dialog.

        # Silently (over)write this file and all external resources required by
        # this file with those contained in this default simulation
        # configuration. Since the guifile.save_file() function has already
        # interactively confirmed this overwrite when this file already exists,
        # doing so is safe to the extent that the user has accepted the pain.
        confio.write_default(
            conf_filename=conf_filename, is_overwritable=True)

        # Deserialize this low-level file into a high-level configuration.
        self.open_sim_conf(conf_filename)


    @Slot()
    def _open_sim(self) -> None:
        '''
        Slot invoked on the user requesting that the currently open simulation
        configuration if any be closed and an existing external simulation
        configuration be opened.
        '''

        # Close the currently open simulation configuration if any.
        self._close_sim()

        # Absolute path of an existing YAML-formatted simulation configuration
        # file selected by the user.
        conf_filename = self._show_dialog_sim_conf_open()

        # If the user canceled this dialog, silently noop.
        if conf_filename is None:
            return
        # Else, the user did *NOT* cancel this dialog.

        # Deserialize this low-level file into a high-level configuration.
        self.open_sim_conf(conf_filename)


    #FIXME: The QBetseeMainWindow.closeEvent() method should be overridden to
    #call this method and respond appropriately: e.g.,
    #
    #    def closeEvent(self, event):
    #        if self._sim_conf is None or self._sim_conf.is_saved_if_dirty():
    #            event.accept()
    #        else:
    #            event.ignore()
    #
    #Naturally, we'll want to define a new is_saved_if_dirty() method as well.

    @Slot()
    def _close_sim(self) -> None:
        '''
        Slot invoked on the user attempting to close the currently open
        simulation configuration.

        If this configuration is dirty (i.e., has unsaved changes), the user
        will be interactively prompted to save this changes *before* this
        configuration is closed and these changes irrevocably lost.
        '''

        # If this configuration is dirty (i.e., has unsaved changes)...
        if self._is_dirty:
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
                    'QBetseeSimConf',
                    'Would you like to save these changes?',
                ),
                buttons=(
                    QMessageBox.Save |
                    QMessageBox.Discard |
                    QMessageBox.Cancel
                ),
                button_default=QMessageBox.Save,
            )

            # If the "Cancel" button was clicked, silently noop.
            if button_clicked == QMessageBox.Cancel:
                return

            # If the "Save" button was clicked, save these changes. Namely,
            # reserialize this configuration back to the same file.
            if button_clicked == QMessageBox.Save:
                self.p.overwrite()
            # Else, the "Discard" button was clicked. Discard these changes by
            # doing absolutely nothing.

        # Revert this configuration to the unread state.
        self.p.unread()

        # Notify all interested slots of this event.
        self.set_filename_signal.emit('')


    @Slot()
    def _save_sim(self) -> None:
        '''
        Slot invoked on the user requesting all unsaved changes to the currently
        open simulation configuration be written to the external YAML-formatted
        file underlying this configuration, overwriting the contents of this
        file.
        '''

        # Reserialize this configuration back to the same file.
        self.p.overwrite()

        # Notify all interested slots of this event.
        self.set_dirty_signal.emit(True)


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
        self.p.write(conf_filename)

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(conf_filename)

    # ..................{ OPENERS                            }..................
    @type_check
    def open_sim_conf(self, conf_filename: str) -> None:
        '''
        Deserialize the passed low-level YAML-formatted simulation configuration
        file into a high-level :class:`Parameters` object *and* signal all
        connected slots of this event.

        Parameters
        ----------
        conf_filename : str
            Absolute path of this file.
        '''

        # Deserialize this low-level file into a high-level configuration.
        self.p.read(conf_filename)

        # Signal all interested slots of this event.
        self.set_filename_signal.emit(conf_filename)

    # ..................{ SHOWERS                            }..................
    def _show_dialog_sim_conf_open(self) -> str:
        '''
        Display a dialog requiring the user to select an existing YAML-formatted
        file to be subsequently opened for reading (rather than overwriting) as
        the new simulation configuration, returning the absolute path of this
        file if this dialog was not canceled *or* ``None`` otherwise (i.e., if
        this dialog was canceled).
        '''

        return guifile.open_file(
            title=QCoreApplication.translate(
                'QBetseeSimConf', 'Open Simulation Configuration'),
            label_to_filetypes={'YAML files': yamls.FILETYPES,},
        )


    def _show_dialog_sim_conf_save(self) -> str:
        '''
        Display a dialog requiring the user to select a YAML-formatted file
        (either existing or non-existing) to be subsequently opened for in-place
        saving and hence overwriting as the new simulation configuration,
        returning the absolute path of this file if this dialog was not canceled
        *or* ``None`` otherwise (i.e., if this dialog was canceled).
        '''

        return guifile.save_file(
            title=QCoreApplication.translate(
                'QBetseeSimConf', 'New Simulation Configuration'),
            label_to_filetypes={'YAML files': yamls.FILETYPES,},
        )

    # ..................{ SETTERS                            }..................
    def _update_widget_state(self) -> None:
        '''
        Update the state (e.g., enabled or disabled, displayed or hidden) of all
        widgets owned or otherwise associated with this object.
        '''

        # Enable or disable actions requiring an open simulation configuration.
        self._action_close_sim  .setEnabled(self.p.is_read)
        self._action_save_sim_as.setEnabled(self.p.is_read)

        # Enable or disable actions requiring an open simulation configuration
        # associated with an existing file and having unsaved changes.
        self._action_save_sim.setEnabled(self.p.is_read and self._is_dirty)

        # Show or hide widgets requiring an open simulation configuration.
        self._sim_conf_stack     .setVisible(self.p.is_read)
        self._sim_conf_tree_frame.setVisible(self.p.is_read)
        self._sim_phase_tabs     .setVisible(self.p.is_read)

        # If a simulation configuration is open...
        if self.p.is_read:
            pass

            #FIXME: Excise the following, which is no longer required.
            # ...and this configuration is clean, mark the undo stack as clean.
            # if not self._is_dirty:
            #     self.undo_stack.setClean()
        # Else, no simulation configuration is open. Clear the undo stack.
        else:
            self.undo_stack.clear()
