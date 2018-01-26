#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

#FIXME: Currently, entering either <Ctrl-z> or <Ctrl-Shift-z> while in an
#editable widget that takes the keyboard focus forwards these key sequence
#events to that specific widget rather than the application as a whole,
#preventing the global undo stack from being modified by keyboard. To address
#this, consider carefully:
#
#* Redefining the key sequence event handler for each editable simulation
#  configuration widget as follows:
#  * If widget.isUndoRedoEnabled() returns True, then defer to the default
#    superclass key sequence event handler for this widget. This preserves the
#    existing functionality for widgets with pending actions to be undone.
#  * Else (i.e., if this widget has no pending actions to be undone), forward
#    this key sequence event to the global application or main window widgets,
#    triggering an undo or redo from the global undo stack.
#
#For further details on installing a custom eventFilter() specifically handling
#<Ctrl-z> keyboard shortcuts from editable widgets, see the following answer:
#    https://stackoverflow.com/a/28867475/2809027

#FIXME: Whenever the undo stack returns to the clean state through undoing and
#redoing commands, it emits the signal cleanChanged(). This signal should be
#connected to a slot simply emitting our more general-purpose
#"set_dirty_signal". Hmmmm; wait. Actually, is doing so even necessary? Since
#each application of an undo or redo operation necessarily invokes an editable
#widget slot already emitting "set_dirty_signal", there appears to be no need
#for this undo stack to explicitly do so as well.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QSize  # Signal, Slot
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QUndoCommand, QUndoStack
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideMenuException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.gui.simconf.guisimconf import QBetseeSimConf

