#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

#FIXME: Clear the undo stack immediately after populating edit widgets on the
#initial creation or opening of a new simulation configuration. Why? Because
#populating these widgets emits signals inducing ignorable undo commands to be
#pushed onto the undo stack. Alternately (and probably preferably), we might
#instead:
#
#* Define a new "QBetseeSimConf.is_init" boolean property set to "True" only
#  if edit widgets are currently being populated.
#* In all "QBetseeSimConfEditWidgetMixin" subclasses, avoid pushing undo
#  commands onto the stack if this property is "True."

#FIXME: Correctly setting the "_is_dirty" flag on simulation configuration
#changes is *NOT* going to be easy, unfortunately. Specifically:
#
#* The pair of QWidget.isWindowChanged() and QWidget.setWindowChanged() methods
#  that *COULD* have made detecting widget changes simpler fail to propagate to
#  parent widgets and hence are effectively useless.
#* The "QEvent::ModifiedChange" event type is emitted for only some but *NOT*
#  all widget changes of interest. Of course, right? From StackOverflow:
#  "I have QFrame::eventFilter installed on the QDateEdit anyway because I need
#   to change row selection for QTableWidget if QDateEdit was edited so I
#   thought I could use it instead... but QEvent::ModifiedChange doesn't work
#   for that and I don't know what to use..."
#* The QLineEdit.isModified() and QTextEdit.isModified() methods are provided
#  *ONLY* by those widgets, despite their general utility.
#* The QWidget.changeEvent() method that that *COULD* also have made detecting
#  widget changes is a protected event handler rather than a public signal.
#  This means that overriding the default handling for widget change events
#  would require:
#  * Defining one BETSEE-specific widget subclass for each widget superclass of
#    interest (e.g., "QBetseeLineEdit" for "QLineEdit").
#  * Overriding the changeEvent() method in that subclass to:
#    * Detect whether the current change event corresponds to an event of
#      interest (e.g., text change).
#    * If so, explicitly emit a signal to a corresponding slot of this
#      "QBetseeMainWindow" instance, which should then register this change.
#  * Explicitly promoting each changeable widget of interest in Qt Creator to
#    our BETSEE-specific widget subclass.
#
#Technically, this *WOULD* maybe work -- but it's also incredibly cumbersome. An
#alternative solution is to shift as much of this tedious manual labour as
#feasible into clever Python automation. How? Specifically:
#
#* Define a new "QBetseeMainWindow._is_sim_changed" boolean corresponding to the
#  typical "dirty" flag (i.e., "True" only if the current simulation has unsaved
#  configuration changes).
#* Define a new "QBetseeMainWindow.sim_changed" slot internally enabling this
#  "self._is_sim_changed" boolean. This slot should accept no arguments.
#* Define a new QBetseeSimConfTreeWidget._init_connections_changed() method,
#  called by the existing QBetseeSimConfTreeWidget._init_connections() method.
#* In this new method:
#  * Define a local dictionary constant mapping from each widget type of
#    interest (e.g., "QComboBox", "QLineEdit") to a tuple of the names of all
#    signals emitted by widgets of this type when their contents change: e.g.,
#
#    #FIXME: Actually, just use the new
#    #"betsee.util.type.psdwidget.FORM_WIDGET_TYPE_TO_SIGNALS_CHANGE" global.
#    WIDGET_TYPE_TO_CHANGE_SIGNALS = {
#        QLineEdit: ('textChanged',),
#        QCombobox: ('currentIndexChanged', 'editTextChanged',),
#        ...
#    }
#
#  * Iteratively find all transitive children of our top-level stack widget by
#    calling the QStackedWidget.findChildren() method.
#  * For each such child:
#    * Map this child's type to the tuple of the names of all change signals
#      emitted by widgets of this type via the "WIDGET_TYPE_TO_CHANGE_SIGNALS"
#      dictionary defined above.
#    * For each such signal name:
#      * Dynamically retrieve this signal with getattr(). (Yay!)
#      * Connect this signal to the "QBetseeMainWindow.sim_changed" slot.
#
#This exact solution is outlined, albeit without any working code, at:
#    http://www.qtcentre.org/archive/index.php/t-44026.html
#
#This is sufficiently annoying that we should consider posting a working
#solution back to StackOverflow... somewhere. The following question might be a
#reasonable place to pose this answer:
#    https://stackoverflow.com/questions/2559681/qt-how-to-know-whether-content-in-child-widgets-has-been-changed

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
from betse.lib.yaml import yamls
from betse.science.config import confio
from betse.science.parameters import Parameters
from betse.util.io.log import logs
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.util.path import guifile
from betsee.gui.widget.guimainwindow import QBetseeMainWindow

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
    undo_stack : QBetseeUndoStackSimConf
        Undo stack for the currently open simulation configuration if any *or*
        the empty undo stack otherwise.

    Attributes (Non-widgets: Private)
    ----------
    _is_dirty : bool
        ``True`` only if a simulation configuration is currently open *and* this
        configuration is **dirty** (i.e., has unsaved changes).
    _p : Parameters
        :mod:`PySide2`-agnostic object encapsulating the low-level dictionary
        deserialized from the current YAML-formatted simulation configuration.

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

        #
        self._p = Parameters()

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

        return self._p.conf_dirname


    @property
    def filename(self) -> StrOrNoneTypes:
        '''
        Absolute path of the currently open simulation configuration file if any
        *or* ``None`` otherwise.
        '''

        return self._p.conf_filename

    # ..................{ SIGNALS                            }..................
    #FIXME: Emit this signal on opening, closing, or saving-as a simulation.
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
    def set_filename(self, filename: StrOrNoneTypes) -> None:
        '''
        Slot signalled on each change of the absolute path of the currently open
        YAML-formatted simulation configuration file if any.

        Parameters
        ----------
        filename : StrOrNoneTypes
            Absolute path of this file if such a configuration is currently open
            *or* the empty string otherwise (i.e., if no such file is open).
        '''

        # Notify all interested slots that no unsaved changes remain, regardless
        # of whether a simulation configuration has just been opened or closed.
        # Since this implicitly calls the _set_widget_state() method to set the
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
        self._set_widget_state()

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
        self._open_sim_conf(conf_filename)


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
        self._open_sim_conf(conf_filename)


    #FIXME: Insufficient. If this configuration is dirty, an interactive prompt
    #should be displayed confirming this closure. See the "SDI" example
    #application for sample code, please.
    @Slot()
    def _close_sim(self) -> None:
        '''
        Slot invoked on the user requesting the currently open simulation
        configuration be closed.

        If this configuration is dirty (i.e., has unsaved changes), the user
        will be interactively prompted to save this changes *before* this
        configuration is closed and these changes irrevocably lost.
        '''

        # Revert this simulation configuration to the unread state.
        self._p.unread()

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(None)


    @Slot()
    def _save_sim(self) -> None:
        '''
        Slot invoked on the user requesting all unsaved changes to the currently
        open simulation configuration be written to the external YAML-formatted
        file underlying this configuration, overwriting the contents of this
        file.
        '''

        # Reserialize this high-level configuration to the same low-level file.
        self._p.overwrite()

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

        # Reserialize this high-level configuration to this new low-level file.
        self._p.write(conf_filename)

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(conf_filename)

    # ..................{ OPENERS                            }..................
    @type_check
    def _open_sim_conf(self, conf_filename: str) -> None:
        '''
        Deserialize the passed low-level YAML-formatted simulation configuration
        file into a high-level :class:`Parameters` object *and* signal all
        interested slots of this event.

        Parameters
        ----------
        conf_filename : str
            Absolute path of this file.
        '''

        # Deserialize this low-level file into a high-level configuration.
        self._p.read(conf_filename)

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
    def _set_widget_state(self) -> None:
        '''
        Set the state (e.g., enabled or disabled, displayed or hidden) of all
        widgets owned by this object.
        '''

        # Enable or disable actions requiring an open simulation configuration.
        self._action_close_sim.setEnabled(self._p.is_read)
        self._action_save_sim_as.setEnabled(self._p.is_read)

        # Enable or disable actions requiring an open simulation configuration
        # associated with an existing file and having unsaved changes.
        self._action_save_sim.setEnabled(self._p.is_read and self._is_dirty)

        # Show or hide widgets requiring an open simulation configuration.
        self._sim_conf_stack.setVisible(self._p.is_read)
        self._sim_conf_tree_frame.setVisible(self._p.is_read)
        self._sim_phase_tabs.setVisible(self._p.is_read)

        # If a simulation configuration is open...
        if self._p.is_read:
            # ...and this configuration is clean, mark the undo stack as clean.
            if not self._is_dirty:
                self.undo_stack.setClean()
        # Else, no simulation configuration is open. Clear the undo stack.
        else:
            self.undo_stack.clear()
