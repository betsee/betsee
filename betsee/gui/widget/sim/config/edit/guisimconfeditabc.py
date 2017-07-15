#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all simulation configuration-specific editable widget
subclasses.
'''

# ....................{ IMPORTS                            }....................

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeSimConfigEditWidgetMixin(object):
    '''
    Abstract base class of all **editable simulation configuration widget**
    (i.e., widgets permitting one or more simulation configuration values stored
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

        # Classify all passed parameters. Since the main window rather than this
        # state object owns this widget, retaining a reference to this state
        # object introduces no circularity and hence is safe. (That's nice.)
        self._sim_conf = sim_conf
        self._undo_stack = sim_conf.undo_stack

    # ..................{ ENABLERS                           }..................
    def _enable_sim_conf_dirty(self) -> None:
        '''
        Enable the dirty staate for the current simulation configuration.

        This method is intended to be called by subclass slots on completion of
        user edits to the contents of this widget. In response, this method
        notifies all connected slots that this simulation configuration has
        received new unsaved changes.
        '''

        self._sim_conf.set_dirty_signal.emit(True)
