#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`PySide2`-based file functionality.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QFileDialog
# from betse.util.io.log import logs
from betse.lib.pil import pils
from betse.lib.yaml import yamls
from betse.util.type.types import type_check, StrOrNoneTypes

# ....................{ GLOBALS                            }....................
_YAML_LABEL_TO_FILETYPES = {'YAML files': yamls.FILETYPES,}
'''
Dictionary mapping from a human-readable label to be displayed for each
iterable of YAML-specific filetypes accepted by this dialog to that iterable.
'''

# ....................{ SELECTORS ~ read                   }....................
@type_check
def select_file_read(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute or relative filename of this file if this dialog was not cancelled
    *or* ``None`` otherwise (i.e., if this dialog was cancelled).

    Parameters
    ----------
    All paremeters are passed as is to the :func:`guipath.select_path`
    function. Note that:

    * The ``dialog_title`` parameter *must* be passed by the caller.
    * The ``dialog_callable`` parameter must *not* be passed by the caller.

    Returns
    ----------
    StrOrNoneTypes
        Either:
        * If this dialog was confirmed, the absolute filename of this file.
        * If this dialog was cancelled, ``None``.
    '''

    # Avoid circular import dependencies.
    from betsee.util.path import guipath

    # Return the user-based result of displaying this path dialog.
    return guipath.select_path(
        *args, dialog_callable=QFileDialog.getOpenFileName, **kwargs)


@type_check
def select_file_yaml_read(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing YAML file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute or relative filename of this file if this dialog was not cancelled
    *or* ``None`` otherwise (i.e., if this dialog was cancelled).

    See Also
    ----------
    :func:`select_file_read`
        Further details.
    '''

    return select_file_read(
        *args, label_to_filetypes=_YAML_LABEL_TO_FILETYPES, **kwargs)


#FIXME: Ideally, this dialog would also display a preview of the currently
#selected image. Unfortunately, as the "QFileDialog" class provides no default
#means of doing so, doing so is non-trivial. Indeed, while existing solutions do
#exist, they exist only for Qt < 5.9. Qt >= 5.9 internally changed the widget
#substructure of "QFileDialog" widgets from a grid to vertical box layout. It
#remains unclear just how both layouts could reasonably be supported.
#Nonetheless, for Qt < 5.9 code in PyQt5 and C++ implementing this preview, see:
#
#    http://www.qtcentre.org/threads/68998-Qt5-QFileDialog-with-preview-picture
#    http://www.qtcentre.org/threads/33593-How-can-i-have-a-QFileDialog-with-a-preview-of-the-picture?p=247022#post247022
@type_check
def select_image_read(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing image file to be
    subsequently opened for reading (rather than overwriting), returning the
    absolute or relative filename of this file if this dialog was not cancelled
    *or* ``None`` otherwise (i.e., if this dialog was cancelled).

    For generality, this dialog recognizes all image filetypes recognized by the
    third-party image processing framework leveraged by BETSE itself: Pillow.
    BETSE defers to this framework for most low-level image I/O operations.
    Deferring to the same framework guarantees parity with BETSE behaviour.

    See Also
    ----------
    :func:`select_file_read`
        Further details.
    '''

    # If no title was passed, default to a sensible title.
    if 'dialog_title' not in kwargs:
        kwargs['dialog_title'] = QCoreApplication.translate(
            'select_image_read', 'Select Image')

    # Select an image for reading and return the filename of this image.
    return select_file_read(
        *args,
        label_to_filetypes={'Image files': pils.get_filetypes(),},
        **kwargs)

# ....................{ SELECTORS ~ save                   }....................
@type_check
def select_file_save(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an arbitrary file (either
    existing or non-existing) to be subsequently opened for in-place saving and
    hence overwriting, returning the absolute filename of this file if this
    dialog was not cancelled *or* ``None`` otherwise (i.e., if this dialog was
    cancelled).

    If this file already exists, this dialog additionally requires the user to
    accept the subsequent overwriting of this file.

    See Also
    ----------
    :func:`select_file_read`
        Further details.
    '''

    # Avoid circular import dependencies.
    from betsee.util.path import guipath

    # Return the user-based result of displaying this path dialog.
    return guipath.select_path(
        *args, dialog_callable=QFileDialog.getSaveFileName, **kwargs)


@type_check
def select_file_yaml_save(*args, **kwargs) -> StrOrNoneTypes:
    '''
    Display a dialog requesting the user to select an existing YAML file to be
    subsequently opened for in-place saving and hence overwriting, returning the
    absolute filename of this file if this dialog was not cancelled *or* ``None``
    otherwise (i.e., if this dialog was cancelled).

    See Also
    ----------
    :func:`select_file_save`
        Further details.
    '''

    return select_file_save(
        *args, label_to_filetypes=_YAML_LABEL_TO_FILETYPES, **kwargs)
