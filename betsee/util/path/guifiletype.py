#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based filetype functionality.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import QCoreApplication
from PySide2.QtGui import QImageReader
from betse.util.type.decorator.decmemo import func_cached
# from betse.util.io.log import logs
from betse.util.type.types import SetType  # type_check,

# ....................{ SELECTORS ~ read                   }....................
@func_cached
def get_image_read_filetypes() -> SetType:
    '''
    Set of all image filetypes readable by the low-level :class:`QImageReader`
    utility class internally required by all high-level image classes (e.g.,
    :class:`PySide2.QtGui.QImage`, :class:`PySide2.QtGui.QPicture`).

    For generality, these filetypes are *not* prefixed by a ``.`` delimiter.

    Examples
    ----------
        >>> from betsee.util.path import guifiletype
        >>> guifiletype.get_image_read_filetypes()
        ... {'bmp',
        ...  'cur',
        ...  'gif',
        ...  'ico',
        ...  'jpeg',
        ...  'jpg',
        ...  'pbm',
        ...  'pgm',
        ...  'png',
        ...  'ppm',
        ...  'svg',
        ...  'svgz',
        ...  'xbm',
        ...  'xpm'}
    '''

    # Avoid circular import dependencies.
    from betsee.util.type.text import guistr

    # Create, cache, and return the set of...
    return {
        # Decode this Qt-specific byte array into a Python string.
        guistr.decode_qbytearray_ascii(image_filetype_qbytearray)
        # For each "QByteArray" instance comprising an ASCII-encoded image
        # filetype readable by "QImageReader"...
        for image_filetype_qbytearray in QImageReader.supportedImageFormats()
    }
