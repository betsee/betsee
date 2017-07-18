#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all simulation configuration-specific editable widget
subclasses.
'''

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logs
from betsee.exceptions import BetseePySideWidgetException
from betsee.util.widget.psdwdg import QBetseeWidgetMixin

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeWidgetMixinSimConfigEdit(QBetseeWidgetMixin):
    '''
    Abstract base class of all **editable simulation configuration widget**
    (i.e., widget permitting one or more simulation configuration values stored
    in an external YAML file to be interactively edited) subclasses.

    Design
    ----------
    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be subclassed *first* rather than *last* in subclasses.

    Attributes
    ----------
    _sim_conf : QBetseeSimConfig
        High-level state of the currently open simulation configuration, which
        depends on the state of this low-level simulation configuration widget.
    _undo_stack : QBetseeSimConfigUndoStack
        Undo stack for the currently open simulation configuration. This
        attribute is a utility alias equivalent to :attr:`_sim_conf.undo_stack`.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf = None
        self._undo_stack = None


    # To avoid circular imports due to the "QBetseeSimConfig" class importing
    # the "QBetseeMainWindowConfig" class importing the "betsee_ui" submodule
    # importing instances of this class, this type is validated dynamically.
    def init(self, sim_conf: 'QBetseeSimConfig') -> bool:
        '''
        Initialize this widget against the passed state object.

        Design
        ----------
        Subclasses should typically override this method with a
        subclass-specific implementation that (in order):

        #. Calls this superclass implementation, which sets instance variables
           typically required by subclass slots.
        #. Connects all relevant signals and slots.

        Connecting these signals and slots earlier in the :meth:`__init__`
        method is *not* recommended, even for slots that Qt technically should
        *never* invoke at that time. Why? Because Qt actually appears to
        erroneously emit signals documented as emitted only by external user
        action (e.g., :meth:`QLineEdit.editingFinished`) on internal code-based
        action (e.g., startup construction of the main window).

        Parameters
        ----------
        sim_conf : QBetseeSimConfig
            High-level state of the currently open simulation configuration.
        '''

        # Avoid circular imports.
        from betsee.gui.widget.sim.config.guisimconf import QBetseeSimConfig

        # Validate this type.
        assert isinstance(sim_conf, QBetseeSimConfig), (
            '"{!r}" not a simulation configuration state object.'.format(
                sim_conf))

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Initializing editable widget "%s"...', self.object_name)

        # Classify all passed parameters. Since the main window rather than this
        # state object owns this widget, retaining a reference to this state
        # object introduces no circularity and hence is safe. (That's nice.)
        self._sim_conf = sim_conf
        self._undo_stack = sim_conf.undo_stack

    # ..................{ ENABLERS                           }..................
    def _enable_sim_conf_dirty(self) -> None:
        '''
        Enable the dirty state for the current simulation configuration.

        This method is intended to be called by subclass slots on completion of
        user edits to the contents of this widget. In response, this method
        notifies all connected slots that this simulation configuration has
        received new unsaved changes.

        See Also
        ----------
        :meth:`_enable_sim_conf_dirty_if_initted`
            Further details.

        Raises
        ----------
        BetseePySideWidgetException
            If the :meth:`init` method has yet to be called.
        '''

        # If this widget has yet to be initialized, raise an exception.
        if self._sim_conf is None:
            raise BetseePySideWidgetException(
                title='Widget Uninitialized',
                synopsis=(
                    'Editable widget "{0}" uninitialized '
                    '(i.e., simulation configuration not set).'
                ).format(self.object_name))

        # Else, this widget is initializedi, in which case the following enabler
        # is safely deferrable to.
        self._enable_sim_conf_dirty_if_initted()


    def _enable_sim_conf_dirty_if_initted(self) -> None:
        '''
        Enable the dirty state for the current simulation configuration if this
        widget has been initialized with such a configuration *or* noop
        otherwise.

        This method is intended to be called by subclass slots on completion of
        user edits to the contents of this widget. In response, this method
        notifies all connected slots that this simulation configuration has
        received new unsaved changes.
        '''

        # If this widget has yet to be initialized, silently noop.
        if self._sim_conf is None:
            return

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Enabling simulation configuration dirty bit by '
            'editable widget "%s"...', self.object_name)

        # Enable the dirty state for this simulation configuration.
        self._sim_conf.set_dirty_signal.emit(True)
