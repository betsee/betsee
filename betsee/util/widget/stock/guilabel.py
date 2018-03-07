#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QLabel` subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import Qt, QCoreApplication, QSize  #, Signal, Slot
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QFrame, QLabel, QScrollArea, QSizePolicy
from betse.lib.pil import pils
from betse.util.io.log import logs
from betse.util.path import pathnames, paths
from betse.util.type.cls import classes
from betse.util.type.text import mls
from betse.util.type.types import type_check
from betsee.util.path import guifiletype
from betsee.util.widget import guiwdg
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUBCLASSES                         }....................
#FIXME: Submit this class once working as a novel solution to:
#    https://stackoverflow.com/questions/8211982/qt-resizing-a-qlabel-containing-a-qpixmap-while-keeping-its-aspect-ratio
#
#In particular, note that the principal deficiency of the top-rated answer is
#its use of:
#
#    # This...
#    pixmap_size_new = self.size()
#
#    # ...rather than this.
#    pixmap_size_new = self.sizeHint()
#
#The former instructs Qt to gradually increase the size of this label to this
#preferred size over a lengthy (and hence unacceptable) period of ten seconds!

class QBetseeLabelImage(QBetseeObjectMixin, QLabel):
    '''
    :mod:`QLabel`-based widget preserving the aspect ratio of the optional
    **pixmap** (i.e., in-memory image) added to this widget.

    By default, pixmaps added to :class:`QLabel` widgets are stretched to fit
    layout requirements -- commonly resulting in unappealing deformation of
    pixmaps added to these widgets. This derivative widget corrects this harmful
    behaviour by constraining the aspect ratio of this widget to be equal to the
    aspect ratio of the contained pixmap if any. To do so:

    * The width of this widget is always preserved as is.
    * The height of this widget is dynamically set to be the width of this
      widget multiplied by the aspect ratio of the contained pixmap if any, thus
      constraining the aspect ratio of this widget to be the same.

    This widget supports all image filetypes supported by standard Qt widgets.
    Specifically, all images whose filetypes are in the system-specific set
    returned by the :func:`betse.util.path.guifiletype.get_image_read_filetypes`
    function are explicitly supported.

    Caveats
    ----------
    This widget *must* be contained in a :class:`QScrollArea` widget.
    Equivalently, some transitive parent widget of this widget *must* be a
    :class:`QScrollArea` widget. If this is *not* the case when the :meth:`init`
    method finalizing this widget's initialization is called, that method
    explicitly raises an exception.

    Why? Because size hints for widgets residing outside of :class:`QScrollArea`
    widgets are typically silently ignored. This widget declares a size hint
    preserving the aspect ratio of its pixmap. If this size hint is silently
    ignored, this pixmap's aspect ratio will typically be silently violated.
    Since this widget type exists *only* to preserve this aspect ratio, this
    constitutes a fatal error.

    Recursion
    ----------
    There exists circumstantial online evidence that this widget can
    *effectively* induces infinite recursion in edge cases. Specifically, `it
    has been asserted elsewhere <recursion claim_>`__ that:

    * :meth:`QBetseeLabelImage.resizeEvent` calls
      :meth:`QBetseeLabelImage.setPixmap`.
    * :meth:`QBetseeLabelImage.setPixmap` calls
      :meth:`QLabel.setPixmap`.
    * :meth:`QLabel.setPixmap` calls :meth:`QLabel.updateLabel`.
    * :meth:`QLabel.updateLabel` calls :meth:`QLabel.updateGeometry`.
    * :meth:`QLabel.updateGeometry` may conditionally call :meth:`QLabel.resize`
      in edge cases.
    * :meth:`QLabel.resize` queues a new resize event for this label.
    * The Qt event loop processes this event by calling
      :meth:`QLabel.resizeEvent`, completing the recursive cycle.

    Technically speaking, no recursive cycle exists. Due to indirection
    introduced by event handling, the :meth:`QLabel.resize` and
    :meth:`QLabel.resizeEvent` methods are called in different branches of the
    call stack. Ergo, the above call chain should noticeably degrade application
    performance *without* fatally exhausting the stack. Sadly, since these
    methods are called sequentially rather than recursively, detecting and
    guarding against this edge case is infeasible. (It could be worse.)

    Practically speaking, we were unable to replicate this worst-case issue.
    Since we cannot replicate it, we cannot resolve it. We have elected instead
    to do nothing, accepting that this may become a demonstrable issue later.

    .. _recursion claim:
        https://stackoverflow.com/a/41403419/2809027

    Attributes
    ----------
    _pixmap : (QPixmap, NoneType)
        Pixmap added to this widget by an external call to the :meth:`setPixmap`
        method if that method has been called *or* ``None`` otherwise.

    See Also
    ----------
    https://stackoverflow.com/a/22618496/2809027
        StackOverflow answer inspiring this implementation.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._pixmap = None

        # Lightly border this label's pixmap for aesthetics.
        self.setFrameShape(QFrame.StyledPanel)

        # Prevent Qt from auto-rescaling either this label's pixmap or text, as
        # Qt does so in a manner *NOT* preserving the aspect ratio of the
        # former. Although this boolean is already disabled by default, enforce
        # this constraint for safety by explicitly disabling this boolean.
        self.setScaledContents(False)


    def init(self) -> None:
        '''
        Finalize the initialization of this widget.

        Raises
        ----------
        BetseePySideWidgetException
            If this widget is *not* contained in a :class:`QScrollArea` widget.
            See the class docstring for commentary.
        '''

        # Finalize the initialization of our superclass.
        super().init()

        # If this widget is *NOT* in a scroll area, raise an exception.
        guiwdg.die_unless_widget_parent_satisfies(
            widget=self,
            predicate=lambda widget_parent: isinstance(
                widget_parent, QScrollArea))

    # ..................{ PROPERTIES                         }..................
    @property
    def _is_pixmap(self) -> bool:
        '''
        ``True`` only if this label has a pixmap that is *not* the null pixmap.
        '''

        return self._pixmap is not None and not self._pixmap.isNull()

    # ..................{ SUPERCLASS ~ getters               }..................
    def sizeHint(self) -> QSize:
        '''
        Preferred size for this label, defined in a manner preserving both this
        label's existing width *and* this label's pixmap's aspect ratio.

        If this property is *not* overridden in this manner, the
        :meth:`setPixmap` method rescaling this pixmap and hence this label
        gradually increase the size of this label to this preferred size over a
        lengthy (and hence unacceptable) period of nearly ten seconds. Hence,
        overriding this is non-optional.
        '''

        # Current width of this label.
        label_width = self.width()

        # Return this label's preferred size in a manner preserving both this
        # label's existing width *AND* this label's pixmap's aspect ratio.
        return QSize(label_width, self.heightForWidth(label_width))


    def heightForWidth(self, label_width_new: int) -> int:
        '''
        Preferred height for this widget given the passed width if this widget's
        height depend on its width *or* -1 otherwise (i.e., if this widget's
        height is independent of its width).

        Parameters
        ----------
        label_width_new : int
            Width that this widget is being externally resized to.

        Returns
        ----------
        int
            Either:
            * If this widget contains a **non-null pixmap** (i.e., if the
              :meth:`setPixmap` method of this widget has been passed a pixmap
              whose :meth:`QPixmap.isNull` method returns ``False``), the
              returned height is guaranteed to preserve the aspect ratio of this
              pixmap with respect to the passed width.
            * Else (i.e., if this widget either contains no pixmap *or* contains
              the null pixmap), the returned height is this widget's current
              height unmodified.
        '''

        # If this label has a non-null pixmap, return a height preserving the
        # aspect ratio of this pixmap with respect to this width, trivially
        # rounded from a float to integer.
        if self._is_pixmap:
            return round(
                (self._pixmap.height() * label_width_new) /
                 self._pixmap.width())
        # Else, this label either has no pixmap *OR* has the null pixmap. In
        # either case, return this label's current height as is.
        else:
            return self.height()

    # ..................{ SUPERCLASS ~ setters               }..................
    @type_check
    def setPixmap(self, pixmap: QPixmap) -> None:
        '''
        Set this label's pixmap to the passed pixmap, internally rescaled to
        this label's current size.

        Under ideal circumstances, this label's current size is identical to
        this label's **preferred size** (i.e., the size returned by the
        :meth:`sizeHint` method). Since the latter is overridden by this
        widget to preserve the aspect ratio of this pixmap, this pixmap's new:

        * Width will be the current width of this label.
        * Height will be a function of this width preserving the aspect ratio of
          this pixmap.

        For aesthetics, this pixmap is rescaled with smooth bilinear filtering
        rather than with the default non-smooth transition.

        Parameters
        ----------
        pixmap : QPixmap
            Pixmap to be set as this label's pixmap
        '''

        # Classify this pixmap and dimensions thereof for usability.
        self._pixmap = pixmap

        # Current size of this pixmap for logging purposes.
        pixmap_size_old = pixmap.size()

        # Size to resize pixmap to, equal to the preferred size of this label.
        # This size preserves the aspect ratio of this pixmap such that its:
        #
        # * Width is the current width of this label.
        # * Height is a function of this width preserving the aspect ratio of
        #   this pixmap.
        #
        # Ideally, the size() method returning the current size of this label
        # rather than the sizeHint() method returning only a preferred size
        # would be called. This widget has overriden all available size-specific
        # hint methods to return sizes preserving the aspect ratio of this
        # pixmap, but the size returned by the size() method still insists on
        # ignoring these hints in common edge cases.
        #
        # In particular, supplanting sizeHint() by size() here instructs Qt to
        # gradually increase the size of this label to this preferred size over
        # a lengthy (and hence unacceptable) period of nearly ten seconds.
        pixmap_size_new = self.sizeHint()

        # Log this rescaling.
        logs.log_debug(
            'Rescaling label pixmap from %dx%d to %dx%d...',
            pixmap_size_old.width(),
            pixmap_size_old.height(),
            pixmap_size_new.width(),
            pixmap_size_new.height())

        # Pixmap rescaled from the passed pixmap.
        pixmap_rescaled = pixmap.scaled(
            pixmap_size_new,  # * pixmap.devicePixelRatioF(),

            # Preserve the passed pixmap's existing aspect ratio. While the
            # passed size *SHOULD* already ensure this, we go the distance.
            Qt.KeepAspectRatio,

            # Rescale this pixmap with smooth bilinear filtering. By default,
            # pixmaps are rescaled abruptly rather than with this transition.
            Qt.SmoothTransformation,
        )
        # scaled.setDevicePixelRatio(devicePixelRatioF())

        # Set this label's pixmap to this rescaled pixmap.
        super().setPixmap(pixmap_rescaled)

    # ..................{ SUPERCLASS ~ events                }..................
    def resizeEvent(self, *args, **kwargs) -> None:

        # Defer to our superclass implementation.
        super().resizeEvent(*args, **kwargs)

        # If this label has a pixmap that is *NOT* the null pixmap...
        if self._is_pixmap:
            logs.log_debug('Rescaling pixmap after resizing label...')
            # Rescale this pixmap to the desired size of this widget.
            self.setPixmap(self._pixmap)

    # ..................{ LOADERS                            }..................
    @type_check
    def load_image(self, filename: str) -> None:
        '''
        Load the image with the passed filename as this label's pixmap in a
        sensible manner preserving the aspect ratio of this image.

        For safety, this method preferentially displays otherwise fatal errors
        resulting from this loading process as non-fatal warnings set as this
        label's text. Since this widget is typically *only* leveraged as an
        image previewer, the failure to preview arbitrary user-defined images of
        dubious origin, quality, and contents and possibly unsupported filetype
        should *not* halt the entire application. Ergo, it doesn't.

        Parameters
        ----------
        filename : str
            Absolute or relative filename of the image to be loaded.
        '''

        # Basename of this image's filename.
        basename = pathnames.get_basename(filename)

        # Filetype of this image if any *OR* "None" otherwise.
        filetype = pathnames.get_filetype_undotted_or_none(filename)

        # Log this preview attempt.
        logs.log_debug('Previewing image "%s"...', basename)

        # Attempt to...
        try:
            # If this image does *NOT* exist or does but is unreadable by the
            # current user, show a non-fatal warning and return.
            if not paths.is_readable(filename):
                self._warn(QCoreApplication.translate('QBetseeLabelImage',
                    'Image "{0}" not found or unreadable.'.format(filename)))
                return
            # Else, this image exists and is readable by the current user.

            # If this image has no filetype, show a warning and return.
            if filetype is None:
                self._warn(QCoreApplication.translate('QBetseeLabelImage',
                    'Image "{0}" has no filetype.'.format(filename)))
                return
            # Else, this image has a filetype.

            # Set of all image filetypes readable by Pillow.
            filetypes_pil = pils.get_filetypes()

            # Set of all image filetypes readable by Qt.
            filetypes_qt = guifiletype.get_image_read_filetypes()

            # If this image is unreadable by Pillow, show a warning and return.
            if filetype not in filetypes_pil:
                self._warn(QCoreApplication.translate('QBetseeLabelImage',
                    'Image filetype "{0}" unrecognized by Pillow.'.format(
                        filetype)))
                return
            # Else, this image is readable by Pillow and hence BETSE and is thus
            # presumably valid.

            # If this image is unreadable by Qt, show a warning and return.
            # Since Qt reads fewer image filetypes than Pillow, this condition
            # is effectively ignorable from the perspective of the end user.
            if filetype not in filetypes_qt:
                self._warn(QCoreApplication.translate('QBetseeLabelImage',
                    'Image filetype "{0}" not previewable.'.format(
                        filetype)))
                return
            # Else, this image is readable by both Pillow *AND* Qt.

            # In-memory pixmap trivially loaded from this on-disk image.
            pixmap = QPixmap(filename)

            # Set this label's pixmap as this pixmap.
            self.setPixmap(pixmap)

            # Resize this label to this message.
            # self.adjustSize()
        # If doing so raises an exception...
        except Exception as exception:
            # Exception type.
            exception_type = classes.get_class_name(exception)

            # Exception message.
            exception_message = str(exception)

            # Display this exception message as a non-fatal warning.
            self._warn(QCoreApplication.translate(
                'QBetseeLabelImage',
                'Image "{0}" preview failed with "{1}": {2}'.format(
                    basename,
                    exception_type,
                    exception_message)))

    # ..................{ WARNERS                            }..................
    @type_check
    def _warn(self, warning: str) -> None:
        '''
        Set the passed human-readable message as this label's text, log this
        message as a warning, and remove this label's existing pixmap if any.

        For clarity, this message is embedded in rich text (i.e., HTML) visually
        accentuating this message in a manner indicative of warnings -- notably,
        with boldened red text.

        Caveats
        ----------
        **This message is logged as is and hence assumed to be plaintext.** All
        HTML syntax (e.g., ``&amp;``, ``<table>``) embedded in this message is
        escaped for safety, preventing this message from being erroneously
        misinterpreted as rich text.

        Parameters
        ----------
        warning : str
            Human-readable warning message to be displayed as this label's text.
        '''

        # Log this warning.
        logs.log_warning(warning)

        # Remove this label's existing pixmap if any.
        self.clear()

        # Warning message with all embedded HTML syntax (e.g., "&amp;", "<b>")
        # escaped for safety.
        warning_escaped = mls.escape_ml(warning)

        # Set this label's text to rich text embedding this message in a
        # visually distinctive manner indicative of a warning.
        self._image_label.setText(QCoreApplication.translate(
            'QBetseeLabelImage',
            '<span style="color: #aa0000;"><b>Warning:</b> {0}</span>'.format(
                warning_escaped)))

        # Resize this label to this message.
        self.adjustSize()
