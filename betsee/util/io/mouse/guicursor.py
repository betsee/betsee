#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level :mod:`PySide2`-based mouse cursor facilities.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt
from PySide2.QtGui import QApplication
from betse.util.type.types import GeneratorType
from contextlib import contextmanager

# ....................{ CONTEXTS                           }....................
@contextmanager
def waiting_cursor() -> GeneratorType:
    '''
    Context manager changing the mouse cursor to the prototypical wait cursor
    (e.g., animated hourglass) for the duration of this context.

    This context manager guaranteeably reverts the cursor to the prior cursor
    even when fatal exceptions are raised (e.g., by the caller's block).

    Returns
    -----------
    contextlib._GeneratorContextManager
        Context manager changing the cursor as described above.

    Yields
    -----------
    None
        Since this context manager yields no values, the caller's ``with``
        statement must be suffixed by *no* ``as`` clause.
    '''

    # Attempt to...
    try:
        # Change the cursor to the wait cursor.
        QApplication.setOverrideCursor(Qt.WaitCursor)

        # Yield control to the body of the caller's "with" block.
        yield
    # Revert to the prior cursor even if that block raised an exception.
    finally:
        QApplication.restoreOverrideCursor()
