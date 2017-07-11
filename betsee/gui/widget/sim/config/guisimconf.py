#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

#FIXME: Correctly setting the "_is_unsaved" flag on simulation configuration
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
from PySide2.QtCore import QObject, Signal
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.gui.widget.guimainwindow import QBetseeMainWindow

# ....................{ CLASSES                            }....................
class QBetseeSimConfig(QObject):
    '''
    :mod:`PySide2`-based management object encapsulating all high-level
    simulation configuration state.

    This state includes:

    * Whether or not a simulation configuration is currently open.
    * Whether or not an open simulation configuration has unsaved changes.

    Attributes (Non-widgets)
    ----------
    _filename : str
        Absolute path of the YAML-formatted simulation configuration file if
        such a configuration is currently open *or* ``None`` otherwise.
    _is_open : bool
        ``True`` only if a simulation configuration is currently open.
    _is_unsaved : bool
        ``True`` only if a simulation configuration is currently open *and* this
        configuration has unsaved changes.

    Attributes (widgets)
    ----------
    _action_new_sim : QAction
        Alias of the :attr:`QBetseeMainWindow.action_new_sim` action.
    _action_open_sim : QAction
        Alias of the :attr:`QBetseeMainWindow..action_open_sim` action.
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
        Initialize this objected owned by the passed main window widget.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all instance variables of this main window subsequently
        # required by this object. Since this main window owns this object,
        # since weak references are unsafe in a multi-threaded GUI context, and
        # since circular references are bad, this object intentionally does
        # *NOT* retain a reference to this main window.
        self._action_new_sim      = main_window.action_new_sim
        self._action_open_sim     = main_window.action_open_sim
        self._action_close_sim    = main_window.action_close_sim
        self._action_save_sim     = main_window.action_save_sim
        self._action_save_sim_as  = main_window.action_save_sim_as
        self._sim_conf_stack      = main_window.sim_conf_stack
        self._sim_conf_tree_frame = main_window.sim_conf_tree_frame
        self._sim_phase_tabs      = main_window.sim_phase_tabs

        # Initialize all instance variables for safety.
        self._filename = None
        self._is_open = False
        self._is_unsaved = False

        # Connect all relevant signals and slots.
        self._init_connections(main_window)

        # Update the state of all widgets dependent upon this object's state
        # *AFTER* connecting these signals and slots implementing this update.
        self._update_widgets()


    @type_check
    def _init_connections(self, main_window: QBetseeMainWindow) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets (including the
        main window, top-level widgets of that window, and leaf widgets
        distributed throughout this application) whose internal state pertains
        to the high-level state of this simulation configuration.

        Specifically:

        * When any such widget's content (e.g., editable text, selectable item)
          is modified, widgets elsewhere are notified of this simulation
          configuration modification via the
          :attr:`update_is_sim_conf_unsaved_signal` signal.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # Log this initialization.
        logs.log_debug('Aggregating widget change connectivity...')

        # Connect this object's signals to this window's corresponding slots.
        self.update_sim_conf_filename_signal.connect(
            main_window.update_sim_conf_filename)
        self.update_is_sim_conf_unsaved_signal.connect(
            main_window.update_is_sim_conf_unsaved)

    # ..................{ SIGNALS                            }..................
    update_sim_conf_filename_signal = Signal(str)
    '''
    Signal passed either the absolute path of the currently open YAML-formatted
    simulation configuration file if any *or* ``None`` otherwise.
    '''


    update_is_sim_conf_unsaved_signal = Signal(bool)
    '''
    Signal passed a single boolean in response to the currently open
    simulation configuration associated with the main window (if any) either
    containing unsaved changes *or* having just saved such changes.
    '''

    # ..................{ UPDATERS                           }..................
    def _update_widgets(self) -> None:
        '''
        Update the state (e.g., enabled or disabled, displayed or hidden) of all
        application widgets pertaining to high-level simulation configuration
        state (e.g., open or closed, saved or unsaved).
        '''

        # Enable or disable actions requiring an open simulation configuration.
        self._action_close_sim.setEnabled(self._is_open)
        self._action_save_sim_as.setEnabled(self._is_open)

        # Enable or disable actions requiring an open simulation configuration
        # with unsaved changes.
        self._action_save_sim.setEnabled(self._is_unsaved)

        #FIXME: Re-enable after widget change detection behaves as expected.

        # Show or hide widgets requiring an open simulation configuration.
        # self._sim_conf_stack.setVisible(self._is_open)
        # self._sim_conf_tree_frame.setVisible(self._is_open)
        # self._sim_phase_tabs.setVisible(self._is_open)

        # Update all widgets dependent upon this simulation configuration state.
        self.update_sim_conf_filename_signal.emit(self._filename)
        self.update_is_sim_conf_unsaved_signal.emit(self._is_unsaved)
