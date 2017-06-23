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

# ....................{ IMPORTS                            }....................
# Accessing attributes of the "PySide2.QtCore.Qt" subpackage requires this
# subpackage to be imported directly. Attributes are *NOT* importable from this
# subpackage, contrary to pure-Python expectation.
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from betsee import metadata
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
#FIXME: Rename to "QBetseeMainWindow" for disambiguity.

# Subclass all main window base classes declared by the above module (in order).
# While multiple inheritance typically invites complex complications (e.g.,
# diamond inheritance problem) and hence is best discouraged, these base classes
# are guaranteed *NOT* to conflict in this manner. All alternatives to this
# multiple inheritance design invite worse complications and otherwise avoidable
# annoyances. In short, this is arguably the best we can do.
#
# For further details, see the following classic PyQt treatise:
#     http://pyqt.sourceforge.net/Docs/PyQt5/designer.html
class BetseeMainWindow(*MAIN_WINDOW_BASE_CLASSES):
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

        # Customize all direct properties of this main window.
        self._init_properties()

        # Customize all abstract QAction widgets of this main window.
        self._init_actions()

        # Customize all physical top-level widgets of this main window.
        self._init_widgets()

        # Finalize the contents of this window *AFTER* customizing this content.
        self.show()

    # ..................{ INITIALIZERS ~ properties          }..................
    def _init_properties(self) -> None:
        '''
        Customize all direct properties of this main window.
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

        #FIXME: Submit an upstream issue report. This is terrible.
        #FIXME: Actually, this is a *HIGHLY* suboptimal approach. Rather than
        #manually reinstantiating all icons (which is absolutely abysmal), the
        #"guicache" submodule should instead perform a simple sed-style
        #global-search-and-replacement after the cached "betse_ui" submodule is
        #produced, reducing each line resembling:
        #
        #    # This...
        #    icon20.addPixmap(QtGui.QPixmap("://icon/open_iconic/download.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #
        #    # ... to this.
        #    icon20.addFile("://icon/open_iconic/download.svg", QtGui.QIcon.Normal, QtGui.QIcon.Off)
        #
        #Reasonably simple, yes? Certainly, doing so is ultimately simpler than
        #attempting to manually do so in this submodule.

        # Reassign all actions with corresponding SVG icons these icons. While
        # "pyside2uic" technically already does so, it does so erroneously.
        # "pyside2uic" converts SVG to raster icons in-memory. Since Qt wisely
        # refuses to scale raster icons up, small SVG icons (e.g., Open Iconic,
        # which are designed to be legible at and hence default to 8 pixels) are
        # effectively frozen to their default sizes. Since this results in
        # illegible icons, all actions having such icons *MUST* be manually
        # reassigned these icons.
        # self.action_undo.setIcon(QIcon('://icon/open_iconic/action-undo.svg'))
        # self.action_redo.setIcon(QIcon('://icon/open_iconic/action-redo.svg'))


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

        # Append all unfiltered log records to the top-level log widget in an
        # autoscrolling, non-blocking, thread-safe manner.
        psdlogconfig.log_to_text_edit(self.log_box)

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
