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
#* Define a new "QBetseeSimConfig.is_init" boolean property set to "True" only
#  if edit widgets are currently being populated.
#* In all "QBetseeSimConfigEditWidgetMixin" subclasses, avoid pushing undo
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
from PySide2.QtCore import QObject, Signal, Slot
from betse.util.io.log import logs
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.gui.widget.guimainwindow import QBetseeMainWindow

# ....................{ CLASSES                            }....................
class QBetseeSimConfig(QObject):
    '''
    :mod:`PySide2`-based management object encapsulating all high-level
    simulation configuration state.

    This state includes:

    * Whether or not a simulation configuration is currently open.
    * Whether or not an open simulation configuration has unsaved changes.

    Attributes (Non-widgets: Public)
    ----------
    undo_stack : QBetseeUndoStackSimConfig
        Undo stack for the currently open simulation configuration if any *or*
        the empty undo stack otherwise. To allow external callers (e.g.,
        :class:`QBetseeWidgetMixinSimConfigEdit` instances) to access this
        attribute, this attribute is public rather than private.

    Attributes (Non-widgets: Private)
    ----------
    _filename : str
        Absolute path of the YAML-formatted file underlying this simulation
        configuration file if a configuration is currently open *or* ``None``
        otherwise.
    _is_open : bool
        ``True`` only if a simulation configuration is currently open.
    _is_file : bool
        ``True`` only if a simulation configuration is currently open *and* the
        user has explicitly associated this configuration with an existing
        YAML-formatted file (e.g., by opening this file or saving a
        configuration as this file).
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
    _sim_conf_stack : QBetseeSimConfigStackedWidget
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

        # Nullify all stateful instance variables for safety. While the signals
        # subsequently emitted by this method also do so, ensure sanity if these
        # variables are tested in the interim.
        self._filename = None
        self._is_dirty = False
        self._is_file = False
        self._is_open = False
        self.undo_stack = None

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
            QBetseeUndoStackSimConfig)

        # Undo stack for this simulation configuration.
        self.undo_stack = QBetseeUndoStackSimConfig(
            main_window=main_window, sim_config=self)

        #FIXME: Shift unrolled into the "guisimconfstack" submodule.

        # # Generator yielding 2-tuples of the name and value of each editable
        # # simulation configuration widget, matching all instance variables of
        # # this main window with names prefixed by a unique substring.
        # edit_widgets = objects.iter_vars_custom_simple_prefixed(
        #     obj=main_window, prefix=SIM_CONF_EDIT_WIDGET_NAME_PREFIX)
        #
        # # For each such widget...
        # for _, edit_widget in edit_widgets:
        #     # If this widget does *NOT* implement the editable widget API, raise
        #     # an exception.
        #     objects.die_unless_instance(
        #         obj=edit_widget, cls=QBetseeWidgetMixinSimConfigEdit)
        #
        #     # Initialize this widget against this state object.
        #     edit_widget.init(self)


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

    # ..................{ SIGNALS                            }..................
    #FIXME: Emit this signal on opening, closing, or saving-as a simulation.
    set_filename_signal = Signal(str)
    '''
    Signal passed either the absolute path of the currently open YAML-formatted
    simulation configuration file if any *or* ``None`` otherwise.

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

        # Classify this parameter.
        self._filename = filename

        # Record this simulation configuration to be open only if this filename
        # is a non-empty string. While there exist numerous means of doing so,
        # this approach remains the simplest, most efficient, and most Pythonic,
        # handling both "None" values and the empty string. This approach is
        # equivalent to:
        #     self._is_open = is not None and len(filename)
        self._is_open = not not filename
        # logs.log_debug('filename: %s; _is_open: %r', self._filename, self._is_open)

        # Notify all interested slots that no unsaved changes remain, regardless
        # of whether a simulation configuration has just been opened or closed.
        # Since this implicitly calls the _set_widget_state() method to set the
        # state of all widgets owned by this object, this method is
        # intentionally *NOT* called again here.
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
    #FIXME: Implement us up.
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
        # configuration file selected by arbitrary default.
        filename = 'my_sim.yaml'

        # Record that this configuration is unassociated with an existing file
        # *BEFORE* signalling slots of this event, which test this boolean.
        self._is_file = False

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(filename)


    #FIXME: Implement us up.
    @Slot()
    def _open_sim(self) -> None:
        '''
        Slot invoked on the user requesting that the currently open simulation
        configuration if any be closed and an existing external simulation
        configuration be opened.
        '''

        #FIXME: Obtain this path from a file dialog.
        # Absolute path of an existing YAML-formatted simulation configuration
        # file selected by the user.
        filename = 'my_sim.yaml'

        # Record that this configuration is associated with an existing file
        # *BEFORE* signalling slots of this event, which test this boolean.
        self._is_file = True

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(filename)


    #FIXME: Implement the rest of us up.
    @Slot()
    def _close_sim(self) -> None:
        '''
        Slot invoked on the user requesting the currently open simulation
        configuration be closed.

        If this configuration is dirty (i.e., has unsaved changes), the user
        will be interactively prompted to save this changes *before* this
        configuration is closed and these changes irrevocably lost.
        '''

        # Record that no configuration exists to be associated with an existing
        # file *BEFORE* signalling slots of this event, which test this boolean.
        self._is_file = False

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(None)


    #FIXME: Implement us up.
    @Slot()
    def _save_sim(self) -> None:
        '''
        Slot invoked on the user requesting all unsaved changes to the currently
        open simulation configuration be written to the external YAML-formatted
        file underlying this configuration, overwriting the contents of this
        file.
        '''

        # Notify all interested slots of this event.
        self.set_dirty_signal.emit(None)


    #FIXME: Implement us up.
    @Slot()
    def _save_sim_as(self) -> None:
        '''
        Slot invoked on the user requesting the currently open simulation
        configuration be written to an arbitrary external YAML-formatted file.
        '''

        # Absolute path of an existing YAML-formatted simulation configuration
        # file selected by the user.
        filename = 'my_sim.yaml'

        # Record that this configuration is associated with an existing file
        # *BEFORE* signalling slots of this event, which test this boolean.
        self._is_file = True

        # Notify all interested slots of this event.
        self.set_filename_signal.emit(filename)

    # ..................{ SETTERS                            }..................
    def _set_widget_state(self) -> None:
        '''
        Set the state (e.g., enabled or disabled, displayed or hidden) of all
        widgets owned by this object.
        '''

        # Enable or disable actions requiring an open simulation configuration.
        self._action_close_sim.setEnabled(self._is_open)
        self._action_save_sim_as.setEnabled(self._is_open)

        # Enable or disable actions requiring an open simulation configuration
        # associated with an existing file and having unsaved changes.
        self._action_save_sim.setEnabled(self._is_file and self._is_dirty)

        # Show or hide widgets requiring an open simulation configuration.
        self._sim_conf_stack.setVisible(self._is_open)
        self._sim_conf_tree_frame.setVisible(self._is_open)
        self._sim_phase_tabs.setVisible(self._is_open)

        # If a simulation configuration is open...
        if self._is_open:
            # ...and this configuration is clean, mark the undo stack as clean.
            if not self._is_dirty:
                self.undo_stack.setClean()
        # Else, no simulation configuration is open. Clear the undo stack.
        else:
            self.undo_stack.clear()
