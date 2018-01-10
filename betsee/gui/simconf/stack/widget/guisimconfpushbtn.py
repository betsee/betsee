#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`QPushButton`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QLineEdit, QPushButton
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.path import pathnames
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.gui.simconf.stack.widget.abc.guisimconfwdg import (
    QBetseeWidgetMixinSimConf)

# ....................{ SUPERCLASSES                       }....................
class QBetseeSimConfPushButtonABC(QBetseeWidgetMixinSimConf, QPushButton):
    '''
    Abstract base class of all :mod:`QPushButton`-based widget subclasses
    enabling simulation configuration paths to be interactively selected.

    Subclasses of this superclass typically display a dialog on being
    interactively clicked, which:

    * Requests the user select a path satisfying various subclass-specific
      constraints (e.g., image, subdirectory).
    * Sets the contents of an associated :mod:`QLineEdit`-based "buddy" widget
      to the selected path.

    Attributes
    ----------
    _line_edit : QLineEdit
        Textual "buddy" widget conceptually associated with this button,
        editing the pathname selected by the user from this dialog.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._line_edit = None


    @type_check
    def init(self, line_edit: QLineEdit, *args, **kwargs) -> None:
        '''
        Finalize this button's initialization.

        Notably, this method connects this button's click signal to a slot
        defined by this class displaying a subclass-specific path dialog.

        Parameters
        ----------
        line_edit : QLineEdit
            Textual "buddy" widget associated with this button.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Finalize the initialization of our superclass.
        super().init(*args, **kwargs)

        # Classify all passed parameters.
        self._line_edit = line_edit

        # Connect this button's click signal to a slot displaying this dialog
        # *AFTER* defining all instance variables accessed by this slot.
        self.clicked.connect(self._select_path)

    # ..................{ SLOTS                              }..................
    @Slot()
    def _select_path(self) -> None:
        '''
        Slot displaying a dialog requesting the user select a possibly
        non-existing path satisfying various subclass-specific constraints
        (e.g., image, subdirectory) *and* setting the contents of an associated
        :mod:`QLineEdit`-based "buddy" widget to the selected pathname.

        This slot is connected to the :attr:`clicked` signal at widget
        finalization time, for safety.
        '''

        #
        # Relative pathname of the currently configured subdirectory of this
        # parent directory to initially display in this dialog.
        pathname = self._line_edit.text()

        # Relative pathname of an existing subdirectory of this parent if this
        # dialog was not canceled *OR* "None" otherwise.
        pathname = self._get_pathname(pathname)

        # If this dialog was *NOT* canceled...
        if pathname is not None:
            # Set the contents of our buddy widget to this pathname.
            self._line_edit.setText(pathname)

    # ..................{ SUBCLASS                           }..................
    # Subclasses are required to implement the following methods.

    def _get_pathname(self, pathname: str) -> StrOrNoneTypes:
        '''
        Possibly non-existing pathname interactively selected by the user from a
        subclass-specific dialog displayed by this method if the user did not
        cancel this dialog *or* ``None`` otherwise (i.e., if the user cancelled
        this dialog).

        Parameters
        ----------
        pathname : str
            Pathname of the path to be initially displayed by this dialog,
            corresponding to the current path in this simulation configuration.

        Returns
        ----------
        StrOrNoneTypes
            Either:
            * If this dialog was *not* cancelled, the possibly non-existing
              pathname selected from this dialog.
            * Else, ``None``.
        '''

        raise BetseMethodUnimplementedException()

# ....................{ SUBCLASSES ~ subdir                }....................
#FIXME: Implement a corresponding "QBetseeSimConfImagePushButton" subclass
#internally calling betsee.util.path.guifile.select_image_read().

class QBetseeSimConfSubdirPushButton(QBetseeSimConfPushButtonABC):
    '''
    :mod:`QPushButton`-based widget subclass enabling simulation configuration
    subdirectories of arbitrary parent directories to be interactively selected.

    To permit simulation configurations to be trivially moved to different
    directories, the textual "buddy" widget associated with this button displays
    only the relative pathname of these subdirectories with respect to their
    parent directories.
    '''

    # ..................{ SUPERCLASS                         }..................
    @type_check
    def _get_pathname(self, pathname: str) -> StrOrNoneTypes:

        # Avoid circular import dependencies.
        from betsee.util.path import guidir

        # Relative pathname of the current subdirectory of this parent directory
        # to initially display in this dialog, renamed for clarity.
        subdirname = pathname

        # If this pathname is absolute, raise an exception.
        pathnames.die_if_absolute(subdirname)

        # Absolute pathname of the directory containing the current simulation
        # configuration to request the user select a subdirectory of.
        parent_dirname = self._sim_conf.dirname

        # Absolute pathname of the currently configured subdirectory of this
        # parent directory to initially display in this dialog.
        current_dirname = pathnames.join(parent_dirname, subdirname)

        # Relative pathname of an existing subdirectory of this parent if this
        # dialog was not canceled *OR* "None" otherwise.
        subdirname = guidir.select_subdir(
            parent_dirname=parent_dirname, current_dirname=current_dirname)

        # If this dialog was *NOT* canceled and this pathname is absolute, raise
        # an exception.
        if subdirname is not None:
            pathnames.die_if_absolute(subdirname)

        # Return this relative pathname.
        return subdirname
