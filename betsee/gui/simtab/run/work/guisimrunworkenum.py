#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator worker enumeration** (e.g., :class:`enum.Enum` subclass
describing different types of simulator work) functionality.
'''

# ....................{ IMPORTS                           }....................
from betsee.gui.simtab.run.guisimrunstate import SimmerState
from enum import Enum

# ....................{ ENUMERATIONS                      }....................
class SimmerPhaseSubkind(Enum):
    '''
    Enumeration of each kind of **simulator subcommand worker** (i.e., type of
    work performed within a given simulation phase by a given simulator
    worker).

    This child enumeration is a proper subset of the parent
    :class:`SimmerState` enumeration differentiating simulator workers from one
    another in a convenient manner permitting the state of each simulator phase
    acted upon by each such worker to be trivially set.

    Attributes
    ----------
    MODELLING : enum
        Modelling state, implying this worker to model its simulator phase.
    EXPORTING : enum
        Exporting state, implying this worker to export its simulator phase.

    Examples
    ----------
    To trivially map between members of these two correlated enumerations, each
    member of this child enumeration is guaranteed to have the same ``value``
    attribute as each corresponding member of the parent :class:`SimmerState`
    enumeration: e.g.,

        >>> from betsee.gui.simtab.run.guisimrunstate import SimmerState
        >>> from betsee.gui.simtab.run.work.guisimrunworkenum import (
        ...     SimmerPhaseSubkind)
        >>> SimmerPhaseSubkind.MODELLING.value == (
        ...     SimmerState.MODELLING.value)
        True
        >>> SimmerPhaseSubkind.EXPORTING.value == (
        ...     SimmerState.EXPORTING.value)
        True
    '''

    # For simplicity elsewhere, reuse existing enumeration values.
    MODELLING = SimmerState.MODELLING.value
    EXPORTING = SimmerState.EXPORTING.value
