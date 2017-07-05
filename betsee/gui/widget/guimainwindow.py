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
from PySide2.QtCore import Qt
from betse.util.io.log import logs
from betsee import metadata
from betsee.util.io import psderr, psdprefs
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

    See Also
    ----------
    http://pyqt.sourceforge.net/Docs/PyQt5/designer.html
        :mod:`PyQt5`-specific documentation detailing this design.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

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

        # Initialize all PySide2-agnostic variables of this main window.
        self._init_vars()

        # Customize all PySide2-specific properties of this main window.
        self._init_props()

        # Customize all abstract QAction widgets of this main window.
        self._init_actions()

        # Customize all physical top-level widgets of this main window.
        self._init_widgets()

        # Finalize the contents of this window *AFTER* customizing this content.
        self.show()

    # ..................{ INITIALIZERS ~ properties          }..................
    def _init_vars(self) -> None:
        '''
        Initialize all :class:`PySide2`-agnostic variables of this main window.
        '''

        self._is_dirty = False
        self._is_dirty = False


    def _init_props(self) -> None:
        '''
        Customize all :class:`PySide2`-specific properties of this main window.
        '''

        #FIXME: While a sensible default, BETSEE should ideally preserve and
        #restor its prior window state if any from the most recent execution of
        #this application.

        # Expand this window to consume all available horizontal and vertical
        # screen space. Note that:
        #
        # * This does *NOT* constitute "full screen" mode, which is typically
        #   desirable only for console-oriented applications (e.g., OpenGL).
        # * This is *NOT* supported by Qt Creator and hence must be performed
        #   with Python logic here.
        # * The more convenient self.main_window.showMaximized() method is
        #   intentionally *NOT* called here, as doing so would implicitly render
        #   the entire GUI (which has yet to be fully customized) visible.
        #
        # Failing to maximize this window typically results in Qt erroneously
        # defaulting this window to an inappropriate size for the current
        # screen. On my a 1920x1080 display, for example, the default window
        # size exceeds the vertical resolution (and hence is clipped on the
        # bottom) but consumes only two-thirds of the horizontal resolution.
        self.setWindowState(Qt.WindowMaximized)

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

    # ..................{ INITIALIZERS ~ actions             }..................
    def _init_widgets(self) -> None:
        '''
        Customize all physical top-level widgets of this main window, thus
        excluding all abstract widgets (e.g., :class:`QAction`).
        '''

        # Initialize both the simulation configuration tree and stack widgets.
        self.sim_conf_tree.init(self)

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

    # ..................{ SETTINGS                           }..................
    #FIXME: This should be called *AFTER* the main window is constructed but
    #*BEFORE* that window is actually displayed.
    def _read_settings(self) -> None:
        '''
        Read application-wide settings previously written to a predefined
        application- and user-specific on-disk file by the most recent execution
        of this application if any *or* reduce to a noop otherwise.
        '''

        # Previously written application settings.
        settings = psdprefs.make_settings()

        # Read settings specific to this main window.
        settings.beginGroup('MainWindow')

        # Restore all previously written properties of this window.
        #
        # Note that there exist numerous means of doing so. While the canonical
        # means of doing so appears to be the QMainWindow.restoreGeometry() and
        # QMainWindow.restoreState() methods, QSettings documentation explicitly
        # states that:
        #
        #     "See Window Geometry for a discussion on why it is better to call
        #      QWidget::resize() and QWidget::move() rather than
        #      QWidget::setGeometry() to restore a window's geometry."
        #
        # Sadly, the "Window Geometry" article fails to actually discuss why the
        # QWidget.resize() and QWidget.move() methods are preferable to
        # QWidget.setGeometry() with respect to the main window. We do note,
        # however, that QWidget.setGeometry() documentation cautions:
        #
        #     "Warning: Calling setGeometry() inside resizeEvent() or
        #      moveEvent() can lead to infinite recursion."
        #
        # In the absence of compelling evidence, the current approach prevails.
        if settings.contains('pos'):
            self.move(settings.value('pos').toPoint())
        if settings.contains('size'):
            self.resize(settings.value('size').toSize())
        if settings.contains('isFullScreen'):
            self.setFullScreen(settings.value('isFullScreen'))

        # Cease reading settings specific to this window.
        settings.endGroup()


    #FIXME: This should be called:
    #
    #* At least immediately *BEFORE* the main window is closed.
    #* Ideally incrementally during the application life cycle to prevent
    #  settings from being lost if the application fails to close gracefully.
    #  "QTimer" is probably our friends, here.
    def _write_settings(self) -> None:
        '''
        Write application-wide settings to a predefined application- and
        user-specific on-disk file, which the next execution of this application
        will read and restore on startup.
        '''

        # Currently written application settings if any.
        settings = psdprefs.make_settings()

        # Write settings specific to this main window.
        settings.beginGroup('MainWindow')
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())
        settings.setValue('isFullScreen', self.isFullScreen())
        settings.endGroup()
