#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QLabel` subclasses.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QSize  # Qt, QCoreApplication, Signal, Slot
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QFrame, QLabel, QSizePolicy
from betse.util.io.log import logs
from betse.util.type.types import type_check
# from betsee.util.widget.abc.guiwdgabc import QBetseeWidgetMixin

# ....................{ SUBCLASSES                         }....................
#FIXME: This label is still highly broken, in that it appears to require
#containment within a parent "QScrollArea". Failing to embed this label in such
#a parent forcefully cuts off the bottom of this label. That said, I believe
#I've finally discovered why: stack page widgets do *NOT* appear to support
#vertical scrolling by default. I... I don't even. We obviously need to enable
#vertical scrolling by default in *ALL* page widgets, so that's our first order
#of business on the next day of irksome toil, trouble, cauldron, and bubble.
#FIXME: Doing so appears thankfully easy. We'll need to:
#
#* Define a new "QScrollArea" widget for each page.
#* Shift all existing widgets in this page into this "QScrollArea" widget.
#* Embed this "QScrollArea" widget inside the existing "QGroupBox" widget.
#
#Maybe? If it's not that, it's probably the reverse. But the above is probably
#simpler, so let's give that a go first.

#FIXME: Submit this class once working as a novel solution to:
#    https://stackoverflow.com/questions/8211982/qt-resizing-a-qlabel-containing-a-qpixmap-while-keeping-its-aspect-ratio

