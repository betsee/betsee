#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry
# See "LICENSE" for further details.

'''
Concrete subclasses defining this application's command line interface (CLI).
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and application modules.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from betse import metadata as betse_metadata
from betse.cli.cliabc import CLIABC
from betse.util.io.log import logs
from betse.util.type.types import type_check, MappingType
from betsee import ignition as betsee_ignition
from betsee import metadata as betsee_metadata

# ....................{ SUBCLASS                           }....................
class BetseeCLI(CLIABC):
    '''
    Command line interface (CLI) for this application.
    '''

    # ..................{ SUPERCLASS ~ header                }..................
    def _show_header(self) -> None:

        # Log a one-line synopsis of metadata logged by the ``info`` subcommand.
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

    # ..................{ SUPERCLASS ~ properties            }..................
    @property
    def _arg_parser_top_kwargs(self) -> MappingType:

        return {
            # Human-readable multi-sentence application description.
            'description': betsee_metadata.DESCRIPTION,

            #FIXME: Define an epilog encouraging users requiring full access to
            #the BETSE's command-line suite of subcommands to call the "betse"
            #command instead.

            # Human-readable multi-sentence application help suffix.
            # 'epilog': SUBCOMMANDS_SUFFIX,
        }

    # ..................{ SUPERCLASS ~ methods               }..................
    def _ignite_app(self) -> None:

        # (Re-)initialize both BETSEE and BETSE.
        betsee_ignition.reinit()


    #FIXME: Augment to also display this exception with PySide2 if importable.
    #See the "betsee.__main__" submodule for similar logic.
    @type_check
    def _handle_exception(self, exception: Exception) -> None:

        # Defer to superclass handling, which typically logs this exception.
        super()._handle_exception(exception)


    #FIXME: Implement to actually do something.
    def _do(self) -> object:
        '''
        Implement this command-line interface (CLI).

        If a subcommand was passed, this method runs this subcommand and returns
        the result of doing so; else, this method prints help output and returns
        the current instance of this object.
        '''

        #,Print help output. Note that this common case constitutes neither
        # a fatal error nor a non-fatal warning.
        print()
        self._arg_parser.print_help()

        # Return the current instance of this object. While trivial, this
        # behaviour simplifies memory profiling of this object.
        return self
