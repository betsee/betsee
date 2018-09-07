#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **simulator state** (i.e., abstract node in the finite state automata
corresponding to this simulator) functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication
from betse.science.export.expenum import SimExportType
from betse.science.phase.phaseenum import SimPhaseKind
# from betse.util.type.types import type_check
from betsee.gui.simtab.run.guisimrunenum import SimmerState, SimmerModelState

# ....................{ GLOBALS ~ dict                    }....................
#FIXME: This absolutely does *NOT* belong here. Shift this into a higher-level
#and more general-purpose submodule. This is sufficiently generic.
SIM_PHASE_KIND_TO_NAME = {
    SimPhaseKind.SEED: QCoreApplication.translate(
        'guisimrunstate', 'seed'),
    SimPhaseKind.INIT: QCoreApplication.translate(
        'guisimrunstate', 'initialization'),
    SimPhaseKind.SIM: QCoreApplication.translate(
        'guisimrunstate', 'simulation'),
}
'''
Dictionary mapping from each type of simulation phase to the human-readable
translated name of that phase.
'''

# ....................{ GLOBALS ~ set                     }....................
SIMMER_STATES = set(simmer_state for simmer_state in SimmerState)
'''
Set of all possible simulator states.
'''


SIMMER_STATES_IDLE = {
    SimmerState.UNQUEUED,
    SimmerState.QUEUED,
}
'''
Set of all **idle simulator states** (i.e., states implying *no* queued
subcommands to be currently working, stopping, or recently finished).
'''

# ....................{ GLOBALS ~ set : running           }....................
SIMMER_STATES_RUNNING = {
    SimmerState.MODELLING,
    SimmerState.EXPORTING,
}
'''
Set of all **running simulator states** (i.e., states implying one or more
queued subcommands to be currently running and hence either modelling or
exportingb but neither paused, stopping, nor finished).
'''


SIMMER_STATES_WORKING = SIMMER_STATES_RUNNING | {SimmerState.PAUSED,}
'''
Set of all **working simulator states** (i.e., states implying one or more
queued subcommands to be currently working and hence either modelling,
exporting, or paused but neither stopping nor finished).
'''

# ....................{ GLOBALS ~ set : halting           }....................
SIMMER_STATES_HALTING = {
    SimmerState.PAUSED,
    SimmerState.STOPPING,
    SimmerState.FINISHED,
}
'''
Set of all **halting simulator states** (i.e., states implying one or more
previously running queued subcommands to be currently halted, either
temporarily as in the case of a paused subcommand or permanently as in the
case of a stopped or finished subcommand).
'''


SIMMER_STATES_UNWORKABLE = {
    SimmerState.UNQUEUED,
    SimmerState.STOPPING,
}
'''
Set of all **unworkable simulator states** (i.e., states implying the proactor
to be incapable of performing any work).
'''

# ....................{ GLOBALS ~ set : from              }....................
SIMMER_STATES_FROM_FLUID = {
    SimmerState.UNQUEUED,
    SimmerState.QUEUED,
    SimmerState.FINISHED,
    SimmerState.STOPPING,
}
'''
Set of all **out-bound fluid simulator states** (i.e., states the simulator may
freely transition from into any other state).

Specifically, the states:

* Contained in this set are all low priority and hence may be flexibly replaced
  at simulator runtime with any other state.
* Excluded by this set are all high priority and hence *must* be preserved as
  is until completed -- possibly by manual user intervention (e.g., toggling
  the start and pause buttons).

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

See Also
----------
:data:`SIMMER_STATES_FROM_FIXED`
    Complement (i.e., negation) of this set.
'''


SIMMER_STATES_FROM_FIXED = SIMMER_STATES - SIMMER_STATES_FROM_FLUID
'''
Set of all **out-bound fixed simulator states** (i.e., states the simulator may
*not* freely transition from into any other state).

Specifically, the states:

* Contained in this set are all high priority and hence may be inflexibly
  replaced at simulator runtime with *only* other states in this same set.
* Excluded by this set are all low priority.

See Also
----------
:data:`SIMMER_STATES_FROM_FLUID`
    Complement (i.e., negation) of this set.
'''

