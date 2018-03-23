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
from betse.science.phase.phaseenum import SimPhaseKind
from betse.util.type.enums import make_enum
# from betse.util.type.types import type_check  #, StrOrNoneTypes

# ....................{ ENUMERATIONS                       }....................
SimmerState = make_enum(
    class_name='SimmerState',
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
SIMMER_STATES_RUNNING = {
    SimmerState.MODELLING,
    SimmerState.EXPORTING,
}
'''
Set of all **running simulator states** (i.e., states implying one or more
queued subcommands to be currently running and hence neither paused, halted, nor
done).
'''

# ....................{ GLOBALS ~ set : (fluid|fixed)      }....................
SIMMER_STATES_FLUID = {
    SimmerState.UNQUEUED,
    SimmerState.QUEUED,
    SimmerState.HALTED,
    SimmerState.DONE,
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

* :attr:`SimmerState.UNQUEUED` state to *only* the
  :attr:`SimmerState.QUEUED` state.
* :attr:`SimmerState.QUEUED` state to *only* the
  :attr:`SimmerState.UNQUEUED`,
  :attr:`SimmerState.MODELLING`, and
  :attr:`SimmerState.EXPORTING` states.

Pragmatically, preserving these distinctions would incur more cost than
pretending these states may be freely transitioned from. We prefer the latter.
'''


SIMMER_STATES_FIXED = {
    SimmerState.MODELLING,
    SimmerState.EXPORTING,
    SimmerState.PAUSED,
}
'''
Set of all **fixed simulator states** (i.e., states the simulator may *not*
freely transition from to any other state).

See Also
----------
:data:`SIMMER_STATES_FIXED`
    Negation of this set.
'''

# ....................{ GLOBALS ~ dict : status            }....................
SIMMER_STATE_TO_STATUS_TERSE = {
    SimmerState.UNQUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Unqueued'),
    SimmerState.QUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Queued'),
    SimmerState.MODELLING: QCoreApplication.translate(
        'guisimrunstate', 'Modelling'),
    SimmerState.EXPORTING: QCoreApplication.translate(
        'guisimrunstate', 'Exporting'),
    SimmerState.PAUSED: QCoreApplication.translate(
        'guisimrunstate', 'Paused'),
    SimmerState.HALTED: QCoreApplication.translate(
        'guisimrunstate', 'Stopped'),
    SimmerState.DONE: QCoreApplication.translate(
        'guisimrunstate', 'Finished'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated string serving as a terse (i.e., single word) synopsis of the action
being performed in that state.
'''


SIMMER_STATE_TO_STATUS_VERBOSE = {
    SimmerState.UNQUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Waiting for phase(s) to be queued...'),
    SimmerState.QUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Waiting for queued phase(s) to be run...'),
    SimmerState.MODELLING: QCoreApplication.translate(
        'guisimrunstate',
        #FIXME: Replace this coarse-grained string with the following
        #fine-grained string after hooking into the simulation process.
        'Modelling <b>{phase_type}</b> phase...'),
        # 'Modelling <b>{phase_type}</b> '
        # 'step {step_curr} '
        #   '<i>of</i> {step_total}:'),
    SimmerState.EXPORTING: QCoreApplication.translate(
        'guisimrunstate',
        #FIXME: Replace this coarse-grained string with the following
        #fine-grained string after hooking into the simulation process.
        'Exporting <b>{phase_type}</b> phase...'),
        # 'Exporting <b>{phase_type}</b> '
        # '{export_type} <pre>"{export_name}"</pre> '
        # 'step {step_curr} '
        #   '<i>of</i> {step_total}:'),
    SimmerState.PAUSED: QCoreApplication.translate(
        'guisimrunstate', 'Paused {status_prior}'),
    SimmerState.HALTED: QCoreApplication.translate(
        'guisimrunstate', 'Stopped {status_prior}'),
    SimmerState.DONE: QCoreApplication.translate(
        'guisimrunstate', 'Finished {status_prior}'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated, unformatted string templating a verbose (i.e., single sentence)
synopsis of the action being performed in that state.

Most such strings contain *no* format specifiers and are thus displayable as is.
Some such strings contain one or more format specifiers (e.g., ``{cmd_name}}`)
and are thus displayable *only* after interpolating the corresponding values.

Format specifiers embedded in these strings include:

* ``{phase_type}``, a word signifying the type of currently running simulator
  phase if any (e.g., "seed," "initialization").
* ``{status_prior}``, text previously formatted from a string of this dictionary
  synopsizing the prior state of this simulator. Since this text is interpolated
  into the middle of arbitrary sentences, the first character of this text
  *must* be lowercase.
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
