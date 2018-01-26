#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QLineEdit`-based simulation configuration widget subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, Signal, Slot
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QLineEdit, QPushButton
from betse.exceptions import BetseMethodUnimplementedException
from betse.lib.pil import pils
from betse.util.io.log import logs
from betse.util.path import pathnames, paths
from betse.util.type.text import mls
from betse.util.type.types import type_check, StrOrNoneTypes
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)
from betsee.util.path import guifiletype
from betsee.util.widget.abc.guiclipboardabc import (
    QBetseeClipboardScalarWidgetMixin)
from betsee.util.widget.stock.guilabel import QBetseeLabelImage

# ....................{ SUBCLASSES                         }....................
class QBetseeSimConfLineEdit(
    QBetseeClipboardScalarWidgetMixin,
    QBetseeSimConfEditScalarWidgetMixin,
    QLineEdit,
):
    '''
    Simulation configuration-specific line edit widget, interactively editing
    single-line strings backed by external simulation configuration files.
    '''

    # ..................{ SUPERCLASS ~ setter                }..................
    def setText(self, text_new: str) -> None:

        # Defer to the superclass setter.
        super().setText(text_new)

        # If this configuration is currently open, set the current value of this
        # simulation configuration alias to this widget's current value.
        self._set_alias_to_widget_value_if_sim_conf_open()

    # ..................{ MIXIN ~ property : read-only       }..................
    @property
    def undo_synopsis(self) -> str:
        return QCoreApplication.translate(
            'QBetseeSimConfLineEdit', 'edits to a text box')


    @property
    def _finalize_widget_change_signal(self) -> Signal:
        return self.editingFinished

    # ..................{ MIXIN ~ property : value           }..................
    @property
    def widget_value(self) -> str:
        return self.text()


    @widget_value.setter
    @type_check
    def widget_value(self, widget_value: str) -> None:

        # If this value is *NOT* a string, coerce this value into a string.
        # Since effectively all scalar values are safely coercable into strings
        # (due to their implementation of the special __str__() method), this is
        # guaranteed to be safe and hence need *NOT* be checked.
        if not isinstance(widget_value, str):
            widget_value = str(widget_value)

        # Set this widget's displayed value to the passed value by calling the
        # setText() method of our superclass rather than this subclass,
        # preventing infinite recursion. (See the superclass method docstring.)
        super().setText(widget_value)


    def _reset_widget_value(self) -> None:
        self.widget_value = ''

# ....................{ SUBCLASSES ~ pathname              }....................
class QBetseeSimConfPathnameLineEditABC(QBetseeSimConfLineEdit):
    '''
    Abstract base class of all simulation configuration-specific pathname line
    edit widget subclasses, interactively editing pathnames backed by external
    simulation configuration files.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def init(self, push_btn: QPushButton, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this line edit, associated with all
        passed **sibling buddy widgets** (i.e., widgets spatially adjacent to
        this line edit, whose initialization is finalized by this method in a
        manner informing these widgets of their association to this line edit).

        Parameters
        ----------
        push_btn : QPushButton
            Push button "buddy" associated with this line edit. To display a
            path dialog selecting this pathname when this button is clicked,
            this method connects the :meth:`QPushButton.clicked` signal of this
            button to the :meth:`_set_text_to_pathname_selected` slot of this
            line edit. By convention, this button is typically labelled
            "Browse..." and situated to the right of this line edit.

        All remaining parameters are passed as is to the superclass
        :meth:`QBetseeSimConfEditScalarWidgetMixin.init` method.
        '''

        # Initialize our superclass with all remaining arguments.
        super().init(*args, **kwargs)

        # Connect this button's click signal to a slot displaying a path dialog
        # yielding the pathname to be displayed by this line edit.
        push_btn.clicked.connect(self._set_text_to_pathname_selected)

    # ..................{ SLOTS                              }..................
    @Slot()
    def _set_text_to_pathname_selected(self) -> None:
        '''
        Slot setting the text displayed by this line edit to the possibly
        non-existing pathname selected by a subclass-specific path dialog
        satisfying various constraints (e.g., image, subdirectory).

        This slot is connected to the :attr:`clicked` signal of the push button
        associated with this line edit at widget finalization time, for safety.
        '''

        # Pathname to initially display in the following dialog.
        old_pathname = self.text()

        # Pathname selected from a dialog displayed on clicking the push button
        # associated with this line edit if not cancelled *OR* "None" otherwise.
        new_pathname = self._select_pathname(old_pathname)

        # If this dialog was *NOT* canceled, set the text displayed by this line
        # edit to this pathname.
        if new_pathname is not None:
            self.setText(new_pathname)

    # ..................{ SUBCLASS                           }..................
    # Subclasses are required to implement the following methods.

    @type_check
    def _select_pathname(self, init_pathname: str) -> StrOrNoneTypes:
        '''
        Possibly non-existing pathname interactively selected by the user on
        clicking the push button buddy associated with this line edit from a
        subclass-specific dialog displayed by this method if the user did not
        cancel this dialog *or* ``None`` otherwise (i.e., if the user cancelled
        this dialog).

        Parameters
        ----------
        init_pathname : str
            Pathname of the path to be initially displayed by this dialog (e.g.,
            as externally specified by this simulation configuration).

        Returns
        ----------
        StrOrNoneTypes
            Either:
            * If this dialog was *not* cancelled, the possibly non-existing
              pathname selected from this dialog.
            * Else, ``None``.
        '''

        raise BetseMethodUnimplementedException()

