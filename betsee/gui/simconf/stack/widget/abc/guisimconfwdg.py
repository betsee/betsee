#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all simulation configuration widget subclasses
instantiated in pages of the top-level stack.
'''

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ MIXINS                             }....................
# To avoid metaclass conflicts with the "QWidget" base class inherited by all
# widgets also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeWidgetMixinSimConf(QBetseeObjectMixin):
    '''
    Abstract base class of all **non-editable simulation configuration widget**
    (i.e., widget *not* interactively editing simulation configuration values
    stored in external YAML files) subclasses.

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
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._sim_conf = None


    @type_check
    def init(
        self,
        # To avoid circularity from the "QBetseeSimConf" class importing the
        # "QBetseeMainWindowConfig" class importing the "betsee_ui" submodule
        # importing instances of this class, this type is validated dynamically.
        sim_conf: 'betsee.gui.simconf.guisimconf.QBetseeSimConf',
    ) -> None:
        '''
        Finalize the initialization of this widget.

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
        '''

        # Log this initialization *AFTER* storing this name.
        logs.log_debug(
            'Initializing non-editable widget "%s"...', self.obj_name)

        # Classify all passed parameters. Since the main window rather than this
        # state object owns this widget, retaining a reference to this state
        # object introduces no circularity and hence is safe. (That's nice.)
        self._sim_conf = sim_conf
