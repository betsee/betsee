#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator state** (i.e., abstract node in the finite state automata
corresponding to this simulator) functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from betse.science.export.expenum import SimExportType
from betse.science.phase.phasecls import SimPhaseKind
from betse.util.type.enums import make_enum
# from betse.util.type.types import type_check  #, StrOrNoneTypes

# ....................{ ENUMS                              }....................
SimulatorState = make_enum(
    class_name='SimulatorState',
    member_names=(
        'UNQUEUED',
        'QUEUED',
        'MODELLING',
        'EXPORTING',
        'PAUSED',
        'HALTED',
        'DONE',
    ))
'''
Enumeration of all supported types of **simulator state** (i.e., mutually
exclusive combination of one or more booleans uniquely capturing the condition
of the currently queued simulation subcommand if any, analogous to a state in a
finite state automata).

Attributes
----------
UNQUEUED : enum
    Unqueued state, implying no subcommands to be queued.
QUEUED : enum
    Queued state, implying one or more subcommands to be queued but *not* yet
    run and hence neither paused, halted, nor done.
MODELLING : enum
    Modelling state, implying one or more queued subcommands specific to
    modelling (e.g., seed, initialization) to be currently running and hence
    neither paused, halted, nor done.
EXPORTING : enum
    Exporting state, implying one or more queued subcommands specific to
    exporting (e.g., seed exports, initialization exports) to be currently
    running and hence neither paused, halted, nor done.
PAUSED : enum
    Paused state, implying one or more queued subcommands to have been run but
    paused before completion.
HALTED : enum
    Halted state, implying one or more queued subcommands to have been run but
    halted before completion.
DONE : enum
    Completion state, implying all queued subcommands to have been run to
    completion.
'''

# ....................{ GLOBALS ~ set                      }....................
SIMULATOR_STATES_FLUID = {
    SimulatorState.UNQUEUED,
    SimulatorState.QUEUED,
    SimulatorState.HALTED,
    SimulatorState.DONE,
}
'''
Set of all **fluid simulator states** (i.e., states the simulator may freely
transition to from any other state).

Specifically, the states:

* Contained in this set are all low priority and hence may be flexibly replaced
  at simulator runtime with any other state.
* Excluded by this set are all high priority and hence *must* be preserved as is
  until completed -- possibly by manual user intervention (e.g., toggling the
  start and pause buttons).

Caveats
----------
Technically, the claims implied by this set are *not* actually all the case.
For example, the simulator may transition from the:

* :attr:`SimulatorState.UNQUEUED` state to *only* the
  :attr:`SimulatorState.QUEUED` state.
* :attr:`SimulatorState.QUEUED` state to *only* the
  :attr:`SimulatorState.UNQUEUED`,
  :attr:`SimulatorState.MODELLING`, and
  :attr:`SimulatorState.EXPORTING` states.

Pragmatically, preserving these distinctions would incur more cost than
pretending these states may be freely transitioned from. We prefer the latter.
'''


SIMULATOR_STATES_FIXED = {
    SimulatorState.MODELLING,
    SimulatorState.EXPORTING,
    SimulatorState.PAUSED,
}
'''
Set of all **fixed simulator states** (i.e., states the simulator may *not*
freely transition from to any other state).

See Also
----------
:data:`SIMULATOR_STATES_FIXED`
    Negation of this set.
'''

# ....................{ GLOBALS ~ dict : status            }....................
SIMULATOR_STATE_TO_STATUS_TERSE = {
    SimulatorState.UNQUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Unqueued'),
    SimulatorState.QUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Queued'),
    SimulatorState.MODELLING: QCoreApplication.translate(
        'guisimrunstate', 'Modelling'),
    SimulatorState.EXPORTING: QCoreApplication.translate(
        'guisimrunstate', 'Exporting'),
    SimulatorState.PAUSED: QCoreApplication.translate(
        'guisimrunstate', 'Paused'),
    SimulatorState.HALTED: QCoreApplication.translate(
        'guisimrunstate', 'Stopped'),
    SimulatorState.DONE: QCoreApplication.translate(
        'guisimrunstate', 'Finished'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated string serving as a terse (i.e., single word) synopsis of the action
being performed in that state.
'''


SIMULATOR_STATE_TO_STATUS_VERBOSE = {
    SimulatorState.UNQUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Waiting for phase(s) to be queued...'),
    SimulatorState.QUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Waiting for queued phase(s) to be modelled...'),
    SimulatorState.MODELLING: QCoreApplication.translate(
        'guisimrunstate',
        'Modelling <b>{phase_type}</b> '
        'step {step_curr} '
          '<i>of</i> {step_total}:'),
    SimulatorState.EXPORTING: QCoreApplication.translate(
        'guisimrunstate',
        'Exporting <b>{phase_type}</b> '
        '{export_type} <pre>"{export_name}"</pre> '
        'step {step_curr} '
          '<i>of</i> {step_total}:'),
    SimulatorState.PAUSED: QCoreApplication.translate(
        'guisimrunstate', 'Paused {cmd_prior}'),
    SimulatorState.HALTED: QCoreApplication.translate(
        'guisimrunstate', 'Stopped {cmd_prior}'),
    SimulatorState.DONE: QCoreApplication.translate(
        'guisimrunstate', 'Finished {cmd_prior}'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated, unformatted string templating a verbose (i.e., single sentence)
synopsis of the action being performed in that state.

Most such strings contain *no* format specifiers and are thus displayable as is.
Some such strings contain one or more format specifiers (e.g., ``{cmd_name}}`)
and are thus displayable *only* after interpolating the corresponding values.
'''

# ....................{ GLOBALS ~ dict : status : details  }....................
MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS = {
    # Note that low-level details for the "SimPhaseKind.SEED" phase are specific
    # to the current action being performed and hence defined in the lower-level
    # BETSE codebase rather than here.

    SimPhaseKind.INIT: QCoreApplication.translate(
        'guisimrunstate', 'Initializing {time_curr} <i>of</i> {time_total}...'),
    SimPhaseKind.SIM: QCoreApplication.translate(
        'guisimrunstate', 'Simulating {time_curr} <i>of</i> {time_total}...'),
}
'''
Dictionary mapping from the initialization and simulation phases to a
human-readable, translated, unformatted string templating the low-level details
of the action being performed when modelling that phase.
'''


EXPORTING_TYPE_TO_STATUS_DETAILS = {
    SimExportType.CSV: QCoreApplication.translate(
        'guisimrunstate',
        'Exporting comma-separated value (CSV) file '
        '<pre>"{filename}"</pre>...'),
    SimExportType.PLOT: QCoreApplication.translate(
        'guisimrunstate', 'Exporting image <pre>"{filename}"</pre>...'),
    SimExportType.ANIM: QCoreApplication.translate(
        'guisimrunstate',
        'Exporting animation <pre>"{filename}"</pre> frame '
        '{time_curr} <i>of</i> {time_total}...'),
}
'''
Dictionary mapping from the initialization and simulation phases to a
human-readable, translated, unformatted string templating the low-level details
of the action being performed when modelling that phase.
'''
