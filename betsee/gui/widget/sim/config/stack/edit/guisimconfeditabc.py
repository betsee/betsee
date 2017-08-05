#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all simulation configuration-specific editable widget
subclasses.
'''

# ....................{ IMPORTS                            }....................
from betse.lib.yaml.yamlalias import YamlAliasABC
from betse.util.io.log import logs
from betse.util.type.descriptor.datadescs import DataDescriptorUnbound
from betse.util.type.types import type_check
from betsee.util.widget.guiundocmd import QBetseeUndoCommandWidgetABC
from betsee.util.widget.guiwidget import QBetseeWidgetEditMixin

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeWidgetEditMixinSimConf(QBetseeWidgetEditMixin):
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
    _sim_conf : QBetseeSimConf
        High-level state of the currently open simulation configuration, which
        depends on the state of this low-level simulation configuration widget.
    _sim_conf_alias : DataDescriptorUnbound
        high-level object encapsulating the low-level data descriptor bound to
        the simulation configuration option edited by this widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf = None
        self._sim_conf_alias = None


    @type_check
    def init(
        self,
        # To avoid circularity from the "QBetseeSimConf" class importing the
        # "QBetseeMainWindowConfig" class importing the "betsee_ui" submodule
        # importing instances of this class, this type is validated dynamically.
        sim_conf: 'betsee.gui.widget.sim.config.guisimconf.QBetseeSimConf',
        sim_conf_alias: YamlAliasABC,
    ) -> None:
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
        sim_conf : QBetseeSimConf
            High-level state of the currently open simulation configuration.
        sim_conf_alias : YamlAliasABC
            Low-level data descriptor bound to the simulation configuration
            option edited by this widget, typically a
            :class:`betse.science.params.Parameters`-specific class variable
            assigned the return value of the
            :func:`betse.science.config.confabc.yaml_alias` function.
        '''

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Initializing editable widget "%s"...', self.object_name)

        # Classify all passed parameters. Since the main window rather than this
        # state object owns this widget, retaining a reference to this state
        # object introduces no circularity and hence is safe. (That's nice.)
        self._sim_conf = sim_conf

        # Wrap the passed low-level data descriptor with a high-level wrapper.
        self._sim_conf_alias = DataDescriptorUnbound(sim_conf_alias)

        #FIXME: To associate the contents of this widget with newly opened
        #configurations, additionally:
        #
        #* Define the following new slot in this superclass:
        #    @Slot
        #    @abstractmethod
        #    def _update_from_sim_conf_alias(self) -> None:
        #* Redefine this slot in all superclasses.
        #* Connect the "self._sim_conf.set_filename_signal" signal to this slot.
        #
        #Astonishingly elegant, really, and proof positive that Qt's slots and
        #signals concept succeeds beyond my admittedly low expectations.

    # ..................{ PROPERTIES                         }..................
    #FIXME: Overly complex and inefficient. Simply define this boolean as a
    #typical instance variable in the init() method. *sigh*
    @property
    def _is_initted(self) -> bool:
        '''
        ``True`` only if this widget has been associated with an open simulation
        configuration (i.e., if the :meth:`init` method has been called).
        '''

        return self._sim_conf is not None

    # ..................{ ENABLERS                           }..................
    def _enable_sim_conf_dirty(self) -> None:
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
        if not self._is_initted:
            return

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Enabling simulation configuration dirty bit by '
            'editable widget "%s"...', self.object_name)

        # Enable the dirty state for this simulation configuration.
        self._sim_conf.set_dirty_signal.emit(True)

    # ..................{ UNDO STACK                         }..................
    @type_check
    def _push_undo_cmd_if_safe(
        self, undo_cmd: QBetseeUndoCommandWidgetABC) -> None:
        '''
        Push the passed widget-specific undo command onto the undo stack
        associated with the currently open simulation configuration.

        Parameters
        ----------
        undo_cmd : QBetseeUndoCommandWidgetABC
            Widget-specific undo command to be pushed onto this stack.
        '''

        # If an undo command is currently being applied to this widget, pushing
        # the passed undo command onto the stack would apply that command to
        # this widget in a nested manner typically provoking infinite recursion.
        # Since that would be bad, this undo command is silently ignored.
        if self.is_in_undo_cmd:
            return

        # Else, no such command is being applied. Since pushing this undo
        # command onto the stack is thus safe, do so.
        self._sim_conf.undo_stack.push(undo_cmd)
