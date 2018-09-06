#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator enumeration** (e.g., :class:`enum.Enum` subclass
describing different types of simulator state) functionality.
'''

# ....................{ IMPORTS                           }....................
from betse.util.type.enums import make_enum
# from betse.util.type.types import type_check

# ....................{ ENUMERATIONS                      }....................
SimmerState = make_enum(
    class_name='SimmerState',
    member_names=(
        'UNQUEUED',
        'QUEUED',
        'MODELLING',
        'EXPORTING',
        'PAUSED',
        'STOPPING',
        'FINISHED',
    ),
    doc='''
    Enumeration of all supported types of **simulator state** (i.e., mutually
    exclusive combination of one or more booleans uniquely capturing the
    condition of the currently queued simulation subcommand if any, analogous
    to a state in a finite state automata).

    Attributes
    ----------
    UNQUEUED : enum
        Unqueued state, implying no subcommands to be queued.
    QUEUED : enum
        Queued state, implying one or more subcommands to be queued but *not*
        yet run and hence neither paused, halted, nor done.
    MODELLING : enum
        Modelling state, implying one or more queued subcommands specific to
        modelling (e.g., seed, initialization) to be currently running and
        hence neither paused, halted, nor done.
    EXPORTING : enum
        Exporting state, implying one or more queued subcommands specific to
        exporting (e.g., seed exports, initialization exports) to be currently
        running and hence neither paused, halted, nor done.
    PAUSED : enum
        Paused state, implying one or more queued subcommands to have been run
        but paused before completion.
    STOPPING : enum
        Stopping state, implying one or more queued subcommands to have been
        run but manually stopped before completion. This is a temporary state
        during which the proactor waits for the previously running worker to
        gracefully stop. Until this worker does so, the proactor remains
        incapable of performing new work (i.e., running queued subcommands).
        After this worker gracefully stops, the proactor switches from this
        state into the :attr:`FINISHED` state, implying the proactor to be
        capable of performing new work.
    FINISHED : enum
        Completion state, implying all queued subcommands to have completed
        either:

        * Successfully, in which case those subcommands ran to completion.
        * Unsuccessfully, in which case either:

          * The user prematurely stopped some or all of those subcommands.
          * One of those subcommands raised an uncaught fatal exception.
    '''
)



SimmerModelState = make_enum(
    class_name='SimmerModelState',
    member_names=(
        'PREPARING',
        'MODELLING',
        'FINISHING',
    ),
    doc='''
    Enumeration of all supported types of **simulator modelling state** (i.e.,
    mutually exclusive boolean uniquely capturing the condition of the
    currently queued modelling simulation subcommand if any, analogous to a
    state in a finite state automata).

    This enumeration applies *only* when the proactor is currently modelling
    (i.e., when the state of the proactor is :attr:`SimmerState.MODELLING`).
    This enumeration generically applies to modelling all simulation phases,
    including the seed, initialization, and simulation phases of a simulation.
    That said, this enumeration is typically only used to describe simulation
    phases whose modelling entails time steps -- notably, the initialization
    and simulation (but *not* seed) phases.

    Attributes
    ----------
    PREPARING : enum
        Pre-processing state. When modelling the initialization and simulation
        (but *not* seed) phases, this state implies a proactor worker to be
        preparing to model the first time step of this phase but to have yet to
        actually do so.
    MODELLING : enum
        In-processing state. When modelling the initialization and simulation
        (but *not* seed) phases, this state implies a proactor worker to be
        modelling a time step of this phase.
    FINISHING : enum
        Post-processing state, implying a proactor worker to:

        * Have successfully modelled all time steps of this phase.
        * Now be saving the results of this phase to disk, typically as one or
          more Python-specific pickled files.
    '''
)
