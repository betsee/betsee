#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level application-specific logging facilities.
'''

# ....................{ IMPORTS                            }....................
from betse import metadata as betse_metadata
from betse.util.io.log import logs
from betsee import guimetadata as betsee_metadata

# ....................{ LOGGERS                            }....................
def log_header() -> None:
    '''
    Log a single-line human-readable sentence synopsizing the state of the
    current application (e.g., name, codename, version).
    '''

    logs.log_info(
        'Welcome to <<'
        '{betsee_name} {betsee_version} | '
        '{betse_name} {betse_version} | '
        '{betse_codename}'
        '>>.'.format(
            betsee_name=betsee_metadata.NAME,
            betsee_version=betsee_metadata.VERSION,
            betse_name=betse_metadata.NAME,
            betse_version=betse_metadata.VERSION,
            betse_codename=betse_metadata.CODENAME,
        ))
