#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all editable simulation configuration widget subclasses
instantiated in pages of the top-level stack.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot
from betse.lib.yaml.yamlalias import YamlAliasABC
from betse.util.io.log import logs
from betse.util.type.descriptor.datadescs import DataDescriptorBound
from betse.util.type.types import type_check  #, CallableTypes
from betsee.util.widget.guiwdg import QBetseeWidgetEditMixin

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeWidgetEditSimConfMixin(QBetseeWidgetEditMixin):
    '''
    Abstract base class of all **editable simulation configuration widget**
    (i.e., widget interactively editing simulation configuration values stored
    in external YAML files) subclasses.

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
    _sim_conf_alias : DataDescriptorBound
        high-level object wrapping the low-level data descriptor of the
        :class:`betse.science.parameters.Parameters` class, itself wrapping the
        lower-level simulation configuration option edited by this widget.
    _sim_conf_alias_type : ClassOrNoneTypes
        Class or tuple of classes that the value to which
        :attr:`_sim_conf_alias` evaluates is required to be an instance of if
        any *or* ``None`` otherwise.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf = None
        self._sim_conf_alias = None
        self._sim_conf_alias_type = None


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
        Finalize the initialization of this widget.

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

        See Also
        ----------
        :meth:`QBetseeWidgetMixinSimConf.init`
            Further details.
        '''

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Initializing editable widget "%s"...', self.object_name)

        # Set the undo stack to which this widget pushes undo commands *BEFORE*
        # connecting signals to slots pushing such commands.
        self._set_undo_stack(sim_conf.undo_stack)

        # Classify all passed parameters. Since the main window rather than this
        # state object owns this widget, retaining a reference to this state
        # object introduces no circularity and hence is safe. (That's nice.)
        self._sim_conf = sim_conf

        # Wrap the passed low-level data descriptor with a high-level wrapper
        # bound to the "Parameters" instance associated with this GUI.
        self._sim_conf_alias = DataDescriptorBound(
            obj=sim_conf.p, data_desc=sim_conf_alias)

        # Type(s) required by this data descriptor if any or "None" otherwise.
        self._sim_conf_alias_type = sim_conf_alias.expr_alias_cls

        # Populate this widget when opening a simulation configuration.
        self._sim_conf.set_filename_signal.connect(self._set_filename)

    # ..................{ PROPERTIES                         }..................
    @property
    def _is_open(self) -> bool:
        '''
        ``True`` only if a simulation configuration file is currently open.
        '''

        return self._sim_conf is not None and self._sim_conf.is_open

    # ..................{ SLOTS                              }..................
    @Slot(str)
    def _set_filename(self, filename: str) -> None:
        '''
        Slot signalled on both the opening of a new simulation configuration
        and closing of an open simulation configuration.

        Design
        ----------
        Subclasses are recommended to override this method by (in order):

        #. Calling this superclass implementation.
        #. If this filename is non-empty, populating this widget's contents with
           the current value of the simulation configuration alias associated
           with this widget.

        Parameters
        ----------
        filename : StrOrNoneTypes
            Absolute path of the currently open YAML-formatted simulation
            configuration file if any *or* the empty string otherwise (i.e., if
            no such file is open).
        '''

        # Undo commands are safely pushable from this widget *ONLY* if a
        # simulation configuration is currently open.
        self.is_undo_cmd_pushable = bool(filename)

    # ..................{ ENABLERS                           }..................
    def _update_sim_conf_dirty(self) -> None:
        '''
        Update the dirty state for the current simulation configuration if this
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

        # "True" only if the undo stack is in the dirty state.
        is_dirty = self._is_undo_stack_dirty()

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Setting simulation configuration dirty bit from '
            'editable widget "%s" to "%r"...', self.object_name, is_dirty)

        # Update the dirty state for this simulation configuration.
        self._sim_conf.set_dirty_signal.emit(is_dirty)
