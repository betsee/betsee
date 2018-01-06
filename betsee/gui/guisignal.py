#!/usr/bin/env python3
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-based application-wide signal classes.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QObject, Signal

# ....................{ CLASSES                            }....................
class QBetseeSignaler(QObject):
    '''
    :class:`PySide2`-based collection of various application-wide signals.

    These signals permit callers to trigger handling of events by corresponding
    slots of interested objects and widgets distributed throughout the
    application, including:

    * Restoration and storage of application-wide settings to and from their
      on-disk backing store (e.g., an application- and user-specific dotfile).

    Design
    ----------
    This class has been intentionally isolated from all sibling classes (e.g.,
    :class:`QBetseeSettings`) to circumvent circular chicken-and-the-egg issues
    between this and the :class:`QBetseeMainWindow` class. Conjoining these
    sibling classes into one monolithic class would introduce non-trivial (and
    probably non-resolvable) complications, including the need for the conjoined
    class to retain a weak reference to its :class:`QBetseeMainWindow` parent,
    which could conceivably be prematurely destroyed by Qt in another thread.
    '''

    # ..................{ SIGNALS ~ settings                 }..................
    restore_settings_signal = Signal()
    '''
    Signal reading and restoring application-wide settings previously written to
    a predefined application- and user-specific on-disk file by the most recent
    execution of this application if any *or* reducing to a noop.

    This signal is connected to the
    :meth:`QBetseeSettings.restore_settings` slot at initialization time,
    enabling callers in different threads to thread-safely restore settings.
    '''


    store_settings_signal = Signal()
    '''
    Signal writing application-wide settings to a predefined application- and
    user-specific on-disk file, which the next execution of this application
    will read and restore on startup.

    This signal is connected to the
    :meth:`QBetseeSettings.store_settings` slot at initialization time, enabling
    callers in different threads to thread-safely store settings.
    '''
