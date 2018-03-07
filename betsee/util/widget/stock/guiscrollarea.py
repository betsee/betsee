#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QScrollArea` subclasses.
'''

# ....................{ IMPORTS                            }....................
# from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QScrollArea
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUBCLASSES                         }....................
class QBetseeScrollImage(QBetseeObjectMixin, QScrollArea):
    '''
    :mod:`QScrollArea`-based widget (pre)viewing a single image within a
    :mod:`QScrollArea`.

    This widget supports all image filetypes supported by standard Qt widgets.
    Specifically, all images whose filetypes are in the system-specific set
    returned by the :func:`betse.util.path.guifiletype.get_image_read_filetypes`
    function are explicitly supported.

    of filetype
    supported by the :class:`QImageReader` in

    substantially improving upon the stock
    :mod:`QScrollArea` functionality with respect to image viewing.

    This application-specific widget augments the :class:`QScrollArea` class
    with additional support for (pre)viewing of a single image of filetype
    supported by the :class:`QImageReader` .

    * **Horizontal scrollbars,** automatically displaying horizontal scrollbars
      for all columns whose content exceeds that column's width. For
      inexplicable reasons, this functionality has been seemingly intentionally
      omitted from the stock :class:`QScrollArea`.

    Attributes
    ----------
    _image_label : QLabel
        Child label contained with this line edit. To preview the image whose
        filename is the text displayed by this line edit, this label's pixmap is
        read from this filename. By convention, this label is typically situated
        below this line edit.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._image_label = None

    # ..................{ SUPERCLASS ~ setters               }..................
    def setColumnCount(self, column_count: int) -> None:

        # Defer to the superclass implementation.
        super().setColumnCount(column_count)

        # If this tree now contains more than one column, permit the last such
        # column's content to automatically resize to the width of the viewport.
        if column_count != 1:
            self.header().setStretchLastSection(True)
