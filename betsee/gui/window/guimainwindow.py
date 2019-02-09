#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
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
submodule is safely importable only *after* the
:mod:`betsee.lib.pyside2.cache.guipsdcache` submodule has locally created and
cached that module for the current user.
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

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.gui.window"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Accessing attributes of the "PySide2.QtCore.Qt" subpackage requires this
# subpackage to be imported directly. Attributes are *NOT* importable from this
# subpackage, contrary to pure-Python expectation.
from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QCloseEvent
from PySide2.QtWidgets import QToolButton, QWidget
from betse.util.io.log import logs
from betse.util.path import pathnames
from betse.util.type.obj import objects
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee import guimetadata
from betsee.guiexception import BetseePySideWindowException
from betsee.gui.guimainsignaler import QBetseeSignaler
from betsee.lib.pyside2 import guipsdui
from betsee.util.app import guiappwindow
from betsee.util.io import guierror
from betsee.util.io.log import guilogconf
from betsee.util.type.guitype import QWidgetOrNoneTypes

# ....................{ GLOBALS                           }....................
MAIN_WINDOW_BASE_CLASSES = guipsdui.get_ui_module_base_classes(
    ui_module_name=guimetadata.MAIN_WINDOW_UI_MODULE_NAME)
'''
Sequence of all main window base classes declared by the module whose
fully-qualified name is given by :attr:`metadata.MAIN_WINDOW_UI_MODULE_NAME`.
'''

