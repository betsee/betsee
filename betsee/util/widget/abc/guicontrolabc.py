#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all :mod:`PySide2`-based controller subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QObject
from PySide2.QtWidgets import QMainWindow
from betse.util.type.types import type_check
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUPERCLASSES                       }....................
class QBetseeControllerABC(QBetseeObjectMixin, QObject):
    '''
    Abstract base class of all :mod:`PySide2`-based controller subclasses in the
    standard model-view-controller (MVC) understanding of that term.

    Each instance of this class is a controller encapsulating all abstract state
    (including connective logic like signals and slots) required to sanely
    display a separate physical view (i.e., widget). To minimally integrate with
    Qt concurrency and signalling, this controller is a minimal :class:`QObject`
    instance rather than a full-fledged :class:`QWidget` instance.
    '''

    # ..................{ INITIALIZERS                       }..................
    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.window.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Initialize this controller against the passed parent main window.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window may
        be retained, however.

        Parameters
        ----------
        parent: QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        # Initialize our superclass.
        super().init()
