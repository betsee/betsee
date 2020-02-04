#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QProgressBar` subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import Slot  # Signal,
from PySide2.QtWidgets import QProgressBar
from betsee.util.widget.mixin.guiwdgmixin import QBetseeObjectMixin

# ....................{ SUBCLASSES                        }....................
class QBetseeProgressBar(QBetseeObjectMixin, QProgressBar):
    '''
    :mod:`QProgressBar`-based widget exposing additional caller-friendly slots.

    This widget augments the stock :class:`QProgressBar` class with high-level
    properties simplifying usage *and* high-level slots combining the utility
    of various lower-level slots (e.g., :meth:`set_range_and_value_minimum`).
    '''

    # # ..................{ INITIALIZERS                      }..................
    # def __init__(self, *args, **kwargs) -> None:
    #
    #     # Initialize our superclass with all passed parameters.
    #     super().__init__(*args, **kwargs)

    # ..................{ PROPERTIES                        }..................
    @property
    def is_done(self) -> bool:
        '''
        ``True`` only if this progress bar is currently in the **finished
        state** (i.e., if the current value of this progress bar is equal to
        the maximum value previously passed to the :meth:`setRange` method).
        '''

        # Surprisingly, this actually makes sense.
        return self.value() == self.maximum()


    @property
    def is_reset(self) -> bool:
        '''
        ``True`` only if this progress bar is currently in the **reset state**
        (i.e., if either the :meth:`setValue` method has yet to be called *or*
        the :meth:`reset` method has been called more recently than the
        :meth:`setValue` method).

        Equivalently, this property returns ``True`` only if this progress bar
        has no current progress value. Note that:

        * All progress bars are initially reset by default.
        * The **undetermined state** (i.e., when the range of this progress
          bar is ``[0, 0]``) takes precedence over this reset state. A progress
          bar that is currently undetermined is *not* reset.
        '''

        #FIXME: While unlikely to ever crop in our progress bar use cases,
        #consider the "INT_MIN" case as well. What is "INT_MIN", exactly?
        #Sadly, extensive grepping about suggests that neither PyQt5 nor
        #PySide2 expose this constant to Python code. Ergo, checking that
        #appears to infeasible. The alternative would be to:
        #
        #* Define a new "_is_reset" boolean instance variable.
        #* Default this boolean to "False" in the __init__() method.
        #* Override the reset() method to enable this boolean.
        #* Override the setValue() method to disable this boolean.

        # Yes, this is insanity. Nonetheless, this condition corresponds
        # exactly to the single-line C++ action performed by the default
        # QProgressBar.reset() implementation:
        #
        #    void QProgressBar::reset()
        #    {
        #        Q_D(QProgressBar);
        #        d->value = d->minimum - 1;
        #        if (d->minimum == INT_MIN)
        #            d->value = INT_MIN;
        #        repaint();
        #    }
        return self.value() == self.minimum() - 1


    @property
    def is_undetermined(self) -> bool:
        '''
        ``True`` only if this progress bar is currently in the **undetermined
        state** (i.e., if the :meth:`set_range_undetermined` method has been
        called more recently than any other range-setting method).

        Equivalently, this property returns ``True`` only if this progress bar
        allows exactly one possible progress value (i.e., 0), which Qt
        typically portrays as a busy indicator.
        '''

        # Insanity, thy name is the Qt API.
        return (
            self.maximum() == 0 and  # ...short-circuit us up the bomb!
            self.minimum() == 0
        )

    # ..................{ SLOTS                             }..................
    @Slot(int, int)
    def set_range_and_value_minimum(self, minimum: int, maximum: int) -> None:
        '''
        Sets the range of this progress bar to the passed range *and* sets the
        value of this progress bar to the minimum value of this range.

        This high-level slot is intended to serve as a drop-in replacement for
        the lower-level :meth:`setRange`. The latter only sets the range of
        this progress bar to the passed range, requiring callers to explicitly
        call the stock :meth:`setValue` slot with the minimum value of this
        range to perform the equivalent of this slot. Since callers typically
        perform both on setting the range, this slot conjoins these two slots
        into one slot for caller convenience.

        Caveats
        ----------
        Note that, if:

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

    # ..................{ METHODS                           }..................
    def set_range_undetermined(self) -> None:
        '''
        Change this progress bar to the **undetermined state** (i.e., the state
        such that this progress bar allows exactly one possible progress value
        of 0 rather than a range of such values).

        Qt typically portrays this state as a busy indicator.
        '''

        # Set the current range to an arbitrary pair of magic numbers. *sigh*
        self.setRange(0, 0)
