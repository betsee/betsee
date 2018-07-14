#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QProgressBar` subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import Slot  # Signal,
from PySide2.QtWidgets import QProgressBar
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUBCLASSES                        }....................
class QBetseeProgressBar(QBetseeObjectMixin, QProgressBar):
    '''
    :mod:`QProgressBar`-based widget exposing additional caller-friendly slots.

    This widget augments the stock :class:`QProgressBar` class with:

    * :meth:`set_range_and_value_minimum`, a drop-in replacement for the stock
      :meth:`setRange` slot that both:

      * Sets the range of this progress bar to the passed range.
      * Sets the value of this progress bar to the minimum value of this range.

    Attributes
    ----------
    '''

    # ..................{ INITIALIZERS                      }..................
    # def __init__(self, *args, **kwargs) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().__init__(*args, **kwargs)

    # ..................{ SLOTS                             }..................
    @Slot(int, int)
    def set_range_and_value_minimum(self, minimum: int, maximum: int) -> None:
        '''
        Sets the range of this progress bar to the passed range *and* sets the
        value of this progress bar to the minimum value of this range.

        The stock :meth:`setRange` slot only performs the former functionality,
        requiring callers to explicitly call the stock :meth:`setValue` slot
        with the minimum value of this range to perform the latter as well.
        Since callers typically perform both on setting the range, this custom
        slot conjoins these two slots into one slot for caller convenience.

        Caveats
        ----------
        If:

        * The passed minimum and maximum are both 0, this progress bar is set
          to an undetermined state.
        * The passed maximum is less than the passed minimum, only the passed
          minimum is set; the passed maximum is ignored.
        * The current value of this progress bar resides outside this range,
          this progress bar is implicitly reset by internally calling the
          :meth:`reset` method.

        Parameters
        ----------
        minimum : int
            Minimum value to constrain the values of this progress bar to.
        maximum : int
            Maximum value to constrain the values of this progress bar to.
        '''

        # Set the current range to the passed range.
        self.setRange(minimum, maximum)

        # Set the current value to the minimum of this range.
        self.setValue(minimum)
