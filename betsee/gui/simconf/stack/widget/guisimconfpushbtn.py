#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`QPushButton`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Slot
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
    interactively selecting simulation configuration paths.

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

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfImagePushButton(QBetseeSimConfPushButtonABC):
    '''
    :mod:`QPushButton`-based widget subclass interactively selecting simulation
    configuration images whose filetypes are supported by the third-party image
    processing framework leveraged by BETSE itself: Pillow.

    See Also
    ----------
    :func:`guifile.select_image_read`
        Further details.
    '''

    # ..................{ SUPERCLASS                         }..................
    @type_check
    def _get_pathname(self, pathname: str) -> StrOrNoneTypes:

        # Avoid circular import dependencies.
        from betsee.util.path import guifile

        # Return the absolute or relative filename of an existing selected image
        # of the parent directory containing the current simulation
        # configuration if this dialog was not canceled *OR* "None" otherwise.
        return guifile.select_image_read(
            init_pathname=pathname,
            parent_dirname=self._sim_conf.dirname)


class QBetseeSimConfSubdirPushButton(QBetseeSimConfPushButtonABC):
    '''
    :mod:`QPushButton`-based widget subclass interactively selecting simulation
    configuration subdirectories of arbitrary parent directories.

    For relocatability (i.e., to permit end users to trivially move simulation
    configurations to different directories), the textual "buddy" widget
    associated with this button displays only the relative pathname of these
    subdirectories with respect to their parent directories; their absolute
    pathnames are _not_ displayed.

    See Also
    ----------
    :func:`guidir.select_subdir`
        Further details.
    '''

    # ..................{ SUPERCLASS                         }..................
    @type_check
    def _get_pathname(self, pathname: str) -> StrOrNoneTypes:

        # Avoid circular import dependencies.
        from betsee.util.path import guidir

        # If the pathname of this subdirectory is absolute, raise an exception.
        pathnames.die_if_absolute(pathname)

        # Return the relative pathname of an existing selected subdirectory of
        # the parent directory containing the current simulation configuration
        # if this dialog was not canceled *OR* "None" otherwise.
        return guidir.select_subdir(
            init_pathname=pathname,
            parent_dirname=self._sim_conf.dirname)
