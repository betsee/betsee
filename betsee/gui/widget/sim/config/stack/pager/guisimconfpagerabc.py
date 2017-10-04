#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Abstract base classes of all :mod:`PySide2`-based stack widget page controller
subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QObject
from PySide2.QtWidgets import QMainWindow
from betse.util.type.types import type_check

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimConfStackedWidgetPagerABC(QObject):
    '''
    Abstract base class of all :mod:`PySide2`-based stack widget page controller
    subclasses, each connecting all editable widgets of the corresponding page
    with all low-level settings associated with some high-level feature of the
    current simulation configuration.
    '''

    # ..................{ INITIALIZERS                       }..................
    # To avoid circular import dependencies, this parameter is validated to be
    # an instance of the "QMainWindow" superclass rather than the expected
    # "QBetseeMainWindow" subclass of the "betsee.gui.widget.guimainwindow"
    # submodule. Why? Because the latter imports the cached "betsee_ui.py"
    # module which imports the current submodule. Since this application only
    # contains one main window, this current validation suffices.
    @type_check
    def init(self, main_window: QMainWindow) -> None:
        '''
        Initialize this stacked widget page against the passed parent main
        window.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window may
        be retained, however.

        Parameters
        ----------
        main_window: QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this widget.
        '''

        pass
