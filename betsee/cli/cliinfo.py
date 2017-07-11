#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Low-level metadata facilities.
'''

# ....................{ IMPORTS                            }....................
from betse  import metadata as betse_metadata
from betsee import metadata as betsee_metadata

# ....................{ GETTERS                            }....................
def get_header() -> str:
    '''
    Single-line string synopsizing the current installation of this application.
    '''

    return (
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
