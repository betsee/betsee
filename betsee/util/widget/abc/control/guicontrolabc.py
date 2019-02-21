#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **controller** (i.e., :mod:`PySide2`-based object controlling the
flow of application execution ala the standard model-view-controller (MVC)
paradigm) hierarchy.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QObject
from PySide2.QtWidgets import QMainWindow
from betse.util.type.types import type_check
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUPERCLASSES                      }....................
class QBetseeControllerABC(QBetseeObjectMixin, QObject):
    '''
    Abstract base class of all **controller** (i.e., :mod:`PySide2`-based
    object controlling the flow of application execution ala the standard
    model-view-controller (MVC) paradigm) subclasses.

    Each instance of this class is a controller encapsulating all abstract
    state (including connective logic like signals and slots) required to
    sanely display a separate physical view (i.e., widget). For integration
    with Qt concurrency and signalling, this controller is a minimal
    :class:`QObject` rather than full-fledged :class:`QWidget` instance.
    '''

    # ..................{ INITIALIZERS                      }..................
    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.window.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow, *args, **kwargs) -> None:
        '''
        Initialize this controller against the passed parent main window.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window
        may be retained, however.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this controller.

        All remaining parameters are passed as is to the
        :meth:`QBetseeObjectMixin.init` method.
        '''

        # Initialize our superclass with all remaining parameters.
        super().init(*args, **kwargs)
