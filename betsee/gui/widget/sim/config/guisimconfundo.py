#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based object encapsulating simulation configuration state.
'''

#FIXME: Add support for Qt's command pattern-based "QUndoStack". It's critical
#we do this *BEFORE* implementing the application, as adhering to the command
#pattern up-front will substantially simplify our life down-the-road. To do so,
#note that:
#
#* The undo stack should be initialized in the _init() method as follows:
#
#    from PySide2.QtGui import QKeySequence
#    from PySide2.QtWidgets import QUndoStack
#
#    self._undo_stack = QUndoStack(self)
#
#* We'll need to replace our existing hard-coded "action_undo" and "action_redo"
#  actions in Qt Creator with dynamically created actions ala:
#
#    self._undo_action = self._undo_stack.createUndoAction(
#        self, QCoreApplication.translate('QBetseeSimConfig', '&Undo %1'))
#    self._undo_action.setShortcuts(QKeySequence.Undo)
#
#    self._redo_action = self._undo_stack.createRedoAction(
#        self, QCoreApplication.translate('QBetseeSimConfig', '&Redo %1'))
#    self._redo_action.setShortcuts(QKeySequence.Redo)
#
#* When the document is saved to disk, the undo stack should be marked as clean:
#
#     self._undo_stack.setClean()
#
#* Whenever the undo stack returns to the clean state through undoing and
#  redoing commands, it emits the signal cleanChanged(). This signal should be
#  connected to a slot simply emitting our more general-purpose
#  "update_is_sim_conf_dirty_signal".
#* Design a new ""QBetseeSimConfigUndoCommandABC" base class. This is getting
#  cumbersome fast, so we probably want to:
#  * Create a new "betsee.gui.widget.sim.config.undo" subpackage.
#  * Shift this "guisimconfundo" submodule into this subpackage.
#  * Create a new "guisimconfundocmd" submodule in this subpackage, to which
#    this base class and all subclasses described below should be added.
#* Connect all applicable edit signals of editable form widgets contained within
#  the stack widget to corresponding slots (probably defined on this object),
#  each internally pushing an instance of the corresponding subclass defined by
#  the "betsee.util.type.psdundo" submodule onto this undo stack.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QSize  # Signal, Slot
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QUndoStack
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.exceptions import BetseePySideMenuException
from betsee.gui.widget.guimainwindow import QBetseeMainWindow
from betsee.gui.widget.sim.config.guisimconf import QBetseeSimConfig

# ....................{ CLASSES                            }....................
class QBetseeSimConfigUndoStack(QUndoStack):
    '''
    :class:`QUndoStack`-based stack of all :class:`QBetseeSimConfigUndoCommand`
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
        sim_config: QBetseeSimConfig,
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
        sim_config: QBetseeSimConfig
            Direct parent object against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Initialize all instance variables for safety.
        self._redo_action = None
        self._undo_action = None

        # Create all actions, menu items, and icons associated with this stack.
        self._init_widgets(main_window=main_window, sim_config=sim_config)

        #FIXME: Connect these actions to appropriate "sim_config" slots and
        #signals. (See the "FIXME" above for commentary on exactly what.)


    @type_check
    def _init_widgets(
        self,
        main_window: QBetseeMainWindow,
        sim_config: QBetseeSimConfig,
    ) -> None:
        '''
        Create all actions, menu items, and icons associated with this stack.

        Design
        ----------
        To synchronize the state and text of these actions with the contents of
        this stack, these actions *must* be created by calling the
        :meth:`createUndoAction` and :meth:`createRedoAction` methods. Since Qt
        Designer lacks support for doing so, this method does so manually.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget.
        sim_config: QBetseeSimConfig
            Direct parent object against which to initialize this object.
        '''

        # Log this initialization.
        logs.log_debug('Fabricating undo stack widgets...')

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

        #FIXME: Is embedding a synopsis of the commands to be undone and redone
        #by these actions in these action names feasible? Documentation for the
        #following methods suggests that suffixing each action name by " %1"
        #suffices; unsurprisingly, doing so appears to have no effect. *sigh*

        # Redo action synchronized with the contents of this stack.
        self._redo_action = self.createRedoAction(
            sim_config, QCoreApplication.translate(
                'QBetseeSimConfigUndoStack', '&Redo'))
        self._redo_action.setShortcuts(QKeySequence.Redo)
        self._redo_action.setIcon(redo_icon)
        self._redo_action.setObjectName('action_redo')

        # Undo action synchronized with the contents of this stack.
        self._undo_action = self.createUndoAction(
            sim_config, QCoreApplication.translate(
                'QBetseeSimConfigUndoStack', '&Undo'))
        self._undo_action.setIcon(undo_icon)
        self._undo_action.setObjectName('action_undo')
        self._undo_action.setShortcuts(QKeySequence.Undo)

        # List of all actions in the "Edit" menu.
        menu_edit_actions = main_window.menu_edit.actions()

        # First action in the "Edit" menu. As a fallback in the event this menu
        # contains no actions, this action intentionally defaults to a
        # placeholder integer instructing subsequent insertions to simply append
        # to this menu.
        #
        # While this should never happen, never is the enemy of reason.
        first_action = 0

        # If at least one such action exists...
        if menu_edit_actions:
            # First such action.
            first_action = menu_edit_actions[0]

            # If this action is *NOT* a separator, raise an exception.
            if not first_action.isSeparator():
                raise BetseePySideMenuException(
                    title=QCoreApplication.translate(
                        'QBetseeSimConfigUndoStack', 'Edit Menu Malformed'),
                    synopsis=QCoreApplication.translate(
                        'QBetseeSimConfigUndoStack',
                        'First "Edit" menu action '
                        '"{0}" not a separator.'.format(first_action.text())))

        # Insert these actions before this action in this menu (in order).
        main_window.menu_edit.insertAction(first_action, self._undo_action)
        main_window.menu_edit.insertAction(first_action, self._redo_action)
