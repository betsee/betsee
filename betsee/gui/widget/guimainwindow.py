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

#FIXME: An application icon should be set. Of course, we first need to create an
#application icon - ideally in SVG format. For exhaustive details on portability
#issues, see the well-written "Setting the Application Icon" article.

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
from betsee import guimetadata
from betsee.gui.guisignal import QBetseeSignaler
from betsee.util.io import guierr
from betsee.util.io.key import guifocus
from betsee.util.io.log import guilogconf
from betsee.util.io.xml import guiui

#FIXME: Clipboard-specific imports. *sigh*
from PySide2.QtWidgets import QWidget
from betsee.util.app.guiapp import GUI_APP
from betsee.util.io import guiclipboard
from betsee.util.type.guitypes import QWidgetOrNoneTypes

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

    Attributes (Private)
    ----------
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

        # Customize all abstract QAction widgets of this main window.
        self._init_actions()

        # Customize all physical top-level widgets of this main window.
        self._init_widgets()

        # Customize the application object with respect to this main window.
        self._init_app()

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
            self.action_copy,
            self.action_cut,
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

        # Associate QAction signals with Python slots.
        self.action_exit.triggered.connect(self.close)


    def _init_actions_edit(self) -> None:
        '''
        Customize all QAction widgets of the top-level ``Edit`` menu.
        '''

        #FIXME: Uncomment us up once working.
        # Associate QAction signals with Python slots.
        # self.action_copy.triggered.connect(
        #     self.copy_widget_value_selected_to_clipboard)

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
        from betsee.gui.widget.sim.config.guisimconf import QBetseeSimConf

        # Initialize the status bar with a sensible startup message.
        self._show_status('Welcome to {}'.format(guimetadata.NAME))

        # Object encapsulating high-level simulation configuration state,
        # instantiated *BEFORE* initializing widgets assuming this state to
        # exist.
        self.sim_conf = QBetseeSimConf(main_window=self)

        # Initialize both the simulation configuration stack widget *BEFORE*
        # initializing the mildly higher-level sibling tree widget, which
        # assumes the former to have been initialized.
        self.sim_conf_stack.init(main_window=self)

        # Initialize the simulation configuration tree widget.
        self.sim_conf_tree.init(main_window=self)

        # If opening an initial simulation configuration file, do so *AFTER*
        # finalizing all widgets.
        if self._sim_conf_filename is not None:
            self.sim_conf.load(self._sim_conf_filename)

    # ..................{ INITIALIZERS ~ app                 }..................
    def _init_app(self) -> None:
        '''
        Customize the :class:`QApplication` singleton with respect to this main
        window.
        '''

        # Connect all relevant application-wide slots to corresponding signals
        # on this main window. Since this application strictly adheres to the
        # SDI metaphor, there exists a one-to-one correspondence between this
        # application and this main window. (That is, this application always
        # contains exactly one main window.)
        GUI_APP.focusChanged.connect(self._set_widget_focus)

        # Signal no widgets to currently be focused, initializing the state of
        # all actions depependent upon this focus state.
        self._set_widget_focus(None, None)

    # ..................{ EVENTS                             }..................
    def closeEvent(self, event: QCloseEvent) -> None:
        '''
        Event handler handling the passed close event signifying a user-driven
        request to close this main window and exit the current application.
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

            # Accept this request, thus finalizing the closure of this window.
            event.accept()
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

    # ..................{ SLOTS ~ widget                     }..................
    #FIXME: For maintainability:
    #
    #* Shift all of the following clipboard-specific functionality into a new
    #  "QBetseeMainClipboard" subclass of the "QObject" base class in a new
    #  "betsee.gui.widget.guimainclipboard" submodule.
    #* Instantiate an instance of that subclass in the _init() method above.
    #
    #Note that the structure of this "QBetseeMainClipboard" subclass should
    #ideally be patterned after that of the "QBetseeSimConf" subclass, which
    #serves a similar managerial role.

    @Slot(QWidget, QWidget)
    def _set_widget_focus(
        self,
        widget_focused_old: QWidgetOrNoneTypes,
        widget_focused_new: QWidgetOrNoneTypes,
    ) -> None:
        '''
        Slot signalled when an application widget loses and/or gains interactive
        keyboard input focus (e.g., due to the tab-key being pressed, this
        widget being clicked, or this main window being made active).

        The slot is signalled *after* both widgets have been notified of this
        :class:`QFocusEvent`.

        Parameters
        ----------
        widget_focused_old : QWidgetOrNoneTypes
            Previously focused widget if any *or* ``None`` otherwise.
        widget_focused_new : QWidgetOrNoneTypes
            Previously focused widget if any *or* ``None`` otherwise.
        '''

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # WARNING: This is a fundamentally fragile slot. Exceptions accidentally
        # raised by this slot's implementation may induce infinite recursion.
        # See the "except" block below for further commentary.
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # Attempt to...
        try:
            # Avoid circular import dependencies.
            from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgedit import (
                QBetseeSimConfEditWidgetMixin)

            #FIXME: *ALL* editable widgets (simulation configuration-specific or
            #not) should support copying, cutting, and pasting into and from the
            #system clipboard. Once this is the case, this test may be reduced to:
            #
            #    is_widget_focused_new_cliboardable = widget_focused_new is not None
            #
            #For this reason, this and the following slots reside in this class.
            is_widget_clipboardable = isinstance(
                widget_focused_new, QBetseeSimConfEditWidgetMixin)

            # Enable or disable actions requiring such a widget to be focused.
            self.action_copy.setEnabled(is_widget_clipboardable)
            self.action_cut .setEnabled(is_widget_clipboardable)

            #FIXME: Insufficient, as this fails to synchronize with changes to the
            #system clipboard. To do so, we'll need to define a new slot connected
            #to the existing QClipboard.dataChanged() signal. Note, however, that:
            #
            #   "On macOS and with Qt version 4.3 or higher, clipboard changes made
            #    by other applications will only be detected when the application is
            #    activated."
            #
            #Is this actually a problem? Only if Qt actually ignores rather than
            #buffers clipboard changes that occur when this application is *NOT* the
            #active application. In that case, we'll need to also define a new slot
            #connecting to the application activation signal (...whatever that is)
            #manually invoking this slot.

            # Enable or disable actions requiring such a widget to be focused
            # *AND* the system clipboard's plaintext buffer to be non-empty.
            self.action_paste.setEnabled(
                is_widget_clipboardable and guiclipboard.is_clipboard_text())
        # If an exception is raised, infinite recursion in the Qt event loop
        # mest be explicitly avoided by permanently disconnecting this slot from
        # its corresponding signal *BEFORE* this exception is propagated up the
        # callstack. While slightly destructive, this is the least-worst option.
        #
        # Failing to do so provokes the following infinite recursion:
        #
        # * This slot raises an exception.
        # * This exception is propagated up to the default exception handler.
        # * This handler displays a PySide2 widget graphically presenting this
        #   exception to the user.
        # * This widget implicitly obtains the interactive keyboard input focus.
        # * This focus change invokes the signal connected to this slot.
        # * This slot raises an exception.
        #
        # The only alternatives would be to:
        #
        # * Prevent the PySide2 widget displayed by the default exception
        #   handler from obtaining the focus -- a fragile, platform-specific,
        #   and possibly unenforceable constraint in the best case.
        # * Call the GUI_APP.blockSignals() method, preventing the "GUI_APP"
        #   object from signalling *ANY* other slots -- which is even more
        #   heavy-handed and hence undesirable than the current approach.
        except:
            # Disconnect this signal from this slot... *PERMANENTLY.*
            GUI_APP.focusChanged.disconnect(self._set_widget_focus)

            # Propagate this exception up the callstack.
            raise



    @Slot(str)
    def copy_widget_value_selected_to_clipboard(self) -> None:
        '''
        Slot invoked in response to a user-driven request to copy the currently
        selected portion of the currently focused widget's value(s) to the
        system clipboard, silently replacing the prior contents of that
        clipboard if any.
        '''

        # Currently focused widget. Since the action signalling this slot should
        # *ONLY* be enabled when a widget is currently focused, this call should
        # *NEVER* raise exceptions.
        widget_focused = guifocus.get_widget_focused()

        #FIXME: Actually do something here. The difficulty, of course, is that
        #most stock QWidget subclasses do *NOT* support the concept of
        #cut-copy-paste. The only one that appears to, in fact, is "QLineEdit".
        #For the remainder, we'll need to implement such functionality manually.
        #Consider:
        #
        #* Raise an exception unless this focused widget is an instance of the
        #  "QBetseeSimConfEditScalarWidgetMixin" base class. This implies, of
        #  course, that this action should be disabled if this is not the case.
        #* Augment this base class with the following three new methods:
        #  * copy_widget_value_selected_to_clipboard().
        #  * cut_widget_value_selected_to_clipboard().
        #  * paste_clipboard_to_widget_value_selected().
        #
        #This shouldn't be *TOO* terribly difficult -- merely tedious.

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

        # Display this temporary message with no timeout.
        self.status_bar.showMessage(text)


    def _clear_status(self) -> None:
        '''
        Remove the temporary message currently displayed in the status bar if
        any *or* reduce to a noop otherwise.

        This Any normal message was displayed prior to this temporary message being
        displayed in the status bar,
        '''

        self.status_bar.clearMessage()
