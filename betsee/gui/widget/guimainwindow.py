#!/usr/bin/env python3
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Top-level classes defining this application's main window.

Caveats
----------
This submodule imports from the module whose fully-qualified name is given by
:attr:`metadata.MAIN_WINDOW_UI_MODULE_NAME`, an external top-level module
dynamically generated at runtime from XML-formatted files exported by the
external Qt Designer GUI and bundled with this application's codebase. Since
that module is *not* guaranteed to exist at application startup, this
submodule is safely importable only *after* the :mod:`betsee.gui.guicache`
submodule has locally created and cached that module for the current user.
'''

#FIXME: Consider permitting multiple simulations to be simultaneously open. The
#conventional means of doing so is the so-called Single Documentation Interface
#(SDI) approach, in which opening a new document opens a new distinct
#application window displaying that new document; open documents and hence
#windows may then be switched between via a "Windows" menu item listing all
#currently open documents. Supporting SDI would permit end users to run multiple
#simultaneous simulations, which only seems reasonable. As a PySide2-specific
#example, see the "pyside2-examples/examples/widgets/mainwindows/sdi/sdi.py"
#application. While incomplete, this application should serve as a simple
#starting point for implementing our own SDI. (It's only 295 lines!)
#FIXME: Actually, modern UI design strongly favours "QTabWidget"-style
#browser-based multiplicity -- and so do we. Ergo, classical window-style
#SDI- and MDI-based multiplicity are right out. That said, it shouldn't be
#terribly arduous to add a new top-level "QTabWidget" permitting multiple
#concurrently open simulations to be switched between.

#FIXME: An application icon should be set. Of course, we first need to create an
#application icon - ideally in SVG format. For exhaustive details on portability
#issues, see the well-written "Setting the Application Icon" article.

#FIXME: The title of the main window should probably be dynamically modified on
#opening and closing a simulation configuration file to reflect both the
#basename of this file *AND* a character indicating whether this file has
#unsaved changes or not. Courtesy the official documentation for the
#"QWidget.windowModified" boolean property:
#
#    "The window title must contain a "[*]" placeholder, which indicates where
#     the '*' should appear. Normally, it should appear right after the file
#     name (e.g., "document1.txt[*] - Text Editor"). If the window isn't
#     modified, the placeholder is simply removed.
#
#     On some desktop platforms (including Windows and Unix), the application
#     name (from QGuiApplication::applicationDisplayName) is added at the end of
#     the window title, if set. This is done by the QPA plugin, so it is shown
#     to the user, but isn't part of the windowTitle string."

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.gui.widget"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Accessing attributes of the "PySide2.QtCore.Qt" subpackage requires this
# subpackage to be imported directly. Attributes are *NOT* importable from this
# subpackage, contrary to pure-Python expectation.
from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QCloseEvent
from betse.util.io.log import logs
from betse.util.path import pathnames
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee import metadata
from betsee.gui.guisignal import QBetseeSignaler
from betsee.util.io import psderr
from betsee.util.io.log import psdlogconfig
from betsee.util.path import psdui

# ....................{ GLOBALS                            }....................
MAIN_WINDOW_BASE_CLASSES = psdui.get_ui_module_base_classes(
    ui_module_name=metadata.MAIN_WINDOW_UI_MODULE_NAME)
'''
Sequence of all main window base classes declared by the module whose
fully-qualified name is given by :attr:`metadata.MAIN_WINDOW_UI_MODULE_NAME`.
'''

# ....................{ CLASSES                            }....................
# Subclass all main window base classes declared by the above module (in order).
# While multiple inheritance typically invites complex complications (e.g.,
# diamond inheritance problem) and hence is best discouraged, these base classes
# are guaranteed *NOT* to conflict in this manner. All alternatives to this
# multiple inheritance design invite worse complications and otherwise avoidable
# annoyances. In short, this is arguably the best we can do.
#
# For further details, see the following classic PyQt treatise:
#     http://pyqt.sourceforge.net/Docs/PyQt5/designer.html
class QBetseeMainWindow(*MAIN_WINDOW_BASE_CLASSES):
    '''
    Main window Qt widget for this application, doubling as both this
    application's root Qt widget containing all other Qt widgets.

    Design
    ----------
    This class subclasses all main window base classes declared by the module
    whose fully-qualified name is given by
    :attr:`metadata.MAIN_WINDOW_UI_MODULE_NAME`. While multiple inheritance
    often invites complex complications (e.g., diamond inheritance) and hence is
    best discouraged, these base classes are guaranteed *not* to conflict in
    this manner. All alternatives to this multiple inheritance design invite
    worse complications and otherwise avoidable annoyances. In short, this is
    arguably the best we can do.

    Attributes (Public)
    ----------
    signaler : QBetseeSignaler
        :class:`PySide2`-based collection of various application-wide signals.
        To allow external callers (e.g., :class:`QBetseeSettings`) to access
        this object, this object is public rather than private.

    Attributes (Private)
    ----------
    _sim_conf : QBetseeSimConfig
        Object encapsulating high-level simulation configuration state.

    See Also
    ----------
    http://pyqt.sourceforge.net/Docs/PyQt5/designer.html
        :mod:`PyQt5`-specific documentation detailing this design.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(
        self,
        signaler: QBetseeSignaler,
        *args, **kwargs
    ) -> None:
        '''
        Initialize this main window.

        Parameters
        ----------
        signaler : QBetseeSettingsSignaler
            :class:`PySide2`-based collection of application-wide signals.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all remaining parameters.
        self.signaler = signaler

        # Nullify all remaining instance variables for safety.
        self._sim_config = None

        # Log this initialization.
        logs.log_debug('Fabricating main window...')

        # Customize this main window as specified by the XML-formatted UI file
        # exported by Qt Creator. This superclass method is defined by the
        # helper base class generated by the "betsee.lib.pyside.psdui" module.
        self.setupUi(self)

        # Customize this main window with additional Python logic.
        self._init()


    def _init(self) -> None:
        '''
        Customize this main window with additional Python logic *after*
        customizing this main window as specified by the XML-formatted UI file
        exported by Qt Creator.

        Design
        ----------
        **Customizations implemented by this method must not be implementable
        by this UI file.** Equivalently, this method should *only* implement
        customizations requiring dynamic Python logic, which typically implies
        signals and slots. For portability, all other customizations should be
        implemented by this UI file.
        '''

        # Append all unfiltered log records to the top-level log widget in an
        # autoscrolling, non-blocking, thread-safe manner *BEFORE* performing
        # any subsequent logic possibly performing logging.
        psdlogconfig.log_to_text_edit(self.log_box)

        # Customize all abstract QAction widgets of this main window.
        self._init_actions()

        # Customize all physical top-level widgets of this main window.
        self._init_widgets()

        # Create all non-physical abstract objects of this main window.
        self._init_objects()

    # ..................{ INITIALIZERS ~ actions             }..................
    def _init_actions(self) -> None:
        '''
        Customize all abstract :class:`QAction` widgets of this main window,
        typically by associating the predefined C-based signals of these widgets
        with custom pure-Python slot callables.
        '''

        # Customize all QAction widgets in the "File", "Edit", and "Help" menus.
        self._init_actions_file()
        self._init_actions_edit()
        self._init_actions_help()

        #FIXME: Implement all remaining actions.

        # Default all remaining actions to display an error box informing the
        # end user that this action has yet to be implemented.
        for action in (
            # "File" menu.
            self.action_new_sim,
            self.action_open_sim,
            self.action_close_sim,
            self.action_save_sim,
            self.action_save_sim_as,

            # "Edit" menu.
            self.action_undo,
            self.action_redo,
            self.action_cut,
            self.action_copy,
            self.action_paste,
            self.action_edit_prefs,

            # "Help" menu.
            self.action_about_betse,
            self.action_about_betsee,
        ):
            action.triggered.connect(self._show_error_action_unimplemented)


    def _init_actions_file(self) -> None:
        '''
        Customize all QAction widgets of the top-level ``File`` menu.
        '''

        # Associate QAction slots with Python signals.
        self.action_exit.triggered.connect(self.close)


    def _init_actions_edit(self) -> None:
        '''
        Customize all QAction widgets of the top-level ``Edit`` menu.
        '''

        pass


    def _init_actions_help(self) -> None:
        '''
        Customize all QAction widgets of the top-level ``Help`` menu.
        '''

        pass

    # ..................{ INITIALIZERS ~ widgets             }..................
    def _init_widgets(self) -> None:
        '''
        Customize all physical top-level widgets of this main window, thus
        excluding all abstract widgets (e.g., :class:`QAction`).
        '''

        # Initialize both the simulation configuration tree and stack widgets.
        self.sim_conf_tree.init(self)

    # ..................{ INITIALIZERS ~ objects             }..................
    def _init_objects(self) -> None:
        '''
        Create all non-physical abstract non-widgets of this main window, thus
        excluding widgets (both physical and abstract).
        '''

        # Avoid circular import dependencies.
        from betsee.gui.widget.sim.config.guisimconf import QBetseeSimConfig

        # Object encapsulating high-level simulation configuration state.
        self._sim_conf = QBetseeSimConfig(self)

    # ..................{ INITIALIZERS                       }..................
    def _show_error_action_unimplemented(self) -> None:
        '''
        Display a modal message box informing the end user that the currently
        selected action has yet to be implemented.
        '''

        psderr.show_error(
            title='Action Unimplemented',
            synopsis='This action is currently unimplemented.',
        )

    # ..................{ EVENT HANDLERS                     }..................
    def closeEvent(self, event: QCloseEvent) -> None:
        '''
        Event handler handling the passed close event signifying a user-driven
        request to close this main window and exit the current application.
        '''

        # Log this closure.
        logs.log_info('Finalizing PySide2 UI...')

        # Store application-wide settings *BEFORE* closing this window.
        self.signaler.store_settings_signal.emit()

        # Accept this request, thus finalizing the closure of this window.
        event.accept()

    # ..................{ SLOTS ~ sim conf                   }..................
    @Slot(str)
    def update_sim_conf_filename(
        self, sim_conf_filename: StrOrNoneTypes) -> None:
        '''
        Slot invoked in response to both the opening of new simulation
        configurations *and* the closing of open simulation configurations.

        Parameters
        ----------
        sim_conf_filename : StrOrNoneTypes
            Absolute path of the currently open YAML-formatted simulation
            configuration file if any *or* ``None`` otherwise.
        '''

        # If a simulation configuration is currently open...
        if sim_conf_filename is not None:
            # Basename of this configuration file.
            sim_conf_basename = pathnames.get_basename(sim_conf_filename)

            # Update this window title to contain this basename appended by a
            # Qt-specific suffix to be subsequently replaced by a
            # platform-specific identifier when the setWindowModified() method
            # is called elsewhere.
            self.setWindowTitle('{}[*]'.format(sim_conf_basename))
        # Else, no simulation configuration is currently open. In this case,
        # clear this window title.
        else:
            self.setWindowTitle('')


    @Slot(bool)
    def update_is_sim_conf_unsaved(self, is_sim_conf_unsaved: bool) -> None:
        '''
        Slot invoked in response to the currently open simulation configuration
        associated with this main window (if any) either having unsaved changes
        *or* having just saved such changes.

        Parameters
        ----------
        is_sim_conf_unsaved : bool
            ``True`` only if a simulation configuration is currently open *and*
            this configuration has unsaved changes.
        '''

        # Set the modification state of this window to correspond to the
        # modification state of this simulation configuration, an operation that
        # has platform-specific effects usually including appending an asterisk
        # to the current window title.
        self.setWindowModified(is_sim_conf_unsaved)

    # ..................{ RESIZERS                           }..................
    def resize_full(self) -> None:
        '''
        Enable full-screen mode for this main window.

        Specifically, this method:

        * Hides all standard window decorations, including the window frame and
          title bar.
        * Resize this window to consume all available screen space.
        '''

        self.setWindowState(self.windowState() | Qt.WindowFullScreen)


    def resize_max(self) -> None:
        '''
        Else, expand this window to consume all available horizontal and
        vertical screen space.

        Note that:

        * This does *not* constitute "full screen" mode, which is typically
          desirable only for console-oriented applications (e.g., OpenGL).
        * This is *not* supported by Qt Creator and hence must be performed
          with Python logic here.
        * The more convenient :meth:`showMaximized` method is intentionally
          *not* called here, as doing so would implicitly render the entire GUI
          (which could currently be under construction) visible.
        '''

        self.setWindowState(self.windowState() | Qt.WindowMaximized)

    # ..................{ STATUS                             }..................
    @type_check
    def _show_status(self, text: str) -> None:
        '''
        Display the passed string as a **temporary message** (i.e., string
        temporarily replacing any normal message currently displayed) in the
        status bar.
        '''

        #FIXME: Validate this string to contain no newlines. Additionally,
        #consider emitting a warning if the length of this string exceeds a
        #sensible maximum (say, 160 characters or so).

        # Display this temporary message.
        self.status_bar.showMessage(text)


    def _clear_status(self) -> None:
        '''
        Remove the temporary message currently displayed in the status bar if
        any *or* reduce to a noop otherwise.

        This Any normal message was displayed prior to this temporary message being
        displayed in the status bar,
        '''

        self.status_bar.clearMessage()
