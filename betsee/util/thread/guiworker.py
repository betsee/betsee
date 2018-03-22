#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **multithreading** (i.e., platform-portable, pure-Qt,
:class:`QThread`-based parallelization implemented external to Python and hence
Python's restrictive Global Interpreter Lock (GIL)) facilities.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject, Signal, Slot
# from betse.util.io.log import logs
from betse.util.type.types import type_check  #, CallableTypes
from betsee.guiexception import BetseePySideThreadException

# ....................{ SUPERCLASS                         }....................
class QBetseeWorkerABC(QObject):
    '''
    Low-level **worker** (i.e., thread-safe object implementing generically
    startable, pausable, resumable, and haltable business logic in a
    multithreaded manner intended to be moved to the thread encapsulated by a
    :class:`QThread` object).

    Attributes
    ----------

    See Also
    ----------
    https://codereview.stackexchange.com/a/173258/124625
        StackOverflow answer strongly inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this workable thread.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # By default, this thread has no adopted worker.
        self._is_worker = False

        # Garbage collect all child objects of this parent worker *AFTER* this
        # worker gracefully (i.e., successfully) terminates.
        self.finished.connect(self.deleteLater)
