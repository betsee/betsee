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
SimCmdState = make_enum(
    class_name='SimCmdState',
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

# ....................{ GLOBALS ~ status                   }....................
SIM_CMD_STATE_TO_STATUS = {
    SimCmdState.UNQUEUED: QCoreApplication.translate(
        'guisimcmd', 'Waiting for phase(s) to be queued...'),
    SimCmdState.QUEUED: QCoreApplication.translate(
        'guisimcmd', 'Waiting for queued phase(s) to be modelled...'),
    SimCmdState.MODELLING: QCoreApplication.translate(
        'guisimcmd',
        'Modelling <b>{phase_type}</b> '
        'step {step_curr} '
          '<i>of</i> {step_total}:'),
    SimCmdState.EXPORTING: QCoreApplication.translate(
        'guisimcmd',
        'Exporting <b>{phase_type}</b> '
        '{export_type} <pre>"{export_name}"</pre> '
        'step {step_curr} '
          '<i>of</i> {step_total}:'),
    SimCmdState.PAUSED: QCoreApplication.translate(
        'guisimcmd', 'Paused {cmd_prior}'),
    SimCmdState.HALTED: QCoreApplication.translate(
        'guisimcmd', 'Stopped {cmd_prior}'),
    SimCmdState.DONE: QCoreApplication.translate(
        'guisimcmd', 'Finished {cmd_prior}'),
}
'''
Dictionary mapping from each type of simulator state to a human-readable,
translated, unformatted string templating a high-level synopsis of the action
being performed in that state.

Most such strings contain *no* format specifiers and are thus displayable as is.
Some such strings contain one or more format specifiers (e.g., ``{cmd_name}}`)
and are thus displayable *only* after interpolating the corresponding values.
'''

# ....................{ GLOBALS ~ status : details         }....................
MODELLING_SIM_PHASE_KIND_TO_STATUS_DETAILS = {
    # Note that low-level details for the "SimPhaseKind.SEED" phase are specific
    # to the current action being performed and hence defined in the lower-level
    # BETSE codebase rather than here.

    SimPhaseKind.INIT: QCoreApplication.translate(
        'guisimcmd', 'Initializing {time_curr} <i>of</i> {time_total}...'),
    SimPhaseKind.SIM: QCoreApplication.translate(
        'guisimcmd', 'Simulating {time_curr} <i>of</i> {time_total}...'),
}
'''
Dictionary mapping from the initialization and simulation phases to a
human-readable, translated, unformatted string templating the low-level details
of the action being performed when modelling that phase.
'''


EXPORTING_TYPE_TO_STATUS_DETAILS = {
    SimExportType.CSV: QCoreApplication.translate(
        'guisimcmd',
        'Exporting comma-separated value (CSV) file '
        '<pre>"{filename}"</pre>...'),
    SimExportType.PLOT: QCoreApplication.translate(
        'guisimcmd', 'Exporting image <pre>"{filename}"</pre>...'),
    SimExportType.ANIM: QCoreApplication.translate(
        'guisimcmd',
        'Exporting animation <pre>"{filename}"</pre> frame '
        '{time_curr} <i>of</i> {time_total}...'),
}
'''
Dictionary mapping from the initialization and simulation phases to a
human-readable, translated, unformatted string templating the low-level details
of the action being performed when modelling that phase.
'''
