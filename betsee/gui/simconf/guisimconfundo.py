#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
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

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication, QSize  # Signal, Slot
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QUndoCommand, QUndoStack
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideMenuException
from betsee.gui.window.guiwindow import QBetseeMainWindow
from betsee.util.widget.abc.guiundocmdabc import QBetseeWidgetUndoCommandABC

# ....................{ SUBCLASSES                        }....................
class QBetseeSimConfUndoStack(QUndoStack):
    '''
    :class:`QUndoStack`-based stack of all :class:`QBetseeUndoCommandSimConf`
    instances signifying user-driven simulation configuration modifications and
    the capacity to undo those modifications.

    Attributes
    ----------
    _sim_conf : QBetseeSimConf
        High-level state of the currently open simulation configuration, which
        depends on the state of this low-level simulation configuration widget.

    Attributes (Actions)
    ----------
    _redo_action : QAction
        Redo action synchronized with the contents of this stack.
    _undo_action : QAction
        Undo action synchronized with the contents of this stack.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this undo stack.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf    = None
        self._redo_action = None
        self._undo_action = None


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Finalize the initialization of this undo stack, owned by the passed
        main window.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Log this initialization.
        logs.log_debug('Initializing simulation configuration undo stack...')

        # Classify attributes of this main window required by this subclass.
        self._sim_conf = main_window.sim_conf

        # Create all actions and icons associated with this undo stack.
        self._init_actions()

        # Create all items of the "Edit" menu requiring these actions.
        self._init_menu_edit(main_window)

        # Create all buttons of the main toolbar requiring these actions.
        self._init_toolbar(main_window)


    #FIXME: Connect these actions to appropriate "sim_conf" slots and
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
            Initialized application-specific :class:`QMainWindow` widget.
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
                'QBetseeSimConfUndoStack', '&Redo'))
        self._redo_action.setIcon(redo_icon)
        self._redo_action.setObjectName('action_redo')
        self._redo_action.setShortcuts(QKeySequence.Redo)

        # Undo action synchronized with the contents of this stack.
        self._undo_action = self.createUndoAction(
            self, QCoreApplication.translate(
                'QBetseeSimConfUndoStack', '&Undo'))
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
            Initialized application-specific :class:`QMainWindow` widget.
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
                    'QBetseeSimConfUndoStack',
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
            Initialized application-specific :class:`QMainWindow` widget.
        '''

        # List of all actions in the main toolbar.
        tool_bar_actions = main_window.toolbar.actions()

        # For each such action...
        for first_separator in tool_bar_actions:
            # If this action is the first separator in this toolbar, this
            # action is the desired separator.
            if first_separator.isSeparator():
                # Insert a new separator before this separator in this toolbar,
                # such that:
                #
                # * The former separator precedes the undo and redo actions.
                # * The latter separator succeeds the undo and redo actions.
                main_window.toolbar.insertSeparator(first_separator)

                # Cease searching.
                break
        # Else, this action contains no separators. In this case, default to a
        # placeholder integer instructing subsequent insertions to append to
        # this toolbar. While this edge case should never happen, never is
        # still the enemy of reason.
        else:
            first_separator = 0

        # Insert undo and redo actions before this separator in this toolbar.
        main_window.toolbar.insertAction(first_separator, self._undo_action)
        main_window.toolbar.insertAction(first_separator, self._redo_action)

    # ..................{ PUSHERS                           }..................
    @type_check
    def push_undo_cmd_if_safe(
        self, undo_cmd: QBetseeWidgetUndoCommandABC) -> None:
        '''
        Push the passed widget-specific undo command onto this undo stack.

        This method is intended to be called *only* by the
        :meth:`betsee.util.widget.mixin.guiwdgmixin.QBetseeEditWidgetMixin._push_undo_cmd_if_safe`
        method, which pushes undo commands from each editable widget onto this
        stack in a hopefully safe manner.

        Parameters
        ----------
        undo_cmd : QBetseeWidgetUndoCommandABC
            Widget-specific undo command to be pushed onto this stack.
        '''

        # If a simulation configuration is currently open, push this command
        # onto this stack.
        if self._sim_conf.is_open:  # and undo_cmd._widget._is_undo_cmd_pushable:
            self.push(undo_cmd)
        # Else, *NO* simulation configuration is currently open. In this case,
        # avoid pushing this command onto this stack with a non-fatal warning.
        else:
            logs.log_debug(
                'Ignoring undo command "%s" push request '
                '(i.e., simulation configuration not open).',
                undo_cmd.actionText())


    #FIXME: Ensure that this unsafe public method is *ONLY* every called by the
    #safe push_undo_cmd_if_safe() method. Doing so will probably require
    #validating within the body of this method that the prior callable on the
    #current call stack is the safe push_undo_cmd_if_safe() method.
    def push(self, undo_cmd: QUndoCommand) -> None:

        # Log this push *BEFORE* performing this push, for debuggability.
        logs.log_debug(
            'Pushing undo command "%s" onto stack...', undo_cmd.actionText())

        # logs.log_debug(
        #     'Action state *BEFORE*: undo (%r), redo (%r)',
        #     self._undo_action.isEnabled(),
        #     self._redo_action.isEnabled())

        # Attempt to push this undo command onto this stack.
        try:
            super().push(undo_cmd)
        # If "libshiboken" raises an overflow, convert this otherwise fatal
        # exception into a non-fatal warning. For unknown reasons,
        # "libshiboken" raises the following exception for otherwise safe
        # (i.e., non-recursive) undo command push requests on some systems:
        #
        #    [betsee] Setting widget "sim_conf_space_intra_lattice_type" alias value to <CellLatticeType.SQUARE: 2>...
        #    [betsee] Disabling editable widget "sim_conf_space_intra_lattice_type" undo command push request handling via setter...
        #    [betsee] Pushing undo command "changes to a radio button" onto stack...
        #    [betsee] Redoing changes to a radio button for widget "sim_conf_space_intra_lattice_type"...
        #    [betsee] Disabling editable widget "sim_conf_space_intra_lattice_type" undo command push request handling via noop...
        #    [betsee] /home/leycec/py/betsee/betsee/gui/simconf/guisimconfundo.py:298: RuntimeWarning: libshiboken: Overflow: Value 94379762154184 exceeds limits of type  [signed] "i" (4bytes).
        #      super().push(undo_cmd)
        #
        #    [betsee] Restoring editable widget "sim_conf_space_intra_lattice_type" undo command push request handling...
        #    [betsee] Exiting prematurely due to fatal error:
        #
        #    OverflowError
        #
        #    Traceback (most recent call last):
        #      File "/home/leycec/py/betsee/betsee/gui/simconf/stack/widget/mixin/guisimconfwdgeditscalar.py", line 322, in _set_alias_to_widget_value_if_safe
        #        self._push_undo_cmd_if_safe(undo_cmd)
        #      File "<string>", line 41, in ___push_undo_cmd_if_safe_type_checked__
        #      File "/home/leycec/py/betsee/betsee/util/widget/mixin/guiwdgeditmixin.py", line 272, in _push_undo_cmd_if_safe
        #        self._undo_stack.push_undo_cmd_if_safe(undo_cmd)
        #      File "<string>", line 14, in __push_undo_cmd_if_safe_type_checked__
        #      File "/home/leycec/py/betsee/betsee/gui/simconf/guisimconfundo.py", line 271, in push_undo_cmd_if_safe
        #        self.push(undo_cmd)
        #      File "/home/leycec/py/betsee/betsee/gui/simconf/guisimconfundo.py", line 298, in push
        #        super().push(undo_cmd)
        #
        # While such exceptions would typically be indicative of a fatal
        # application failure, this particular exception appears to be a
        # harmless (and hence ignorable) artifact of the "libshoken" binding
        # for this method.
        except OverflowError:
            logs.log_warning(
                'Harmless overflow from editable widget "%s" '
                'undo command push request detected...',
                undo_cmd._widget.obj_name)

        # logs.log_debug(
        #     'Action state *AFTER*: undo (%r), redo (%r)',
        #     self._undo_action.isEnabled(),
        #     self._redo_action.isEnabled())
