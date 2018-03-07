#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level application clipboard functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Slot
from PySide2.QtWidgets import QWidget
from betsee.util.app import guiapp
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.guiexception import BetseePySideClipboardException
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.util.io import guiclipboard
from betsee.util.io.key import guifocus
from betsee.util.type.guitype import QWidgetOrNoneTypes
from betsee.util.widget.abc.guicontrolabc import QBetseeControllerABC

# ....................{ CLASSES                            }....................
class QBetseeMainClipboard(QBetseeControllerABC):
    '''
    High-level **clipboarder** (i.e., :mod:`PySide2`-based object encapsulating
    all application clipboard state).

    This state includes:

    * Whether or not an application widget capable of receiving the interactive
      keyboard input focus is currently focused.
    * Whether or not the platform-specific system clipboard's plaintext buffer
      is currently empty (i.e., contains the empty string).

    Attributes
    ----------
    _widget_focused_if_any : QWidgetOrNoneTypes
        Widget currently receiving the interactive keyboard input focus if any
        *or* ``None`` otherwise. Ideally, the
        :func:`betsee.util.io.key.guifocus.get_widget_focused` getter would be
        called as needed to query for this widget rather than classifying this
        widget. Sadly, that getter appears to raise spurious exceptions on
        attempting to query for this widget when a toolbar button (notably, the
        copy, cut, or paste buttons) is clicked. Why? Presumably due to Qt
        subtleties in which the currently focused widget is temporarily
        defocused when a toolbar button is clicked -- regardless of that
        button's focus policy. In short, Qt issues.

    Attributes (Actions)
    ----------
    _action_copy : QAction
        Alias of the :attr:`QBetseeMainWindow.action_copy` action.
    _action_cut : QAction
        Alias of the :attr:`QBetseeMainWindow.action_cut` action.
    _action_paste : QAction
        Alias of the :attr:`QBetseeMainWindow.action_paste` action.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this clipboarder.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._action_copy  = None
        self._action_cut   = None
        self._action_paste = None
        self._widget_focused_if_any = None


    @type_check
    def init(self, main_window: QBetseeMainWindow) -> None:
        '''
        Initialize this clipboarder, owned by the passed main window widget.

        This method connects all relevant signals and slots of *all* widgets
        (including the main window, top-level widgets of that window, and leaf
        widgets distributed throughout this application) whose internal state
        pertains to the high-level state of the system clipboard.

        To avoid circular references, this method is guaranteed to *not* retain
        references to this main window on returning. References to child widgets
        (e.g., actions) of this window may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Log this initialization.
        logs.log_debug('Sanitizing system clipboard state...')

        # Classify actions subsequently required by this object. Since this main
        # window owns this object, since weak references are unsafe in a
        # multi-threaded GUI context, and since circular references are bad,
        # this object does *NOT* retain a reference to this main window.
        self._action_copy  = main_window.action_copy
        self._action_cut   = main_window.action_cut
        self._action_paste = main_window.action_paste

        # Connect each such action to this object's corresponding slot.
        self._action_copy.triggered.connect(
            self._copy_widget_focused_selection_to_clipboard)
        self._action_cut.triggered.connect(
            self._cut_widget_focused_selection_to_clipboard)
        self._action_paste.triggered.connect(
            self._paste_clipboard_to_widget_focused_selection)
        # logs.log_debug('Wiring everything up...')

        # Application singleton, localized to avoid retaining references..
        gui_app = guiapp.get_app()

        # System clipboard.
        clipboard = guiclipboard.get_clipboard()

        # Connect all relevant application-wide slots to corresponding signals
        # on this main window. Since this application strictly adheres to the
        # SDI metaphor, there exists a one-to-one correspondence between this
        # application and this object. (That is, this application always
        # contains exactly one object of this type.)
        gui_app.focusChanged.connect(self._widget_focus_set)
        clipboard.dataChanged.connect(self._clipboard_text_set)

        # Set the state of all widgets dependent upon this simulation
        # configuration state *AFTER* connecting all relavant signals and slots.
        # Initially, no widget has yet to be focused.
        self._widget_focus_set(None, None)

    # ..................{ SLOTS ~ state                      }..................
    #FIXME: Is this slot's macOS-specific caveat (see docstring below) actually
    #an issue? Only if Qt actually ignores rather than defers clipboard changes
    #that occur when this application is *NOT* the active application. In that
    #case, we'll need to also define a new slot connecting to the application
    #activation signal (...whatever that is) manually invoking this slot.

    @Slot()
    def _clipboard_text_set(self) -> None:
        '''
        Slot signalled when any text is copied or cut into the system
        clipboard's plaintext buffer by any application in the current windowing
        session (including the current application).

        Caveats
        ----------
        The slot is signalled in a somewhat deferred manner on macOS. To quote
        the documentation for the :attr:`QClipboard.dataChanged` signal:

             On macOS and with Qt version 4.3 or higher, clipboard changes made
             by other applications will only be detected when the application is
             activated.
        '''

        # Currently focused widget if any or None otherwise.
        widget_focused_if_any = guifocus.get_widget_focused_or_none()

        # Update the state of all clipboard-dependent actions with this widget.
        self._widget_focus_set(widget_focused_if_any, widget_focused_if_any)


    @Slot(QWidget, QWidget)
    def _widget_focus_set(
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
            # Log this focus change.
            # from betsee.util.widget.abc import guiwdgabc
            # logs.log_debug(
            #     'Changing focus from %s to %s...',
            #     guiwdgabc.get_label(widget_focused_old),
            #     guiwdgabc.get_label(widget_focused_new))

            # Classify this widget for subsequent lookup *BEFORE* calling the
            # _is_widget_clipboardable() method.
            self._widget_focused_if_any = widget_focused_new

            # True only if the currently focused widget is an
            # application-specific editable widget transparently supporting
            # copying, cutting, and pasting into and from the system clipboard.
            is_widget_focused_clipboardable = (
                self._is_widget_focused_clipboardable())

            # Enable or disable actions requiring such a widget to be focused.
            self._action_copy.setEnabled(is_widget_focused_clipboardable)
            self._action_cut .setEnabled(is_widget_focused_clipboardable)

            # Enable or disable actions requiring such a widget to be focused
            # *AND* the system clipboard's plaintext buffer to be non-empty.
            #
            # This overly simplistic logic would typically invite
            # desynchronization issues. Namely, if this buffer is currently
            # empty but subsequently copied or cut into with a non-empty string
            # by any application (including the current application), the state
            # of this action would be desynchronized from the state of this
            # buffer. To circumvent these issues, the _clipboard_text_set() slot
            # defers to this slot on each change to the state of this buffer and
            # hence guarantees this logic to be reevaluated as needed.
            self._action_paste.setEnabled(
                is_widget_focused_clipboardable and
                guiclipboard.is_clipboard_text())
        # If an exception is raised, avoid infinite recursion in the Qt event
        # loop by permanently disconnecting this slot from its corresponding
        # signal *BEFORE* this exception is propagated up the callstack. While
        # slightly destructive, this is the least-worst option.
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
        # * Call the qApp.blockSignals() method, preventing the "QApplication"
        #   singleton from signalling *ANY* other slots -- which is even more
        #   heavy-handed and hence undesirable than the current approach.
        except:
            # Application singleton, localized to avoid retaining references..
            gui_app = guiapp.get_app()

            # Disconnect this signal from this slot... *PERMANENTLY.*
            gui_app.focusChanged.disconnect(self._widget_focus_set)

            # Propagate this exception up the callstack.
            raise

    # ..................{ SLOTS ~ action                     }..................
    @Slot()
    def _copy_widget_focused_selection_to_clipboard(self) -> None:
        '''
        Slot invoked in response to a user-driven request to copy the
        currently focused widget's **current selection** (i.e., currently
        selected subset of this widget's value(s)) to the system clipboard,
        silently replacing the prior contents if any.
        '''

        # If no clipboardable widget is currently focused, raise an exception.
        self._die_unless_widget_focused_clipboardable()

        # Log this copy.
        logs.log_debug(
            'Copying widget "%s" selection to clipboard...',
            self._widget_focused_if_any.obj_name)

        # Copy this widget's current selection to the clipboard.
        self._widget_focused_if_any.copy_selection_to_clipboard()


    @Slot()
    def _cut_widget_focused_selection_to_clipboard(self) -> None:
        '''
        Slot invoked in response to a user-driven request to **cut** (i.e., copy
        and then remove as a single atomic operation) the currently focused
        widget's **current selection** (i.e., currently selected subset of this
        widget's value(s)) to the clipboard's plaintext buffer, silently
        replacing the prior contents if any.
        '''

        # If no clipboardable widget is currently focused, raise an exception.
        self._die_unless_widget_focused_clipboardable()

        # Log this cut.
        logs.log_debug(
            'Cutting widget "%s" selection to clipboard...',
            self._widget_focused_if_any.obj_name)

        # Cut this widget's current selection to the clipboard.
        self._widget_focused_if_any.cut_selection_to_clipboard()


    @Slot()
    def _paste_clipboard_to_widget_focused_selection(self) -> None:
        '''
        Slot invoked in response to a user-driven request to paste the contents
        of the system clipboard over the currently focused widget's **current
        selection** (i.e., currently selected subset of this widget's value(s)),
        silently replacing the prior selection if any.
        '''

        # If no clipboardable widget is currently focused, raise an exception.
        self._die_unless_widget_focused_clipboardable()

        # Log this paste.
        logs.log_debug(
            'Pasting clipboard over widget "%s" selection...',
            self._widget_focused_if_any.obj_name)

        # Paste the clipboard over this widget's current selection.
        self._widget_focused_if_any.paste_clipboard_to_selection()

    # ..................{ EXCEPTIONS                         }..................
    def _die_unless_widget_focused_clipboardable(self) -> None:
        '''
        Raise an exception unless an application-specific widget transparently
        supporting copying, cutting, and pasting into and from the system
        clipboard is currently focused.

        Raises
        ----------
        BetseePySideFocusException
            If *no* widget is currently focused.
        BetseePySideClipboardException
            If a widget is currently focused but this widget is *not* an
            application-specific editable widget supporting clipboard operation.
        '''

        # If this widget is *NOT* an application-specific editable widget, raise
        # an exception.
        if not self._is_widget_focused_clipboardable():
            raise BetseePySideClipboardException(QCoreApplication.translate(
                'QBetseeMainClipboard',
                'Focused widget "{0}" not clipboardable (i.e., not '
                'an instance of "QBetseeEditWidgetMixin" '
                'whose "is_clipboardable" property is True).'.format(
                    self._widget_focused_if_any)))

    # ..................{ TESTERS                            }..................
    @type_check
    def _is_widget_focused_clipboardable(self) -> bool:
        '''
        ``True`` only if the currently focused widget (if any) is an
        application-specific editable widget transparently supporting copying,
        cutting, and pasting into and from the system clipboard.

        Returns
        ----------
        bool
            ``True`` only if this widget is an application-specific
            clipboardable widget.
        '''

        # Avoid circular import dependencies.
        from betsee.util.widget.abc.guiclipboardabc import (
            QBetseeClipboardWidgetMixin)

        # Return True if the currently focused widget if any is clipboardable.
        return isinstance(
            self._widget_focused_if_any, QBetseeClipboardWidgetMixin)
