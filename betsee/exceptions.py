#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application-specific exception hierarchy.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during application startup, this module may
# import *ONLY* from modules guaranteed to exist at startup. This includes all
# standard Python and application modules but *NOT* third-party dependencies,
# which if unimportable will only be validated at some later time in startup.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from abc import ABCMeta

# ....................{ EXCEPTIONS                         }....................
#FIXME: Introduce into the "betse.exceptions" submodule as a new
#"BetseVerboseException" base class from which all other exception classes
#defined by that submodule should eventually subclass.
class BetseeException(Exception, metaclass=ABCMeta):
    '''
    Abstract base class of all application-specific exceptions.

    Attributes
    ----------
    title : str
        Human-readable title associated with this exception, typically
        constrained to at most two to three words.
    synopsis : str
        Human-readable synopsis tersely describing this exception, typically
        constrained to a single sentence.
    exegesis : optional[str]
        Human-readable explanation fully detailing this exception if any,
        typically spanning multiple sentences, *or* ``None`` otherwise (i.e.,
        if no such explanation is defined).
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(
        self,
        title: str,
        synopsis: str,
        exegesis: str = None,
    ) -> None:
        '''
        Initialize this exception.

        Parameters
        ----------
        title : str
            Human-readable title associated with this exception, typically
            constrained to at most two to three words.
        synopsis : str
            Human-readable synopsis tersely describing this exception, typically
            constrained to a single sentence.
        exegesis : optional[str]
            Human-readable explanation fully detailing this exception, typically
            spanning multiple sentences. Defaults to ``None``, in which case no
            such explanation is defined.
        '''

        # Since the @type_check decorator is unavailable at this early point in
        # application startup, manually assert the types of these parameters.
        assert isinstance(title, str), '"{}" not a string.'.format(title)
        assert isinstance(synopsis, str), '"{}" not a string.'.format(synopsis)
        assert isinstance(exegesis, (str, type(None))), (
            '"{}" neither a string nor "None".'.format(exegesis))

        # Initialize our superclass with the concatenation of this
        # exception's synopsis, a space, and exegesis (defaulting to the empty
        # string when unpassed).
        super().__init__(
            synopsis + (' ' + exegesis if exegesis is not None else ''))

        # Classify all passed parameters.
        self.title = title
        self.synopsis = synopsis
        self.exegesis = exegesis

# ....................{ EXCEPTIONS ~ general               }....................
class BetseeCacheException(BetseeException):
    '''
    General-purpose exception applicable to user-specific caching, including
    dynamic generation of pure-Python modules imported at runtime.
    '''

    pass

# ....................{ EXCEPTIONS ~ lib                   }....................
class BetseeLibException(BetseeException):
    '''
    General-purpose exception applicable to third-party dependencies.
    '''

    pass

# ....................{ EXCEPTIONS ~ pyside                }....................
class BetseePySideException(BetseeException):
    '''
    General-purpose exception applicable to :mod:`PySide2`, this application's
    principal third-party dependency.
    '''

    pass
