#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application-specific exception hierarchy.
'''

# ....................{ IMPORTS                            }....................
from abc import ABCMeta

# ....................{ EXCEPTIONS                         }....................
#FIXME: Define an __init__() method asserting that the passed exception message
#is non-None, which Python permits by default but which is functionally useless.
class BetseeException(Exception, metaclass=ABCMeta):
    '''
    Abstract base class of all application-specific exceptions.
    '''
    pass

# ....................{ EXCEPTIONS ~ lib                   }....................
class BetseeLibException(BetseeException):
    '''
    General-purpose exception applicable to third-party dependencies.
    '''
    pass
