#!/usr/bin/env python3
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
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
#concurrently open simulations to be switched between. (Yeah, right.)

#FIXME: The status bar of the main window should be dynamically modified
#whenever *ANY* action (e.g., simulation opening or closure) is successfully
#completed. See to it, please.

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
# "betsee.gui.window"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Accessing attributes of the "PySide2.QtCore.Qt" subpackage requires this
# subpackage to be imported directly. Attributes are *NOT* importable from this
# subpackage, contrary to pure-Python expectation.
from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QToolButton, QWidget
from betse.util.io.log import logs
from betse.util.path import pathnames
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee import guimetadata
from betsee.guiexception import BetseePySideWindowException
from betsee.gui.guisignal import QBetseeSignaler
from betsee.util.app import guiappwindow
from betsee.util.io import guierr
from betsee.util.io.log import guilogconf
from betsee.util.io.xml import guiui
from betsee.util.type.guitype import QWidgetOrNoneTypes

# ....................{ GLOBALS                            }....................
MAIN_WINDOW_BASE_CLASSES = guiui.get_ui_module_base_classes(
    ui_module_name=guimetadata.MAIN_WINDOW_UI_MODULE_NAME)
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
    sim_conf : QBetseeSimConf
        Object encapsulating high-level simulation configuration state.
    sim_tab : QBetseeSimmerTabWidget
        Object encapsulating high-level simulator state.

    Attributes (Private)
    ----------
    _clipboard : QBetseeMainClipboard
        Object encapsulating high-level application clipboard state.
    _sim_conf_filename : StrOrNoneTypes
        Absolute or relative path of the initial YAML-formatted simulation
        configuration file to be initially opened if any *or* ``None``
        otherwise.

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
        sim_conf_filename: StrOrNoneTypes,
        *args, **kwargs
    ) -> None:
        '''
        Initialize this main window.

        Parameters
        ----------
        signaler : QBetseeSettingsSignaler
            :class:`PySide2`-based collection of application-wide signals.
        sim_conf_filename : StrOrNoneTypes
            Absolute or relative path of the initial YAML-formatted simulation
            configuration file to be initially opened if any *or* ``None``
            otherwise.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all remaining parameters.
        self.signaler = signaler
        self._sim_conf_filename = sim_conf_filename

        # Nullify all remaining instance variables for safety.
        self.sim_conf = None
        self._clipboard = None

        # Log this initialization.
        logs.log_debug('Generating main window...')

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
        guilogconf.log_to_text_edit(self.log_box)

        # Customize all abstract actions of this main window.
        self._init_actions()

        # Customize all physical top-level widgets of this main window *AFTER*
        # customizing all abstract actions required by these widgets.
        self._init_widgets()

        # Finalize the initialization of this main window *AFTER* customizing
        # all physical and abstract widgets of this window .
        self._init_end()

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
            # "Edit" menu.
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

        # Associate QAction signals with Python slots.
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


    #FIXME: Excise this, which should no longer be required.
    def _show_error_action_unimplemented(self) -> None:
        '''
        Display a modal message box informing the end user that the currently
        selected action has yet to be implemented.
        '''

        guierr.show_error(
            title='Action Unimplemented',
            synopsis='This action is currently unimplemented.',
        )

    # ..................{ INITIALIZERS ~ widgets             }..................
    def _init_widgets(self) -> None:
        '''
        Customize all physical top-level widgets of this main window, thus
        excluding all abstract widgets (e.g., :class:`QAction`).
        '''

        # Avoid circular import dependencies.
        from betsee.gui.window.guimainclipboard import QBetseeMainClipboard
        from betsee.gui.simconf.guisimconf import QBetseeSimConf

        # Object wrapping high-level state, instantiated in arbitrary order.
        self._clipboard = QBetseeMainClipboard()
        self.sim_conf = QBetseeSimConf()

        # Initialize these objects (in arbitrary order) *BEFORE* initializing
        # widgets assuming these objects to have been initialized.
        self._clipboard.init(main_window=self)
        self.sim_conf.init(main_window=self)
        self.sim_tab.init(main_window=self)

        # Initialize the simulation configuration stack widget *BEFORE* its
        # higher-level sibling tree widget, which assumes the former to have
        # been initialized.
        self.sim_conf_stack.init(main_window=self)

        # Initialize the simulation configuration tree widget.
        self.sim_conf_tree.init(main_window=self)

    # ..................{ INITIALIZERS ~ end                 }..................
    def _init_end(self) -> None:
        '''
        Finalize the initialization of this main window.

        As this method's name implies, this method is called *after* all widgets
        of this main window have been initialized. This method then performs all
        remaining logic assuming these widgets to be initialized -- including:

        * **Toolbar button sanitization.** Since widget initialization typically
          programmatically inserts additional buttons into the toolbar,
          sanitizing these buttons *must* be deferred until this method.
        '''

        # Prevent toolbar buttons from receiving the keyboard input focus,
        # ensuring that the currently focused widget if any retains focus even
        # when the user clicks one or more of these buttons. For safety, this
        # is done *AFTER* finalizing all widgets and hence programmatically
        # inserting all remaining toolbar buttons into the toolbar.
        #
        # By default, toolbar buttons are *ALWAYS* permitted to receive focus
        # regardless of whether the toolbar containing these buttons is
        # permitted to do so (i.e., has a focus policy of "NoFocus") and despite
        # there being no demonstrable use case for focusing these buttons.
        for toolbar_button in self.toolbar.findChildren(QToolButton):
            toolbar_button.setFocusPolicy(Qt.NoFocus)

        #FIXME: For maintainability, refactor this as follows:
        #
        #* Remove the "self.set_filename_signal.emit('')" call from the
        #  "guisimconf" submodule.
        #* Define a new QBetseeSimConf.unload() method, called below. This
        #  method should internally perform the equivalent of:
        #    self.set_filename_signal.emit('')
        #* Expand the following if conditional to resemble:
        #    if self._sim_conf_filename is not None:
        #        self.sim_conf.load(self._sim_conf_filename)
        #    else:
        #        self.sim_conf.unload()

        # If opening an initial simulation configuration file, do so as this
        # method's last logic (i.e., *AFTER* all finalization performed above).
        if self._sim_conf_filename is not None:
            self.sim_conf.load(self._sim_conf_filename)

    # ..................{ EVENTS                             }..................
    def closeEvent(self, event: QCloseEvent) -> None:
        '''
        Event handler handling the passed close event signifying a user-driven
        request to close this main window and exit the current application.

        See Also
        ----------
        :meth:`QObject.destroyed`
            Slot whose signals are signalled immediately *before* that object
            and all children objects of that parent object are destroyed.
        :meth:`QGuiApplication::lastWindowClosed`
            Slot whose signals are signalled immediately *before* the last main
            window (i.e., this singleton) and all children objects of that
            window are destroyed.
        '''

        # Log this closure.
        logs.log_info('Finalizing PySide2 UI...')

        # If either...
        if (
            # This window has yet to be fully initialized.
            getattr(self, 'sim_conf', None) is None or
            # This window has been fully initialized *AND* the user
            # interactively confirmed saving all unsaved changes if any for the
            # currently open simulation configuration if any.
            self.sim_conf.save_if_dirty()
        ):
            # Store application-wide settings *BEFORE* closing this window.
            self.signaler.store_settings_signal.emit()

            # Unset the global exposing this main window, minimizing subtle
            # garbage collection issues during application destruction.
            guiappwindow.unset_main_window()

            # Accept this request, thus finalizing the closure of this window.
            # To ensure superclass handling is performed, call the superclass
            # implementation rather than event.accept().
            super().closeEvent(event)
        # Else, refuse this request, preventing this window from being closed.
        # Well, the window manager typically ignores us and closes the window
        # anyway... but, hey. If it's laptop battery life or us, we've gotta go.
        else:
            event.ignore()

    # ..................{ SLOTS ~ sim conf                   }..................
    @Slot(str)
    def set_sim_conf_filename(self, sim_conf_filename: StrOrNoneTypes) -> None:
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
    def set_sim_conf_dirty(self, is_sim_conf_dirty: bool) -> None:
        '''
        Slot invoked on the currently open simulation configuration associated
        with the main window either receiving new unsaved changes (in which case
        this boolean is ``True``) *or* having just been saved (in which case
        this boolean is ``False``).

        Parameters
        ----------
        is_sim_conf_dirty : bool
            ``True`` only if a simulation configuration is currently open *and*
            this configuration is **dirty** (i.e., has unsaved changes).
        '''

        # Set the modification state of this window to correspond to the
        # modification state of this simulation configuration, an operation that
        # has platform-specific effects usually including appending an asterisk
        # to the current window title.
        self.setWindowModified(is_sim_conf_dirty)

    # ..................{ GETTERS                            }..................
    @type_check
    def get_widget(self, widget_name: str) -> QWidget:
        '''
        Widget with the passed name directly owned by this main window if such a
        widget exists *or* raise an exception otherwise.

        The Qt (Creator|Designer)-managed ``.ui`` file underlying this window
        declares most of this application's widgets as public instance variables
        of this window, whose variable names are these widget's Qt-specific
        object names. This function provides dynamica access to these windows in
        a safe manner raising human-readable exceptions.

        Caveats
        ----------
        This function is principally intended for use cases in which this widget
        is known only at runtime. Widgets known at development time may instead
        be statically retrieved as public instance variables of this window.

        Parameters
        ----------
        widget_name : str
            Name of the widget to be retrieved.

        Returns
        ----------
        QWidget
            This widget.

        Raises
        ----------
        BetseePySideWindowException
            If this window directly owns no such widget.
        '''

        # Widget with this name if any *OR* "None" otherwise.
        widget = self.get_widget_or_none(widget_name)

        # If no such widget exists, raise an exception.
        if widget is None:
            raise BetseePySideWindowException(
                'Qt (Creator|Designer)-managed widget "{}" not found.'.format(
                    widget_name))

        # Return this widget.
        return widget


    @type_check
    def get_widget_or_none(self, widget_name: str) -> QWidgetOrNoneTypes:
        '''
        Widget with the passed name directly owned by this main window if such a
        widget exists *or* ``None`` otherwise.

        Parameters
        ----------
        widget_name : str
            Name of the widget to be retrieved.

        Returns
        ----------
        QWidgetOrNoneTypes
            This widget if any *or* ``None`` otherwise.

        See Also
        ----------
        :func:`get_widget`
            Further details.
        '''

        # All that glitters is not gold.
        return getattr(self, widget_name, None)

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
        Resize this window to consume all available screen space.

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