# ....................{ CLASSES                            }....................
class QBetseeUndoStackSimConf(QUndoStack):
    '''
    :class:`QUndoStack`-based stack of all :class:`QBetseeUndoCommandSimConf`
    instances signifying user-driven simulation configuration modifications and
    the capacity to undo those modifications.

    Attributes (Non-widgets)
    ----------
    _redo_action : QAction
        Redo action synchronized with the contents of this stack.
    _undo_action : QAction
        Undo action synchronized with the contents of this stack.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(
        self,
        main_window: QBetseeMainWindow,
        sim_config: QBetseeSimConf,
        *args, **kwargs
    ) -> None:
        '''
        Initialize this object, owned by the passed objects.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        sim_config: QBetseeSimConf
            Direct parent object against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Initialize all instance variables for safety.
        self._redo_action = None
        self._undo_action = None

        # Log this initialization.
        logs.log_debug('Customizing simulation configuration undo stack...')

        # Create all actions and icons associated with this undo stack.
        self._init_actions()

        # Create all items of the "Edit" menu requiring these actions.
        self._init_menu_edit(main_window)

        # Create all buttons of the main toolbar requiring these actions.
        self._init_toolbar(main_window)

        #FIXME: Connect these actions to appropriate "sim_config" slots and
        #signals. (See the "FIXME" above for commentary on exactly what.)


    @type_check
    def _init_actions(
        self,
        # main_window: QBetseeMainWindow,
        # sim_config: QBetseeSimConf,
    ) -> None:
        '''
        Create all actions and icons associated with this undo stack.

        Design
        ----------
        To synchronize the state and text of these actions with the contents of
        this undo stack, this method creates these actions by calling the
        :meth:`createUndoAction` and :meth:`createRedoAction` methods. Since Qt
        Designer lacks support for doing so, this method does so manually.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        sim_config: QBetseeSimConf
            Direct parent object against which to initialize this object.
        '''

        # Redo icon associated with this redo action.
        redo_icon = QIcon()
        redo_icon.addFile(
            ':/icon/open_iconic/action-redo.svg',
            QSize(), QIcon.Normal, QIcon.Off,)

        # Undo icon associated with this undo action.
        undo_icon = QIcon()
        undo_icon.addFile(
            ':/icon/open_iconic/action-undo.svg',
            QSize(), QIcon.Normal, QIcon.Off,)

        # Redo action synchronized with the contents of this stack.
        self._redo_action = self.createRedoAction(
            self, QCoreApplication.translate(
                'QBetseeUndoStackSimConf', '&Redo'))
        self._redo_action.setIcon(redo_icon)
        self._redo_action.setObjectName('action_redo')
        self._redo_action.setShortcuts(QKeySequence.Redo)

        # Undo action synchronized with the contents of this stack.
        self._undo_action = self.createUndoAction(
            self, QCoreApplication.translate(
                'QBetseeUndoStackSimConf', '&Undo'))
        self._undo_action.setIcon(undo_icon)
        self._undo_action.setObjectName('action_undo')
        self._undo_action.setShortcuts(QKeySequence.Undo)


    @type_check
    def _init_menu_edit(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all items of the ``Edit`` menu requiring actions previously
        created by the :meth:`_init_actions` method.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # List of all actions in the "Edit" menu.
        menu_edit_actions = main_window.menu_edit.actions()

        # First action in the "Edit" menu, guaranteed by the logic below to be
        # separator. As a fallback in the event this menu contains no actions,
        # this action intentionally defaults to a placeholder integer
        # instructing subsequent insertions to append to this menu. While this
        # edge case should never happen, never is the enemy of reason.
        first_separator = 0

        # If at least one such action exists...
        if menu_edit_actions:
            # First such action.
            first_separator = menu_edit_actions[0]

            # If this action is *NOT* a separator, raise an exception.
            if not first_separator.isSeparator():
                raise BetseePySideMenuException(QCoreApplication.translate(
                    'QBetseeUndoStackSimConf',
                    'First "Edit" menu action '
                    '"{0}" not a separator.'.format(first_separator.text())))

        # Insert undo and redo actions before this separator in this menu.
        main_window.menu_edit.insertAction(first_separator, self._undo_action)
        main_window.menu_edit.insertAction(first_separator, self._redo_action)


    @type_check
    def _init_toolbar(self, main_window: QBetseeMainWindow) -> None:
        '''
        Create all buttons of the main toolbar requiring actions previously
        created by the :meth:`_init_actions` method.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        '''

        # List of all actions in the main toolbar.
        tool_bar_actions = main_window.toolbar.actions()

        # For each such action...
        for first_separator in tool_bar_actions:
            # If this action is the first separator in this toolbar, this action
            # is the desired separator.
            if first_separator.isSeparator():
                # Insert a new separator before this separator in this toolbar,
                # such that:
                #
                # * The former separator will precede the undo and redo actions.
                # * The latter separator will succeed the undo and redo actions.
                main_window.toolbar.insertSeparator(first_separator)

                # Cease searching.
                break
        # Else, this action contains no separators. In this case, default to a
        # placeholder integer instructing subsequent insertions to append to
        # this toolbar. While this edge case should never happen, never is still
        # the enemy of reason.
        else:
            first_separator = 0

        # Insert undo and redo actions before this separator in this toolbar.
        main_window.toolbar.insertAction(first_separator, self._undo_action)
        main_window.toolbar.insertAction(first_separator, self._redo_action)

    # ..................{ PUSHERS                            }..................
    def push(self, undo_command: QUndoCommand) -> None:

        # Log this push *BEFORE* performing this push, for debuggability.
        logs.log_debug(
            'Pushing undo command "%s" onto stack...',
            undo_command.actionText())

        # logs.log_debug(
        #     'Action state *BEFORE*: undo (%r), redo (%r)',
        #     self._undo_action.isEnabled(),
        #     self._redo_action.isEnabled())

        # Push this undo command onto this stack.
        super().push(undo_command)

        # logs.log_debug(
        #     'Action state *AFTER*: undo (%r), redo (%r)',
        #     self._undo_action.isEnabled(),
        #     self._redo_action.isEnabled())
