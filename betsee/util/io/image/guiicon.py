#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **icon** (i.e., :class:`QIcon`-based in-memory icon, including both
rasterized and vectorized formats) functionality.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication
from PySide2.QtGui import QIcon
# from betsee.guiexception import BetseePySideIconException
from betse.util.type.types import type_check

# ....................{ MAKERS                            }....................
@type_check
def make_icon(resource_name: str) -> QIcon:
    '''
    Create and return a new :class:`QIcon` instance encapsulating an in-memory
    icon deserialized from the Qt-specific resource with the passed name.

    Parameters
    ----------
    resource_name : str
        Name of the `Qt-specific resource <resources_>`__ providing this icon.
        For generality, this should typically be a ``:/``- or
        ``qrc:///``-prefixed string (e.g., ``://icon/entypo+/dot-single.svg``).

    .. _resources:
        https://doc.qt.io/qt-5/resources.html

    Returns
    ----------
    QIcon
        In-memory icon deserialized from this resource.
    '''

    #FIXME: Non-ideal. Ideally, we would have seem means of validating the
    #passed string as a valid resource name before handing this string off to
    #Qt for subsequent parsing.

    # Well, that pretty much does it.
    return QIcon(resource_name)
