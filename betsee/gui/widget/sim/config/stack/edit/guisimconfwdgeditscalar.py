#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all editable scalar simulation configuration widget
subclasses instantiated in pages of the top-level stack.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Signal, Slot  # QCoreApplication
from PySide2.QtWidgets import QUndoCommand
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.io.log import logs
from betse.util.type.types import type_check  #, ClassOrNoneTypes
from betsee.gui.widget.sim.config.stack.edit.guisimconfwdgedit import (
    QBetseeSimConfEditWidgetMixin)
from betsee.util.widget.guiundocmd import QBetseeWidgetUndoCommandABC

# ....................{ MIXINS                             }....................
class QBetseeSimConfEditScalarWidgetMixin(QBetseeSimConfEditWidgetMixin):
    '''
    Abstract base class of all **editable scalar simulation configuration
    widget** (i.e., widget interactively editing scalar simulation configuration
    values stored in external YAML files) subclasses.

    In this context, the term "scalar" encompasses all widget subclasses whose
    contents reduce to a single displayed value (e.g., integer, floating point
    number, string).

    Attributes
    ----------
    _value_prev : object
        Previously displayed value of this widget cached on the completion of
        the most recent user edit (i.e., :meth:`editingFinished` signal),
        possibly but *not* necessarily reflecting this widget's current state.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this editable scalar widget mixin.
        '''

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        self._value_prev = None


    def init(self, *args, **kwargs) -> bool:

        # Initialize our superclass with all passed parameters.
        super().init(*args, **kwargs)

        # Connect all relevant signals to slots *AFTER* initializing our
        # superclass. See the superclass method for details.
        self._finalize_widget_edit_signal.connect(self._finalize_widget_edit)

    # ..................{ SUBCLASS ~ mandatory : property    }..................
    # Subclasses are required to implement the following properties.

    @property
    def undo_synopsis(self) -> str:
        '''
        Human-readable string synopsizing the operation performed by this scalar
        widget, preferably as a single translated sentence fragment.
        '''

        raise BetseMethodUnimplementedException()


    @property
    def widget_value(self) -> object:
        '''
        High-level :mod:`PySide2`-specific scalar value currently displayed by
        this scalar widget.

        Design
        ----------
        Each subclass typically implements this Python property in terms of an
        unprefixed getter method of this widget (e.g., :meth:`QLineEdit.text`).

        Caveats
        ----------
        If this value is neither of the exact type(s) required by the simulation
        configuration alias associated with this widget *nor* of a similar type
        safely convertible into such a type, the subclass *must* redefine both
        the :meth:`_get_alias_from_widget_value` and
        :meth:`_get_widget_from_alias_value` methods to convert this value to
        and from such a type.

        This high-level value is purely :mod:`PySide2`-specific and hence
        distinct from the associated low-level scalar value defined by the
        simulation configuration. In particular, these two values are typically
        but *not* necessarily of the same type.

        For example, for the :class:`QBetseeSimConfEnumComboBox` subclass:

        * The high-level :meth:`QBetseeSimConfEnumComboBox.widget_value`
          property returns an integer (i.e., the 0-based index of the currently
          selected item in that combo box).
        * The low-level :meth:`QBetseeSimConfEnumComboBox._sim_conf_alias.get`
          getter returns the enumeration member corresponding to this item.
        '''

        raise BetseMethodUnimplementedException()


    @widget_value.setter
    def widget_value(self, widget_value: object) -> None:
        '''
        Set the high-level :mod:`PySide2`-specific scalar value currently
        displayed by this scalar widget to the passed value.

        Design
        ----------
        Each subclass typically implements this Python property in terms of a
        ``set``-prefixed setter method of this widget (e.g.,
        :meth:`QLineEdit.setText`).

        To avoid infinite recursion, the superclass rather than subclass
        implementation of this setter method should typically be called.
        For the :class:`QBetseeSimConfLineEdit` subclass, for example,
        erroneously calling this subclass implementation would ensure that:

        #. On each call to the :meth:`setValue` method...
        #. Which pushes an undo command onto the undo stack...
        #. Whose `QUndoCommand.redo` method is called by that stack...
        #. Which calls the :meth:`setValue` method...
        #. Which induces infinite recursion.
        '''

        raise BetseMethodUnimplementedException()


    @property
    def _finalize_widget_edit_signal(self) -> Signal:
        '''
        Signal signalled on each finalized interactive user (but *not*
        programmatic) edit of the contents of this widget.

        The :meth:`init` method implicitly connects this signal to the
        :meth:`_finalize_widget_edit` slot.
        '''

        raise BetseMethodUnimplementedException()

    # ..................{ SUBCLASS ~ mandatory : method      }..................
    # Subclasses are required to implement the following methods.

    def _reset_widget_value(self) -> None:
        '''
        Reset the scalar value currently displayed by this scalar widget, thus
        reverting this widget to its default state divorced from an underlying
        model.

        For example, if this widget displays:

        * A string value, this method should set this value to the empty string.
        * A float value, this method should set this value to 0.0.
        * An integer value, this method should set this value to 0.
        '''

        raise BetseMethodUnimplementedException()

    # ..................{ SLOTS                              }..................
    @Slot(str)
    def _set_filename(self, filename: str) -> None:

        # Call the superclass method first.
        super()._set_filename(filename)

        # Set the value displayed by this widget to the current value of this
        # simulation configuration alias.
        self._set_widget_to_alias_value(filename)

        # Cache this value in preparation for the next edit.
        self._value_prev = self.widget_value


    @Slot()
    def _finalize_widget_edit(self) -> None:
        '''
        Slot signalled on each finalized interactive user (but *not*
        programmatic) change to the contents of this widget.

        Design
        ----------
        While *not* directly signalled on each programmatic change, this slot is
        called as a method by the
        :meth:`_set_alias_to_widget_value_if_sim_conf_open` method, which is
        called by the subclass implementation of this widget's principal setter
        method (e.g., :meth:`QLineEdit.setText`). Hence, this method is *always*
        called on each finalized widget change.
        '''

        # Log this edit.
        logs.log_debug(
            'Finalizing editable widget "%s" change...', self.object_name)

        # Value currently displayed by this widget.
        value_curr = self.widget_value

        # If this widget's contents have changed: specifically, if...
        if (
            # Prior text has been cached for this widget.
            self._value_prev is not None and
            # This prior text differs from this current text.
            self._value_prev != value_curr
        ):
            # Push an undo command onto the stack (permitting this edit to be
            # undone) *BEFORE* updating the "_value_prev" variable.
            undo_cmd = QBetseeSimConfEditScalarWidgetUndoCommand(
                widget=self, value_old=self._value_prev)
            self._push_undo_cmd_if_safe(undo_cmd)

            # Notify all connected slots that the currently open simulation
            # configuration has received new unsaved changes *AFTER* pushing an
            # undo command onto the stack. Why? Because this method detects
            # unsaved changes by deferring to the stack state.
            self._update_sim_conf_dirty()

        # Cache this widget's newly displayed value in preparation for the next
        # edit.
        self._value_prev = value_curr

    # ..................{ CONVERTERS ~ alias to widget       }..................
    def _set_alias_to_widget_value_if_sim_conf_open(self) -> None:
        '''
        Set the current value of the simulation configuration alias associated
        with this widget to this widget's displayed value if a simulation
        configuration is currently open *or* reduce to a noop otherwise.

        Design
        ----------
        This method should typically be explicitly called in the subclass
        implementation of this widget's principal setter method (e.g.,
        :meth:`QLineEdit.setText`).
        '''

        # If no simulation configuration is currently open, reduce to a noop.
        if not self._is_open:
            return

        # Value to set this alias to, coerced from this widget's current value.
        alias_value = self._get_alias_from_widget_value()

        # Set this alias' current value to this coerced value.
        self._sim_conf_alias.set(alias_value)

        # Finalize this programmatic change to the contents of this widget.
        self._finalize_widget_edit()


    def _get_alias_from_widget_value(self) -> object:
        '''
        Value displayed by this widget, coerced into a type expected by this
        simulation configuration alias.

        Design
        ----------
        The default implementation should suffice for most subclasses. However,
        subclasses for which the following test fails to validate that the value
        displayed by this widget is of the type required by this simulation
        configuration alias must override this method to do so in a
        subclass-specific manner:

            >>> isinstance(self.widget_value, self._sim_conf_alias_type)
        '''

        # Value displayed by this widget.
        alias_value = self.widget_value

        # Type(s) required by this simulation configuration alias, localized to
        # permit reduction from a tuple to non-tuple below.
        alias_type = self._sim_conf_alias_type

        # If this value is *NOT* of the type required by this simulation
        # configuration alias...
        if not isinstance(alias_value, alias_type):
            #FIXME: Non-ideal, obviously. Sadly, no better ideas come to mind.
            # If this type is an tuple of such types (e.g., "NumericTypes")
            # rather than a single type, arbitrarily coerce this value into the
            # type selected by the first item of this tuple.
            if alias_type is tuple:
                alias_type = alias_type[0]

            # Attempt to coerce this value into this type.
            alias_value = alias_type(alias_value)

        # Return this coerced value.
        return alias_value

    # ..................{ CONVERTERS ~ widget to alias       }..................
    @type_check
    def _set_widget_to_alias_value(self, filename: str) -> None:
        '''
        Set this widget's displayed value to the current value of the
        simulation configuration alias associated with this widget if a
        simulation configuration is currently open *or* clear this displayed
        value otherwise.

        Parameters
        ----------
        filename : str
            Absolute path of the currently open YAML-formatted simulation
            configuration file if any *or* the empty string otherwise (i.e., if
            no such file is open).
        '''

        # If a simulation configuration is currently open, set this widget's
        # displayed value from this alias' current value.
        if filename and self._is_open:
            self.widget_value = self._get_widget_from_alias_value()
        # Else, no simulation configuration is currently open. In this case,
        # clear this widget's displayed value.
        else:
            self._reset_widget_value()


    def _get_widget_from_alias_value(self) -> object:
        '''
        Value of the simulation configuration alias associated with this widget,
        coerced into a type displayable by this widget.

        See Also
        ----------
        :meth:`_get_alias_from_widget_value`
            Further details.
        '''

        return self._sim_conf_alias.get()

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfEditScalarWidgetUndoCommand(QBetseeWidgetUndoCommandABC):
    '''
    Undo command generically applicable to all editable scalar simulation
    configuration widgets, implementing the application and restoration of the
    scalar contents (e.g., float, integer, string) of a single such widget.

    This subclass provides functionality specific to scalar widgets, including:

    * Automatic merging of adjacent undo commands associated with the same
      scalar widget.

    Attributes
    ----------
    _value_new : object
        New value replacing the prior value of the scalar widget associated with
        this undo command.
    _value_old : object
        Prior value of the scalar widget associated with this undo command.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(
        self,
        widget: QBetseeSimConfEditScalarWidgetMixin,
        value_old: object,
        *args, **kwargs
    ) -> None:
        '''
        Initialize this undo command.

        Parameters
        ----------
        widget : QBetseeSimConfEditScalarWidgetMixin
            Scalar widget operated upon by this undo command.
        value_old : object
            Prior value of the scalar widget associated with this undo command.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Initialize our superclass with all remaining arguments.
        super().__init__(
            *args,
            widget=widget,
            synopsis=widget.undo_synopsis,
            **kwargs
        )

        # Classify all passed parameters.
        self._value_old = value_old
        self._value_new = widget.widget_value

    # ..................{ SUPERCLASS ~ mandatory             }..................
    # Mandatory superclass methods required to be redefined by each subclass.

    def undo(self) -> None:

        # Defer to our superclass first.
        super().undo()

        # Undo the prior edit. To prevent infinite recursion, notify this widget
        # that an undo command is now being applied to it.
        with self._in_undo_cmd():
            self._widget.widget_value = self._value_old

            #FIXME: This focus attempt almost certainly fails across pages. If
            #this is the case, a sane general-purpose solution would be to
            #iteratively search up from the parent of this widget to the
            #eventual page of the "QStackedWidget" object containing this widget
            #and then switch to that.
            # self._widget.setFocus(Qt.OtherFocusReason)


    def redo(self) -> None:

        # Defer to our superclass first.
        super().redo()

        # Redo the prior edit. See the undo() method for further details.
        with self._in_undo_cmd():
            self._widget.widget_value = self._value_new
            # self._widget.setFocus(Qt.OtherFocusReason)

    # ..................{ SUPERCLASS ~ optional              }..................
    # Optional superclass methods permitted to be redefined by each subclass.

    def mergeWith(self, prior_undo_cmd: QUndoCommand) -> bool:
        '''
        Attempt to merge this undo command with the passed undo command
        immediately preceding this undo command on the parent undo stack,
        returning ``True`` only if this method performed this merge.

        Specifically, this method returns:

        * ``True`` if this method successfully merged both the undo and redo
          operations applied by the prior undo command into those applied by
          this undo command, in which case the prior undo command is safely
          removable from the parent undo stack.
        * ``False`` otherwise, in which case both the prior undo command and
          this undo command *must* be preserved as is the parent undo stack.

        Parameters
        ----------
        prior_undo_cmd : QUndoCommand
            Undo command immediately preceding this undo command on the parent
            undo stack.

        Returns
        ----------
        bool
            ``True`` only if these undo commands were successfully merged.
        '''

        # If this prior undo command is either of a different type *OR*
        # associated with a different widget than this undo command, these
        # commands cannot be safely merged and failure is reported.
        if not (
            self.id() == prior_undo_cmd.id() and
            self._widget == prior_undo_cmd._widget
        ):
            return False

        # Else, these commands are safely mergeable. Do so by replacing the
        # prior value of this scalar widget stored with this undo command by the
        # prior value of this scalar widget stored with this prior undo command.
        self._value_old = prior_undo_cmd._value_old

        # Report success.
        return True
