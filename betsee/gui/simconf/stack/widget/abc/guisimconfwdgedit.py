#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all editable simulation configuration widget subclasses
instantiated in pages of the top-level stack.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Slot
from betse.lib.yaml.abc.yamlabc import YamlABCOrNoneTypes
from betse.lib.yaml.yamlalias import YamlAliasABC
from betse.util.io.log import logs
from betse.util.type.descriptor.datadescs import DataDescriptorBound
from betse.util.type.types import type_check, ClassOrNoneTypes
from betsee.guiexception import BetseePySideWidgetException
from betsee.util.widget.abc.guiwdgabc import QBetseeEditWidgetMixin

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeSimConfEditWidgetMixin(QBetseeEditWidgetMixin):
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

        # Mandatory parameters.
        #
        # To avoid circularity from the "QBetseeSimConf" class importing the
        # "QBetseeMainWindowConfig" class importing the "betsee_ui" submodule
        # importing instances of this class, this type is validated dynamically.
        sim_conf: 'betsee.gui.simconf.guisimconf.QBetseeSimConf',
        sim_conf_alias: YamlAliasABC,

        # Optional parameters.
        sim_conf_alias_parent: YamlABCOrNoneTypes = None,
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
        sim_conf_alias_parent : YamlABCOrNoneTypes
            YAML-backed simulation subconfiguration whose class declares the
            passed data descriptor. Defaults to ``None``, in which case this
            parameter defaults to ``sim_conf.p`` (i.e., the top-level
            YAML-backed simulation configuration).

        See Also
        ----------
        :meth:`QBetseeWidgetMixinSimConf.init`
            Further details.
        '''

        # Initialize our superclass.
        super().init()

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Initializing editable widget "%s"...', self.obj_name)

        # If no parent simulation subconfiguration was passed, default to the
        # the top-level simulation configuration.
        if sim_conf_alias_parent is None:
            sim_conf_alias_parent = sim_conf.p

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
            obj=sim_conf_alias_parent, data_desc=sim_conf_alias)

        # Type(s) required by this data descriptor if any or "None" otherwise.
        self._sim_conf_alias_type = sim_conf_alias.expr_alias_cls

        # If these type(s) are unsupported by this subclass, raise an exception.
        self._die_if_sim_conf_alias_type_invalid()

        # Populate this widget when opening a simulation configuration.
        self._sim_conf.set_filename_signal.connect(self._set_filename)

    # ..................{ SUBCLASS ~ optional                }..................
    # Subclasses may optionally reimplement the following methods.

    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:
        '''
        Superclass of all low-level values defined by the simulation
        configuration associated with this widget if this widget is strictly
        constrained to values of only a single type *or* ``None`` otherwise
        (i.e., if this widget loosely displays values satisfying any one of
        several different types).

        By default, this method returns ``None``.

        Caveats
        ----------
        This low-level type is simulation configuration-specific and hence
        distinct from the high-level type(s) of all :mod:`PySide2`-specific
        scalar values displayed by this widget. See the
        :meth:`QBetseeSimConfEditScalarWidgetMixin.widget_value` property for
        discussion of the distinction between these two related types.
        '''

        return None


    def _die_if_sim_conf_alias_type_invalid(self) -> None:
        '''
        Raise an exception if the types of low-level values exposed by the
        simulation configuration alias associated with this widget are
        unsupported by this widget's subclass.
        '''

        # If this widget is *NOT* constrained to values of only a single type,
        # silently noop. In this case, the subclass is required to manually
        # validate these values.
        if self._sim_conf_alias_type_strict is None:
            return
        # Else, this widget is constrained to values of only a single type.

        # True only if this widget is incompatible with this alias.
        is_sim_conf_alias_type_invalid = None

        # This widget is incompatible with this alias if the latter accepts
        # either:
        #
        # * Multiple types excluding this single type.
        # * A single type incompatible with this single type.
        if self._sim_conf_alias_type is tuple:
            is_sim_conf_alias_type_invalid = (
                self._sim_conf_alias_type_strict not in
                self._sim_conf_alias_type)
        else:
            is_sim_conf_alias_type_invalid = not issubclass(
                self._sim_conf_alias_type,
                self._sim_conf_alias_type_strict)

        # If this widget is incompatible with this alias, raise an exception.
        if is_sim_conf_alias_type_invalid:
            raise BetseePySideWidgetException(QCoreApplication.translate(
                'QBetseeSimConfEditWidgetMixin',
                'Widget "{0}" YAML alias type {1!r} != {2!r} '
                '(i.e., expected a type compatible with {2!r} '
                'but received an incompatible type {1!r}).'.format(
                    self.obj_name,
                    self._sim_conf_alias_type,
                    self._sim_conf_alias_type_strict,)))

    # ..................{ PROPERTIES                         }..................
    @property
    def _is_sim_open(self) -> bool:
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
        filename : str
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
            'editable widget "%s" to "%r"...', self.obj_name, is_dirty)

        # Update the dirty state for this simulation configuration.
        self._sim_conf.set_dirty_signal.emit(is_dirty)