# ....................{ CLASSES                           }....................
# Subclass all main window base classes declared by the above module (in
# order).  While multiple inheritance typically invites complex complications
# (e.g., diamond inheritance problem) and hence is best discouraged, these base
# classes are guaranteed *NOT* to conflict in this manner. All alternatives to
# this multiple inheritance design invite worse complications and otherwise
# avoidable annoyances. In short, this is arguably the best we can do.
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
    often invites complex complications (e.g., diamond inheritance) and hence
    is best discouraged, these base classes are guaranteed *not* to conflict in
    this manner. All alternatives to this multiple inheritance design invite
    worse complications and otherwise avoidable annoyances. In short, this is
    arguably the best we can do.

    Attributes (Public)
    ----------
    signaler : QBetseeSignaler
        :class:`PySide2`-based collection of various application-wide signals.
    sim_conf : QBetseeSimConf
        **Simulation configurator ** (i.e., object encapsulating high-level
        simulation configuration state).

    Attributes (Public: Widgets)
    ----------
    Note that the following instance variables are dynamically injected into
    this object's dictionary at runtime by the
    "betsee.lib.pyside2.cache.guipsdcacheui" submodule, which deserializes the
    XML-formatted "betsee.ui" file generated by Qt (Creator|Designer) into
    corresponding pure-Python logic.

    sim_conf_stack : QBetseeSimConfStackedWidget
        Simulation configuration stacked widget, interactively modifying
        settings pertaining to a single simulation configuration feature.
    sim_conf_tree : QBetseeSimConfTreeWidget
        Simulation configuration tree widget, interactively navigating and
        manipulating *all* simulation configuration features.
    sim_tab : QBetseeSimmerTabWidget
        Simulator tab widget, interactively running simulation phases of the
        currently open simulation configuration.

    Attributes (Private)
    ----------
    _clipboard : QBetseeMainClipboard
        Object encapsulating high-level application clipboard state.

    See Also
    ----------
    http://pyqt.sourceforge.net/Docs/PyQt5/designer.html
        :mod:`PyQt5`-specific documentation detailing this design.
    '''

    # ..................{ INITIALIZERS                      }..................
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
            Absolute or relative filename of the simulation configuration file
            to be opened on application startup if any *or* ``None`` otherwise
            (i.e., if no such file is to be opened on application startup).
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all remaining parameters.
        self.signaler = signaler

        # Nullify all remaining instance variables for safety.
        #
        # Note that the "sim_tab" instance variable is defined by our
        # superclass, itself statically defined by our main UI file and hence
        # "betsee.data.py.betsee_ui" submodule. For obvious reasons, this
        # instance variable must *NOT* be overridden to "None" here.
        self.sim_conf = None
        self._clipboard = None

        # Log this initialization.
        logs.log_debug('Generating main window...')

        # Customize this main window as specified by the XML-formatted UI file
        # exported by Qt Creator, including defining and configuring all
        # transitive widgets of this window. This superclass method is defined
        # by the helper base class generated by the
        # "betsee.lib.pyside2.cache.guipsdcacheui" submodule.
        self.setupUi(self)

        # Customize this main window with additional Python logic.
        self._init(sim_conf_filename)


    @type_check
    def _init(self, sim_conf_filename: StrOrNoneTypes) -> None:
        '''
        Customize this main window with additional Python logic *after*
        customizing this main window as specified by the XML-formatted UI file
        exported by Qt Creator.

        Design
        ----------
        **This method and all methods transitively called by this method may
        safely assume all other widgets to exist as instance variables of this
        widget.** This method is called by the :meth:`__init__` method *after*
        the latter calls the :meth:`setupUi` method, externally defined by the
        pregenerated :mod:`betsee.data.py.betsee_ui` submodule and forcefully
        injected into this subclass at runtime by the
        :mod:`betsee.lib.pyside2.cache.guipsdcacheui` submodule. Since the
        :meth:`setupUi` method defines and configures *all* transitive widgets
        of this main window, all widgets are safely accessible in this method.

        **Customizations implemented by this method must not be implementable
        by this UI file.** Equivalently, this method should *only* implement
        customizations requiring dynamic Python logic, which typically implies
        signals and slots. For portability, all other customizations should be
        implemented by this UI file.

        Parameters
        ----------
        sim_conf_filename : StrOrNoneTypes
            Absolute or relative filename of the simulation configuration file
            to be opened on application startup if any *or* ``None`` otherwise
            (i.e., if no such file is to be opened on application startup).
        '''

        # Initialize all widgets pertaining to the state of this simulation
        # configuration *BEFORE* connecting all relevant signals and slots
        # typically expecting these widgets to be initialized.
        self._init_widgets()
        self._init_connections()

        # Finalize the initialization of this main window *AFTER* customizing
        # all physical and abstract widgets of this window.
        self._init_end(sim_conf_filename)


    def _init_widgets(self) -> None:
        '''
        Customize all physical top-level widgets of this main window, thus
        excluding all abstract widgets (e.g., :class:`QAction`).
        '''

        # Avoid circular import dependencies.
        from betsee.gui.window.guimainclipboard import QBetseeMainClipboard
        from betsee.gui.simconf.guisimconf import QBetseeSimConf

        # Append all unfiltered log records to the top-level log widget in an
        # autoscrolling, non-blocking, thread-safe manner *BEFORE* performing
        # any subsequent logic possibly performing logging.
        guilogconf.log_to_text_edit(self.log_box)

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


    #FIXME: Implement all remaining actions.
    def _init_connections(self) -> None:
        '''
        Connect all relevant signals and slots of *all* widgets whose internal
        state pertains to the high-level state of this main window.
        '''

        # Connect custom signals to corresponding slots on this object.
        self.sim_conf.set_filename_signal.connect(self.set_sim_conf_filename)

        # Connect action signals to corresponding slots on this object.
        self.action_exit.triggered.connect(self.close)

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


    @type_check
    def _init_end(self, sim_conf_filename: StrOrNoneTypes) -> None:
        '''
        Finalize the initialization of this main window.

        This method performs all "last-minute logic" requiring all widgets of
        this window to have been fully initialized, including:

        * **Toolbar button sanitization.** Since widget initialization
          typically programmatically inserts additional buttons into the
          toolbar, sanitizing these buttons *must* be deferred until this
          method.

        Parameters
        ----------
        sim_conf_filename : StrOrNoneTypes
            Absolute or relative filename of the simulation configuration file
            to be opened on application startup if any *or* ``None`` otherwise
            (i.e., if no such file is to be opened on application startup).
        '''

        # Prevent toolbar buttons from receiving the keyboard input focus,
        # ensuring that the currently focused widget if any retains focus even
        # when the user clicks one or more of these buttons. For safety, this
        # is done *AFTER* finalizing all widgets and hence programmatically
        # inserting all remaining toolbar buttons into the toolbar.
        #
        # By default, toolbar buttons are *ALWAYS* permitted to receive focus
        # regardless of whether the toolbar containing these buttons is
        # permitted to do so (i.e., has a focus policy of "NoFocus") and
        # despite there being no demonstrable use case for focusing these
        # buttons.
        for toolbar_button in self.toolbar.findChildren(QToolButton):
            toolbar_button.setFocusPolicy(Qt.NoFocus)

        # If no simulation configuration file is to be opened on application
        # startup, default our configuration to the unloaded state.
        #
        # In either case, do so as this method's last statement (i.e., *AFTER*
        # all other finalization performed above).
        if sim_conf_filename is None:
            self.sim_conf.unload()
        # Else, such a file is to be opened on application startup. In this
        # case, default our configuration to the loaded state.
        else:
            self.sim_conf.load(sim_conf_filename)

    # ..................{ TESTERS                           }..................
    def _is_closable(self) -> bool:
        '''
        ``True`` only if this application is **safely closable** (i.e.,
        closable without incuring possible simulation data loss).

        Depending on the current state of this application, this method may
        indefinitely block until the user interactively confirms all of the
        following safety constraints:

        * That all unsaved changes (if any) are to be saved for the currently
          open simulation (if any).
        * That the currently running simulation subcommand (if any) is to be
          prematurely halted.

        Design
        ----------
        This method is intentionally implemented as a method rather than
        property to imply to callers that this method incurs side effects,
        including indefinitely blocking until receiving user confirmation.
        '''

        # If this application has yet to be fully initialized, this application
        # is safely closable. Why? By definition, an application that is only
        # partially initialized is an application that has yet to be displayed
        # to the user and hence has yet to open and hence edit a simulation.
        if (
            objects.get_attr_or_none(obj=self, attr_name='sim_conf') is None or
            objects.get_attr_or_none(obj=self, attr_name='sim_tab') is None
        ):
            return True

        #FIXME: Also interactively confirm that the currently running
        #simulation subcommand (if any) is to be prematurely halted.

        # Return true only if the user interactively confirms...
        return (
            # That all unsaved changes (if any) are to be saved for the
            # currently open simulation (if any).
            self.sim_conf.save_if_dirty()
        )

    # ..................{ EVENTS                            }..................
    def closeEvent(self, event: QCloseEvent) -> None:
        '''
        Event handler handling the passed close event signifying a user-driven
        request to close this main window and exit the current application.

        See Also
        ----------
        :meth:`QObject.destroyed`
            Slot whose signals are signalled immediately *before* this object
            and all children objects of this object are destroyed.
        :meth:`QGuiApplication::lastWindowClosed`
            Slot whose signals are signalled immediately *before* the last main
            window (i.e., this singleton) and all children objects of this
            window are destroyed.
        '''

        # Log this attempt.
        logs.log_info('Attempting PySide2 UI closure...')

        # If this application is safely closable...
        if self._is_closable():
            # Log this closure.
            logs.log_info('Performing PySide2 UI closure...')

            # Halt all currently working simulator workers if any by attempting
            # to gracefully stop each such worker if feasible or non-gracefully
            # terminating each such worker otherwise.
            self.sim_tab.halt_work()

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
        # anyway... but hey. If it's battery life or us, we gotta go.
        else:
            # Log this refusal.
            logs.log_info('Ignoring PySide2 UI closure...')

            # Refuse this closure request.
            event.ignore()

    # ..................{ SLOTS                             }..................
    #FIXME: Excise this *AFTER* this is no longer be required.
    @Slot()
    def _show_error_action_unimplemented(self) -> None:
        '''
        Display a modal message box informing the end user that the currently
        selected action has yet to be implemented.
        '''

        guierror.show_error(
            title='Action Unimplemented',
            synopsis='This action is currently unimplemented.',
        )

    # ..................{ SLOTS ~ sim conf                  }..................
    @Slot(str)
    def set_sim_conf_filename(self, sim_conf_filename: str) -> None:
        '''
        Slot signalled on both the opening of a new simulation configuration
        *and* closing of an open simulation configuration.

        Parameters
        ----------
        filename : str
            Either:

            * If the user opened a new simulation configuration file, the
              non-empty absolute filename of that file.
            * If the user closed an open simulation configuration file, the
              empty string.
        '''

        # If a simulation configuration is currently open...
        if sim_conf_filename:
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
        with the main window either receiving new unsaved changes (in which
        case this boolean is ``True``) *or* having just been saved (in which
        case this boolean is ``False``).

        Parameters
        ----------
        is_sim_conf_dirty : bool
            ``True`` only if a simulation configuration is currently open *and*
            this configuration is **dirty** (i.e., has unsaved changes).
        '''

        # Set the modification state of this window to correspond to the
        # modification state of this simulation configuration, an operation
        # that has platform-specific effects usually including appending an
        # asterisk to the current window title.
        self.setWindowModified(is_sim_conf_dirty)

    # ..................{ GETTERS                           }..................
    @type_check
    def get_widget(self, widget_name: str) -> QWidget:
        '''
        Widget with the passed name directly owned by this main window if this
        widget exists *or* raise an exception otherwise.

        The Qt (Creator|Designer)-managed ``.ui`` file underlying this window
        declares most of this application's widgets as public instance
        variables of this window, whose variable names are these widget's
        Qt-specific object names. This function provides dynamica access to
        these windows in a safe manner raising human-readable exceptions.

        Caveats
        ----------
        This function is principally intended for use cases in which this
        widget is known only at runtime. Widgets known at development time may
        instead be statically retrieved as public instance variables of this
        window.

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
        Widget with the passed name directly owned by this main window if this
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

    # ..................{ RESIZERS                          }..................
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
