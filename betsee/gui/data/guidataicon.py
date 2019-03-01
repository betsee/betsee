#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application-specific **post-startup icon store** (i.e., abstract container of
all :class:`QIcon`-based in-memory icons required *after* rather than during
application startup) functionality.

By compare, most icons leveraged by this application are required only at
application startup and hence already managed by the pregenerated
:mod:`betsee.data.py.betsee_ui` submodule cached from the Qt Creator-managed
``betsee/data/ui/betsee.ui` file created at application design time. To avoid
redundancy, this submodule intentionally excludes these icons.

Design
----------
Each post-startup icon stored by this submodule is exposed through a
corresponding function decorated by the :func:`func_cached` memoizer,
guaranteeing that:

* The first call to that function creates, caches, and returns a new
  :class:`QIcon` instance encapsulating that icon.
* All subsequent calls to that function return the existing :class:`QIcon`
  instance previously cached by the first call to that function.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication
from PySide2.QtGui import QIcon
# from betse.util.io.log import logs
from betse.util.type.decorator.decmemo import func_cached
# from betse.util.type.types import type_check
from betsee.util.io.image import guiicon

# ....................{ GETTERS                           }....................
@func_cached
def get_icon_dot() -> QIcon:
    '''
    **Bullet point** (i.e., icon typically signifying a numberless item of a
    dynamically constructed list, tree, or other data structure).
    '''

    return guiicon.make_icon(resource_name='://icon/entypo+/dot-single.svg')
