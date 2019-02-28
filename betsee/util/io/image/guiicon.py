#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Icon** (i.e., :class:`QIcon`-based in-memory image, including both rasterized
and vectorized formats) functionality.
'''

#FIXME: Define the following functionality in this submodule:
#
#* "_URI_TO_ICON = {}", a global private dictionary mapping arbitrary URIs to
#  "QIcon" instances previously created and returned by the get_icon()
#  function, which internally leverages this dictionary to seamlessly cache
#  these icons.
#* "def make_icon(uri: str) -> QIcon", a function accepting an arbitrary URI
#  and creating and returning a "QIcon" instance from this URI. Avoid
#  attempting to manually validate this URI. Leave that to Qt, please.
#* "def get_icon(uri: str) -> QIcon", a function accepting an arbitrary URI
#  and either:
#  * If the "_URI_TO_ICON" dictionary does *NOT* already contain this URI as an
#    existing key:
#    * Call the lower-level make_icon() function to create a "QIcon" instance
#      from this URI.
#    * Cache this instance with the "_URI_TO_ICON" dictionary.
#    * Return this instance.
#  * Else, return the previously cached instance in "_URI_TO_ICON" dictionary.
#
#Naturally, most callers should call the higher-level get_icon() function.

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication
from PySide2.QtGui import QIcon
# from betsee.guiexception import BetseePySideIconException

# ....................{ MAKERS                            }....................