# ....................{ GLOBALS ~ set : into              }....................
SIMMER_STATES_INTO_FLUID = {
    SimmerState.UNQUEUED,
    SimmerState.QUEUED,
}
'''
Set of all **in-bound fluid simulator states** (i.e., states the simulator may
freely transition into from any other state).

See Also
----------
:data:`SIMMER_STATES_FROM_FLUID`
    Analogue of this set with respect to in-bound transitions.
:data:`SIMMER_STATES_INTO_FIXED`
    Complement (i.e., negation) of this set.
'''


SIMMER_STATES_INTO_FIXED = SIMMER_STATES - SIMMER_STATES_INTO_FLUID
'''
Set of all **in-bound fixed simulator states** (i.e., states the simulator may
*not* freely transition into from any other state).

See Also
----------
:data:`SIMMER_STATES_FROM_FIXED`
    Analogue of this set with respect to in-bound transitions.
:data:`SIMMER_STATES_INTO_FLUID`
    Complement (i.e., negation) of this set.
'''

# ....................{ GLOBALS ~ dict : status           }....................
SIMMER_STATE_TO_PHASE_STATUS = {
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
    SimmerState.STOPPING: QCoreApplication.translate(
        'guisimrunstate', 'Stopped'),
    SimmerState.FINISHED: QCoreApplication.translate(
        'guisimrunstate', 'Finished'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated string serving as a single-word synopsis of the action being
performed in that state.
'''


SIMMER_STATE_TO_PROACTOR_STATUS = {
    SimmerState.UNQUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Waiting for phase(s) to be queued...'),
    SimmerState.QUEUED: QCoreApplication.translate(
        'guisimrunstate', 'Waiting for queued phase(s) to be started...'),
    SimmerState.MODELLING: QCoreApplication.translate(
        'guisimrunstate', 'Modelling <b>{phase_type}</b> phase...'),
    SimmerState.EXPORTING: QCoreApplication.translate(
        'guisimrunstate', 'Exporting <b>{phase_type}</b> phase...'),
    SimmerState.PAUSED: QCoreApplication.translate(
        'guisimrunstate', 'Paused {status_prior}.'),
    SimmerState.STOPPING: QCoreApplication.translate(
        'guisimrunstate', 'Stopped {status_prior}.'),
    SimmerState.FINISHED: QCoreApplication.translate(
        'guisimrunstate', 'Finished {status_prior}.'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated, unformatted string templating a single-sentence synopsis of the
action being performed in that state.

Formats
----------
Format specifiers embedded in these strings include:

* ``{phase_type}``, a word signifying the type of currently running simulator
  phase if any (e.g., "seed," "initialization").
* ``{status_prior}``, text previously formatted from a string of this
  dictionary synopsizing the prior state of this simulator. Since this text is
  interpolated into the middle of arbitrary sentences, the first character of
  this text *must* be lowercase.

Most such strings contain no format specifiers and are thus displayable as is.
Some such strings contain one or more format specifiers (e.g., ``{cmd_name}}`)
and are thus displayable *only* after interpolating the corresponding values.
'''

# ....................{ GLOBALS ~ dict : substatus        }....................
SIMMER_STATE_TO_PROACTOR_SUBSTATUS = {
    SimmerState.UNQUEUED: QCoreApplication.translate(
        'guisimrunstate',
        'Queued '
        '{queued_modelling} phase(s) for modelling and '
        '{queued_exporting} phase(s) for exporting.'
    ),
    SimmerState.QUEUED: QCoreApplication.translate(
        'guisimrunstate',
        'Queued '
        '{queued_modelling} phase(s) for modelling and '
        '{queued_exporting} phase(s) for exporting.'
    ),
    SimmerState.MODELLING: {
        SimPhaseKind.SEED: None,
        SimPhaseKind.INIT: {
            SimmerModelState.PREPARING: QCoreApplication.translate(
                'guisimrunstate', 'Loading seeded cell cluster...'),
            SimmerModelState.MODELLING: QCoreApplication.translate(
                'guisimrunstate',
                'Initialized '
                '<b>{progress_current}</b> <i>of</i> '
                '<b>{progress_maximum}</b> '
                'simulation time steps.'
            ),
            SimmerModelState.FINISHING: QCoreApplication.translate(
                'guisimrunstate', 'Saving initialization results...'),
        },
        SimPhaseKind.SIM: {
            SimmerModelState.PREPARING: QCoreApplication.translate(
                'guisimrunstate', 'Loading initialization results...'),
            SimmerModelState.MODELLING: QCoreApplication.translate(
                'guisimrunstate',
                'Simulated '
                '<b>{progress_current}</b> <i>of</i> '
                '<b>{progress_maximum}</b> '
                'simulation time steps.'
            ),
            SimmerModelState.FINISHING: QCoreApplication.translate(
                'guisimrunstate', 'Saving simulation results...'),
        },
    },
    #FIXME: Consider querying the BETSE client for the metadata interpolated
    #into the following strings by defining the following new worker signals:
    #
    #* subprogress_ranged(), enabling us to at least subdivide a unit of
    #
    #  progress (e.g., exportation of a single animation) into subunits of
    #  subprogress (e.g., each frame of that animation).
    #* subprogressed(), analogous to the existing progressed() signal.
    #* Some variant of pathname_saved(), pathname_wrote(), pathname_saving(),
    #  pathname_writing(), or pathname_written(), accepting a single string
    #  pathname. The saved variants read a tad better than the wrote variants,
    #  but none of these stand out as particularly inspiring. Tense is
    #  certainly an issue, as we'd rather callers not assume this pathname to
    #  have already been written to by this worker when this signal is emitted.
    SimmerState.EXPORTING: {
        SimExportType.CSV: QCoreApplication.translate(
            'guisimrunstate',
            'Exported comma-separated value (CSV) file '
            '<pre>"{pathname}"</pre>.'
        ),
        SimExportType.PLOT: QCoreApplication.translate(
            'guisimrunstate',
            'Exported image <pre>"{pathname}"</pre>.'
        ),
        SimExportType.ANIM: QCoreApplication.translate(
            'guisimrunstate',
            'Exported animation <pre>"{pathname}"</pre> frame '
            '{subprogress_current} <i>of</i> {subprogress_total}.'
        ),
    },
    SimmerState.PAUSED:   '{substatus_prior}',
    SimmerState.STOPPING:  '{substatus_prior}',
    SimmerState.FINISHED: '{substatus_prior}',
}
'''
Dictionary mapping from each type of simulator state to an object specific to
that type transitively yielding a human-readable, translated, unformatted
string templating the single-sentence details of the action being performed in
that state.

Structure
----------
Whereas each value of each key-value pair of the comparable
:data:`SIMMER_STATE_TO_PHASE_STATUS` and
:data:`SIMMER_STATE_TO_PROACTOR_STATUS` dictionaries is *always* a string,
each value of each key-value pair of this dictionary contextually depends upon
that value. Specifically, if this key is:

* :attr:`SimmerState.MODELLING`, this value is a nested dictionary mapping from
  each type of simulation phase to either:

  * If that phase is the seed phase, ``None``. Due to the variability of
    details pertaining to this phase, BETSE itself defines these details by the
    :meth:`betsee.gui.simtab.run.work.guisimrunworksig.SimCallbacksSignaller.progress_stated`
    method emitting a signal connected to the text box showing these details.
  * If that phase is the initialization or simulation phase, a nested
    dictionary mapping from each type of simulator modelling state to an
    unformatted string template detailing the current action being performed in
    that state.

* :attr:`SimmerState.EXPORTING`, this value is a nested dictionary mapping from
  each type of simulation export to an unformatted string template detailing
  the exporting of that export.
* Any other key, this value is an unformatted string template.

Formats
----------
Format specifiers embedded in these strings include:

* ``{progress_current}``, a non-negative integer signifying the current time
  step of this phase.
* ``{progress_total}``, a non-negative integer signifying the total number of
  time steps in this phase.

Most such strings contain no format specifiers and are thus displayable as is.
Some such strings contain one or more format specifiers (e.g., ``{cmd_name}}`)
and are thus displayable *only* after interpolating the corresponding values.
'''

# ....................{ GLOBALS ~ dict : status : details }....................
MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS = {
    # Note that low-level details for the "SimPhaseKind.SEED" phase are unique
    # to the current action being performed and hence defined by the
    # lower-level BETSE codebase rather than here.
    SimPhaseKind.INIT: QCoreApplication.translate(
        'guisimrunstate',
        'Initializing {progress_current} <i>of</i> {progress_total} '
        'time steps...'),
    SimPhaseKind.SIM: QCoreApplication.translate(
        'guisimrunstate',
        'Simulating {progress_current} <i>of</i> {progress_total} '
        'time steps...'),
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