# ....................{ SUBCLASSES ~ pathname : image      }....................
class QBetseeSimConfPathnameImageLineEdit(QBetseeSimConfPathnameLineEditABC):
    '''
    Simulation configuration-specific **image filename** (i.e., filenames with
    filetypes recognized by Pillow, the third-party image processing framework
    leveraged by BETSE itself) line edit widget, interactively editing image
    filenames backed by external simulation configuration files.

    Attributes
    ----------
    _image_label : QLabel
        Label "buddy" associated with this line edit. To preview the image whose
        filename is the text displayed by this line edit, this label's pixmap is
        read from this filename. By convention, this label is typically situated
        below this line edit.

    See Also
    ----------
    :func:`guifile.select_image_read`
        Further details.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._image_label = None


    @type_check
    def init(self, image_label: QBetseeLabelImage, *args, **kwargs) -> None:
        '''
        Finalize the initialization of this line edit, associated with all
        passed **sibling buddy widgets** (i.e., widgets spatially adjacent to
        this line edit, whose initialization is finalized by this method in a
        manner informing these widgets of their association to this line edit).

        Parameters
        ----------
        image_label : QBetseeLabelImage
            Label "buddy" associated with this line edit. To preview the image
            whose filename is the text displayed by this line edit, this label's
            pixmap is read from this filename. By convention, this label is
            typically situated below this line edit. To preserve this image's
            aspect ratio, this widget is required to be an instance of the
            application-specific :class:`QBetseeLabelImage` class rather than
            application-agnostic :class:`QLabel` class, which does *not*
            preserve this image's aspect ratio.

        All remaining parameters are passed as is to the superclass
        :meth:`QBetseeSimConfPathnameLineEditABC.init` method.
        '''

        # Initialize our superclass with all remaining arguments.
        super().init(*args, **kwargs)

        # Classify all passed parameters.
        self._image_label = image_label

        # Finalize the initialization of this widget if needed.
        self._image_label.init_if_needed()

        # Instruct this label to auto-wrap long lines, required to display
        # non-fatal warnings subsequently added as this label's text in a
        # DPI-independent manner.
        self._image_label.setWordWrap(True)

    # ..................{ SUPERCLASS ~ getters               }..................
    # Called on opening and closing simulation configurations.
    def _get_widget_from_alias_value(self) -> object:

        # Value of the alias associated with this widget, equivalent to the
        # relative or absolute filename of expected image.
        image_filename = super()._get_widget_from_alias_value()

        # Preview an image only if a simulation configuration is open.
        self._image_label.setVisible(self._is_sim_open)

        # If a simulation configuration is open, preview this image.
        self._preview_image_if_sim_open(image_filename)

        # Return this value.
        return image_filename


    # Called on each user edit of this widget's value.
    def _get_alias_from_widget_value(self) -> object:

        # This widget's currently displayed value, equivalent to the relative or
        # absolute filename of the expected image.
        image_filename = super()._get_alias_from_widget_value()

        # If a simulation configuration is open, preview this image.
        self._preview_image_if_sim_open(image_filename)

        # Return this filename.
        return image_filename

    # ..................{ PREVIEWERS                         }..................
    #FIXME: Sadly, labels fail to automatically scroll their pixmap contents. To
    #do so, we'll need to generalize this class as follows:
    #
    #* Define a new "betsee.util.widget.stock.guiscrollarea" submodule.
    #* In this submodule:
    #  * Define a "QBetseeScrollImage" subclass of the "QScrollArea" class.
    #  * In the QBetseeScrollImage.__init__() method:
    #    * Instantiate and add a new "QLabel" widget to this scroll area.
    #    * Presumably set other properties of both this scroll area and this
    #      label facilitating image display. In particular, we'll want to:
    #
    #      #FIXME: This may or may *NOT* be necessary. Try without, first.
    #      # Automatically resize this label to the size of this image.
    #      self._image_label.setSizePolicy(
    #          QSizePolicy.Ignored, QSizePolicy.Ignored);
    #      self._image_label.setScaledContents(True)
    #
    #    * Shift the majority of the content in this private
    #      _preview_image_if_sim_open() method into a public show_image() method
    #      with a similar signature, but ideally generalized to accept either a
    #      filename *OR* "None" (in which case the text "N/A" should be shown):
    #
    #      @type_check
    #      def show_image(self, image_filename: StrOrNoneTypes) -> None:
    #
    #* Revise the init() method defined above to accept a "QBetseeScrollImage"
    #  rather than "QLabel" parameter.
    #* Replace the "QLabel" widget accompanying this line edit in Qt Creator
    #  with a "QBetseeScrollImage" widget promoted from "QScrollArea".
    #
    #For a detailed example, see the following StackOverflow entry:
    #https://stackoverflow.com/a/10988109/2809027
    #FIXME: O.K., we absolutely need to pursue the above refactoring. Why?
    #Because Qt Designer implicitly adds a "QWidget" named
    #"scrollAreaWidgetContents" to *ALL* "QScrollArea" widgets. The desired
    #"QLabel" is then added as a child of this "QWidget" rather than this
    #"QScrollArea". This is both silly and appears to prevent us from sanely
    #resizing the image. Or maybe not? In any case, this indirection only
    #obfuscates the underlying logic. Eliminate this by pursuing the above
    #approach. Note that the "scrollAreaWidgetContents" widget automatically
    #added to "QScrollArea" widgets should be removed in the
    #QBetseeScrollImage.init() method (...not __init__() method!), presumably
    #by simply calling "self.setWidget(image_label)" and hence replacing the
    #previously set "scrollAreaWidgetContents" widget for this scroll area. For
    #further discussion, see this related StackOverflow question:
    #
    #https://stackoverflow.com/a/7507221/2809027
    #FIXME: Test this method with common edge cases, including:
    #
    #* A filename of filetype unrecognized by Pillow.
    #* A filename of filetype unrecognized by Qt.
    #* A file of recognized filetype that isn't actually an image.
    @type_check
    def _preview_image_if_sim_open(self, image_filename: str) -> None:
        '''
        Display a preview of the image with the passed filename as the pixmap of
        the label associated with this line edit if this image is previewable
        *or* log and/or display a non-fatal warning otherwise.

        If no simulation configuration is open, this method safely reduces to a
        noop without erroneously handling this image.

        Parameters
        ----------
        image_filename : str
            Absolute or relative filename of the image to be previewed.
        '''

        # Remove any prior content (e.g., image, text) displayed by this label,
        # regardless of whether subsequent logic displays any new such content.
        self._image_label.clear()

        # If no simulation configuration is open...
        if not self._is_sim_open:
            # Display a placeholder message.
            self._image_label.setText(QCoreApplication.translate(
                'QBetseeSimConfPathnameImageLineEdit', 'N/A'))

            # That's all she wrote.
            return
        # Else, a simulation configuration is open.

        #FIXME: Refactor all of the following logic as follows:
        #
        #* Define a new QBetseeLabelImage.load_image() method. This high-level
        #  method wraps the low-level QLabel.setPixmap() method with all of the
        #  following logic and should have the following signature:
        #
        #    @type_check
        #    def load_image(self, filename: str) -> None:
        #
        #* Shift all of the following logic into this load_image() method.
        #* For convenience, define a new QBetseeLabelImage.warn() method as well
        #  with signature resembling:
        #
        #    @type_check
        #    def warn(self, warning: str) -> None:
        #
        #  This method should:
        #  * Log this warning.
        #  * Clear this label's existing content.
        #  * Set this label's text to this warning.
        #  * Calls "self.adjustSize()".
        #
        #  Naturally, however, it remains the caller's responsibility to
        #  translate this warning.

        # Basename of this image's filename.
        image_basename = pathnames.get_basename(image_filename)

        # Filetype of this image if any *OR* "None" otherwise.
        image_filetype = pathnames.get_filetype_undotted_or_none(image_filename)

        # Log this preview attempt.
        logs.log_debug('Previewing image "%s"...', image_basename)

        # If this image does *NOT* exist or does but is unreadable by the
        # current user...
        if not paths.is_readable(image_filename):
            # Log a non-fatal warning.
            logs.log_warning(
                'Image "%s" not found or unreadable.', image_filename)

            # Display a non-fatal warning as this label's text.
            self._image_label.setText(QCoreApplication.translate(
                'QBetseeSimConfPathnameImageLineEdit',
                '<b>Warning:</b> image "{0}" not found or unreadable.'.format(
                    image_filename)))

            #FIXME: Do this for every warning as well, obviously.
            self._image_label.adjustSize()
        # Else, this image exists and is readable by the current user.
        #
        # if this image has a filetype...
        if image_filetype is not None:
            # Set of all image filetypes readable by Pillow.
            image_filetypes_pil = pils.get_filetypes()

            # Set of all image filetypes readable by Qt.
            image_filetypes_qt = guifiletype.get_image_read_filetypes()

            # If this image is unreadable by Pillow...
            if image_filetype not in image_filetypes_pil:
                # Log a non-fatal warning.
                logs.log_warning(
                    'Image filetype "%s" unrecognized by Pillow.',
                    image_filetype)

                # Display a non-fatal warning as this label's text.
                self._image_label.setText(QCoreApplication.translate(
                    'QBetseeSimConfPathnameImageLineEdit',
                    '<b>Warning:</b> image filetype "{0}" '
                    'unrecognized by Pillow.'.format(image_filetype)))
            # Else, this image is readable by Pillow.
            #
            # If this image is unreadable by Qt, log a non-fatal warning. Note
            # that this warning is intentionally *NOT* displayed as this label's
            # text. Since this image is readable by Pillow, this image is
            # readable by BETSE (and is presumably valid). Since Qt reads
            # substantially fewer image filetypes than Pillow, this condition is
            # effectively ignorable from the perspective of the end user.
            elif image_filetype not in image_filetypes_qt:
                logs.log_warning(
                    'Image filetype "%s" unrecognized by Qt.', image_filetype)
            # Else, this image is readable by both Pillow *AND* Qt.
            else:
                # Absolute filename of this desired image, localized into a
                # separate variable to permit the original filename to be
                # returned unmodified. If this filename is relative, convert
                # this into an absolute filename relative to this simulation
                # configuration's top-level directory.
                image_filename_absolute = (
                    image_filename if pathnames.is_absolute(image_filename) else
                    pathnames.join(self._sim_conf.dirname, image_filename))

                # Attempt to...
                try:
                    # Qt-specific pixmap deserialized from this filename.
                    image_pixmap = QPixmap(image_filename_absolute)

                    # (Pre)view this pixmap in the label associated with this
                    # line edit.
                    self._image_label.setPixmap(image_pixmap)
                    # self._image_label.resize(422, 422)
                    # self._image_label.adjustSize()
                # If doing so raises an exception...
                except Exception as exception:
                    # This exception's message.
                    exception_message = str(exception)

                    # Log this message as a non-fatal warning.
                    logs.log_warning(
                        'Previewing image "%s" failed with "%s": %s',
                        image_basename,
                        type(exception).__name__,
                        exception_message)

                    # Escape this message to avoid interpretation as HTML.
                    exception_message = mls.escape_ml(str(exception))

                    # Display this exception message as a non-fatal warning
                    # replacing any prior content displayed by this label.
                    self._image_label.setText(QCoreApplication.translate(
                        'QBetseeSimConfPathnameImageLineEdit',
                        '<b>Warning:</b> {0}'.format(exception_message)))

    # ..................{ SUPERCLASS ~ selectors             }..................
    @type_check
    def _select_pathname(self, init_pathname: str) -> StrOrNoneTypes:

        # Avoid circular import dependencies.
        from betsee.util.path import guifile

        # Return the absolute or relative filename of an existing selected image
        # of the parent directory containing the current simulation
        # configuration if this dialog was not canceled *OR* "None" otherwise.
        return guifile.select_image_read(
            init_pathname=init_pathname,
            parent_dirname=self._sim_conf.dirname)

# ....................{ SUBCLASSES ~ pathname : subdir     }....................
class QBetseeSimConfPathnameSubdirLineEdit(QBetseeSimConfPathnameLineEditABC):
    '''
    Simulation configuration-specific **subdirectory pathname** (i.e., pathnames
    of subdirectories of top-level simulation configuration directories) line
    edit widget, interactively editing subdirectory pathnames backed by external
    simulation configuration files.

    For relocatability (i.e., to permit end users to trivially move simulation
    configurations to different directories), this line edit displays only the
    relative pathname of these subdirectories with respect to their parent
    directories; their absolute pathnames are *not* displayed.

    See Also
    ----------
    :func:`guidir.select_subdir`
        Further details.
    '''

    # ..................{ SUPERCLASS                         }..................
    @type_check
    def _select_pathname(self, init_pathname: str) -> StrOrNoneTypes:

        # Avoid circular import dependencies.
        from betsee.util.path import guidir

        # If the pathname of this subdirectory is absolute, raise an exception.
        pathnames.die_if_absolute(init_pathname)

        # Return the relative pathname of an existing selected subdirectory of
        # the parent directory containing the current simulation configuration
        # if this dialog was not canceled *OR* "None" otherwise.
        return guidir.select_subdir(
            init_pathname=init_pathname,
            parent_dirname=self._sim_conf.dirname)