# class QBetseeLabelImage(QBetseeWidgetMixin, QLabel):
class QBetseeLabelImage(QLabel):
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
      width multiplied by the aspect ratio of the contained pixmap if any, thus
      constraining the aspect ratio of this widget to be the same.

    This widget supports all image filetypes supported by standard Qt widgets.
    Specifically, all images whose filetypes are in the system-specific set
    returned by the :func:`betse.util.path.guifiletype.get_image_read_filetypes`
    function are explicitly supported.

    Attributes
    ----------
    _is_in_resizeEvent : bool
        ``True`` only if the current thread of execution is in the conditional
        branch of the :meth:`resizeEvent` event handler preserving the aspect
        ratio of this widget's pixmap. This boolean guards against infinite
        recursion in this handler induced by unwanted reentrancy. Specifically:
        * :meth:`QLabel.resizeEvent` effectively "calls"
          :meth:`QBetseeLabelImage.resizeEvent` by inheritance.
        * :meth:`QBetseeLabelImage.resizeEvent` calls
          :meth:`QBetseeLabelImage.setPixmap`.
        * :meth:`QBetseeLabelImage.setPixmap` calls
          :meth:`QLabel.setPixmap`.
        * :meth:`QLabel.setPixmap` calls :meth:`QLabel.updateGeometry`.
        * :meth:`QLabel.updateGeometry` calls :meth:`QLabel.resizeEvent` in
          edge cases, completing the recursive cycle.
    _pixmap : (QPixmap, NoneType)
        Pixmap added to this widget by an external call to the :meth:`setPixmap`
        method if that method has been called *or* ``None`` otherwise.
    _pixmap_height : IntOrNoneTypes
        Height in pixels of this pixmap if non-``None`` *or* ``None`` otherwise.
    _pixmap_width : IntOrNoneTypes
        Width in pixels of this pixmap if non-``None`` *or* ``None`` otherwise.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._is_in_resizeEvent = False
        self._pixmap = None
        self._pixmap_height = None
        self._pixmap_width = None

        #FIXME: This is... awful. Document why the "_is_in_resizeEvent" boolean
        #fails to suffice here.
        self._pixmap_size_new = None

        #FIXME: Document us up.
        #FIXME: Do we require both this and minimumSizeHint()?
        self.setMinimumSize(1, 1)

        #FIXME: Document us up.
        self.setFrameShape(QFrame.StyledPanel)

        #FIXME: Document us up.
        # self.setScaledContents(True)
        self.setScaledContents(False)

        # Non-default size policy permitting:
        #
        # * This label's width (but *NOT* height) to be arbitrarily resized by
        #   this label's parent layout or widget. Note that despite the use of
        #   an expanding policy for this label's height, this label's height
        #   remains a deterministic function of its width and hence is *NOT*
        #   arbitrarily resized in the same manner.
        # * This label's height to be constrained to be a function of its width.
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        size_policy.setHeightForWidth(True)

        # Set this label's size policy to this policy.
        self.setSizePolicy(size_policy)

    # ..................{ SUPERCLASS ~ getters               }..................
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

        # If this label either has no pixmap *OR* has the null pixmap, return
        # this label's current height unmodified.
        if self._pixmap is None or self._pixmap.isNull():
            return self.height()
        # Else, this label has a non-null pixmap. In this case, return a height
        # preserving the aspect ratio of this pixmap with respect to this width,
        # trivially rounded from a float to integer.
        else:
            return round(
                (self._pixmap_height * label_width_new) / self._pixmap_width)


    #FIXME: Docstring us up.
    #FIXME: Is this actually necessary? Try commenting us out, please.
    def sizeHint(self) -> QSize:

        label_width = self.width()
        return QSize(label_width, self.heightForWidth(label_width))


    def minimumSizeHint(self) -> QSize:
        '''
        Recommended minimum size for this widget.

        :class:`QLayout` will never resize this widget to a size smaller than
        this minimum size hint unless the :meth:`minimumSize` property is
        explicitly set on this widget *or* the size policy for this widget is
        set to :attr:`QSizePolicy.Ignore`. If the :meth:`minimumSize` property
        is explicitly set, this minimum size hint will be ignored.

        Ideally, the :meth:`minimumSize` property would be explicitly set in the
        :meth:`__init__` method for this widget to the desired minimum (e.g.,
        ``self.setMinimumSize(1, 1)``). Unfortunately, the default
        :meth:`minimumSizeHint` implementation for this widget unconditionally
        resets the size policy to the default size policy. To preserve a
        non-default size policy, this property *must* be reimplemented.
        '''

        return QSize(1, 1)

    # ..................{ SUPERCLASS ~ setters               }..................
    #FIXME: Document us up.
    @type_check
    def setPixmap(self, pixmap: QPixmap) -> None:

        # Classify the passed pixmap and this pixmap's dimensions, as an
        # extremely minar efficiency gain.
        self._pixmap = pixmap
        self._pixmap_height = pixmap.height()
        self._pixmap_width  = pixmap.width()

        # Current size of this label, possibly *NOT* respecting size hints.
        label_size_old = self.size()

        # Current size of this pixmap.
        pixmap_size_old = self._pixmap.size()

        # Desired size of this pixmap, equivalent to the preferred size of this
        # label. This size is guaranteed to preserve the aspect ratio of this
        # pixmap. Specifically, this size's:
        #
        # * Width is the current width of this label.
        # * Height is a function of this width preserving the aspect ratio of
        #   this pixmap.
        #
        # Ideally, the size() method returning the current size of this label
        # rather than the sizeHint() method returning only a hint would be
        # called. Unfortunately, although all possible size-specific hint
        # methods have been overriden to return sizes preserving the aspect
        # ratio of this pixmap, the size returned by the size() method still
        # insists on ignoring these hints in edge cases. *sigh*
        #label_size = self.size()
        pixmap_size_new = self.sizeHint()

        # Log this rescaling.
        logs.log_debug(
            'Rescaling label pixmap from %dx%d to %dx%d...',
            pixmap_size_old.width(),
            pixmap_size_old.height(),
            pixmap_size_new.width(),
            pixmap_size_new.height())

        # Pixmap rescaled from the passed pixmap.
        pixmap_rescaled = self._pixmap.scaled(
            pixmap_size_new,  # * pixmap.devicePixelRatioF(),

            # Preserve the passed pixmap's existing aspect ratio. While the
            # passed size *SHOULD* already ensure this, we go the distance.
            # Qt.KeepAspectRatio,

            # Rescale this pixmap with smooth bilinear filtering. By default,
            # pixmaps are rescaled abruptly rather than with this transition.
            # Qt.SmoothTransformation,
        )
        # scaled.setDevicePixelRatio(devicePixelRatioF())

        # Set this label's pixmap to this rescaled pixmap.
        super().setPixmap(pixmap_rescaled)

        # If the conditional branch in the resizeEvent() handler that calls this
        # method is *NOT* already being handled...
        # if not self._is_in_resizeEvent:
        # if self._is_in_resizeEvent <= 1:
        # if label_size_old != pixmap_size_new:

        # Log this resizing.
        logs.log_debug(
            'Rescaling label from %dx%d to %dx%d...',
            label_size_old.width(),
            label_size_old.height(),
            pixmap_size_new.width(),
            pixmap_size_new.height())

        #FIXME: Rename this boolean to something saner -- say,
        #"_is_setPixmap_callable". Then globally invert the state of this
        #boolean (e.g., from "False" to "True" and vice versa) to comply with
        #this saner nomenclature.

        # Prevent this branch from being erroneously reentered if the
        # call to setPixmap() induces a recursive call to this handler.
        # self._is_in_resizeEvent = True
        # self._is_in_resizeEvent += 1

        #FIXME: While significantly better, this still results in this method
        #being called twice in rapid succession.

        # If the conditional branch in the resizeEvent() handler that calls this
        # method is *NOT* already being handled...
        if self._pixmap_size_new != pixmap_size_new:
            self._pixmap_size_new = pixmap_size_new

            # Resize this label to this rescaled pixmap's size.
            self.resize(pixmap_size_new)

        # # Attempt to...
        # try:
        #     # Prevent this branch from being erroneously reentered if the
        #     # call to setPixmap() induces a recursive call to this handler.
        #     self._is_in_resizeEvent = True
        #     # self._is_in_resizeEvent += 1
        #
        #     # Resize this label to this rescaled pixmap's size.
        #     self.resize(pixmap_size_new)
        # # Regardless of whether doing so raises an exception, permit this
        # # branch to be entered on the next handling of this resize event.
        # finally:
        #     self._is_in_resizeEvent = False

    # ..................{ SUPERCLASS ~ events                }..................
    def resizeEvent(self, *args, **kwargs) -> None:

        # Defer to our superclass implementation.
        super().resizeEvent(*args, **kwargs)

        #FIXME: Compact this conditional.
        # If...
        if (
            # This label has a pixmap.
            self._pixmap is not None and
            # This pixmap is *NOT* the null pixmap.
            not self._pixmap.isNull()
        ):
            logs.log_debug('Rescaling pixmap after resizing label...')

            # Rescale this pixmap to the desired size of this widget.
            self.setPixmap(self._pixmap)

    #     try:
    #         # Defer to our superclass implementation.
    #         super().resizeEvent(*args, **kwargs)
    #
    # def resize(self, *args, **kwargs) -> None:
    #
    #     # Defer to our superclass implementation.
    #     super().resize(*args, **kwargs)

        # # If...
        # if (
        #     # This label has a pixmap.
        #     self._pixmap is not None and
        #     # This pixmap is *NOT* the null pixmap.
        #     not self._pixmap.isNull() and
        #     # This branch has *NOT* already been entered for this resize event,
        #     # preventing infinite recursion. See the class docstring.
        #     not self._is_in_resizeEvent
        #     # self._is_in_resizeEvent <= 1
        # ):
        #     # Attempt to...
        #     try:
        #         logs.log_debug('Rescaling pixmap after resizing label...')
        #
        #         # Prevent this branch from being erroneously reentered if the
        #         # call to setPixmap() induces a recursive call to this handler.
        #         self._is_in_resizeEvent = True
        #         # self._is_in_resizeEvent += 1
        #
        #         # Rescale this pixmap to the desired size of this widget.
        #         self.setPixmap(self._pixmap)
        #     # Regardless of whether doing so raises an exception, permit this
        #     # branch to be entered on the next handling of this resize event.
        #     finally:
        #         self._is_in_resizeEvent = False
        #         # self._is_in_resizeEvent -= 1

        # try:
        #     # Defer to our superclass implementation.
        #     super().resize(*args, **kwargs)
        #
        #     # If...
        #     if (
        #         # This label has a pixmap.
        #         self._pixmap is not None and
        #         # This pixmap is *NOT* the null pixmap.
        #         not self._pixmap.isNull() and
        #         # This branch has *NOT* already been entered for this resize event,
        #         # preventing infinite recursion. See the class docstring.
        #         not self._is_in_resizeEvent
        #         # self._is_in_resizeEvent <= 1
        #     ):
        #         # Log possible recursion.
        #         logs.log_debug('Rescaling pixmap after resizing label...')
        #
        #         # Rescale this pixmap to the desired size of this widget.
        #         self.setPixmap(self._pixmap)
        # # Regardless of whether doing so raises an exception, permit this
        # # branch to be entered on the next handling of this resize event.
        # finally:
        #     # Log possible recursion.
        #     logs.log_debug('Reenabling label pixmap rescaling...')
        #     self._is_in_resizeEvent = False

            # # Attempt to...
            # try:
            #     logs.log_debug('Rescaling pixmap after resizing label...')
            #
            #     # Prevent this branch from being erroneously reentered if the
            #     # call to setPixmap() induces a recursive call to this handler.
            #     self._is_in_resizeEvent = True
            #     # self._is_in_resizeEvent += 1
            #
            #     # Rescale this pixmap to the desired size of this widget.
            #     self.setPixmap(self._pixmap)
            # # Regardless of whether doing so raises an exception, permit this
            # # branch to be entered on the next handling of this resize event.
            # finally:
            #     self._is_in_resizeEvent = False
            #     # self._is_in_resizeEvent -= 1

    # ..................{ RESCALERS                          }..................
    # #FIXME: Document us up.
    # @type_check
    # def _rescale_pixmap(self, pixmap: QPixmap) -> QPixmap:
    #
    #     # Pixmap rescaled to the desired width and height of this
    #     pixmap_rescaled = pixmap.scaled(
    #         self.size(),  # * pixmap.devicePixelRatioF(),
    #         Qt.KeepAspectRatio,
    #         Qt.SmoothTransformation
    #     )
    #     # scaled.setDevicePixelRatio(devicePixelRatioF())
    #
    #     # Return this rescaled pixmap.
    #     return pixmap_rescaled
