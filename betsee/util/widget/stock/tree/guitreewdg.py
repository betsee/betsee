#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :class:`QTreeWidget` subclasses.
'''

#FIXME: Show connective branch lines (i.e., icons resembling the traditional
#Unicode box-drawing characters "├" and "│") to the left of each tree row. Note
#that most Qt styles *EXCEPT* the default Fusion default already define a
#qss-formatted stylesheet showing these lines by default. Since Fusion does
#not, however, we'll be required to do so manually. Note, however, that there
#appear to exist no well-defined solutions for doing so. The closest
#approximation that we could uncover is this Qt forum thread:
#    https://forum.qt.io/topic/77061/qtreewidget-with-connecting-lines-for-the-tree-branches/3
#...which leads directly to:
#    https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qtreeview
#
#There are numerous outstanding issues with the example provided by the latter
#link, including:
#
#* Usage of rasterized PNG icons rather than vectorized SVG icons, thus
#  ensuring pixellation on high-resolution displays.
#* Failure to properly style the background colours of the pseudo-states of
#  the "QTreeView::branch" state, requiring that we do so.
#
#Certainly, these issues can be resolved. Is doing so worthwhile, however? One
#reasonable alternative would be to entirely replace our current usage of
#Fusion with an existing third-party stylesheet -- which would then implicitly
#resolve this entire discussion. For further details, see "FIXME:" commentary
#in the "betse.gui.guimain" submodule.

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication  # Signal, Slot
from PySide2.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.type.text.string import strjoin
from betse.util.type.types import type_check, GeneratorType
from betsee.guiexception import BetseePySideTreeWidgetException
from betsee.util.widget.mixin.guiwdgmixin import QBetseeObjectMixin

# ....................{ SUBCLASSES                        }....................
class QBetseeTreeWidget(QBetseeObjectMixin, QTreeWidget):
    '''
    :mod:`QTreeWidget`-based widget marginally improving upon the stock
    :mod:`QTreeWidget` functionality.

    This application-specific widget augments the :class:`QTreeWidget` class
    with additional support for:

    * **Animations,** all of which are sufficiently aesthetic *and* minimally
      intrusive to warrant unconditionally enabling. Presumably for backward
      compatibility, these animations are disabled by the :class:`QTreeView`
      superclass by default. These include animations of:

      * The expansion and collapsing of tree branches.

    * **Horizontal scrollbars,** automatically displaying horizontal scrollbars
      for all columns whose content exceeds that column's width. For
      inexplicable reasons, this functionality has been seemingly intentionally
      omitted from the stock :class:`QTreeWidget`.
    * **Tree item introspection,** including:

      * Retrieval of the currently selected tree item if any in a safe manner.
      * Retrieval of arbitrary tree items from absolute text paths.
      * Iteration over all top-level tree items.

    Note that the default value of the :meth:`selectionMode` property is
    :attr:`QAbstractItemView.SingleSelection`, implying that only one tree item
    may be concurrently selected by default.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Enable all tree animations by default.
        self.setAnimated(True)

        # Header view for this tree.
        header_view = self.header()

        # To display a horizontal scrollbar instead of an ellipse when resizing
        # a column smaller than its content, resize that column's section to
        # its optimal size. For further details, see the following FAQ entry:
        #     https://wiki.qt.io/Technical_FAQ#How_can_I_ensure_that_a_horizontal_scrollbar_and_not_an_ellipse_shows_up_when_resizing_a_column_smaller_than_its_content_in_a_QTreeView_.3F
        header_view.setSectionResizeMode(QHeaderView.ResizeToContents)

        #FIXME: Consider excising this. The following call once behaved as
        #expected under obsolete PySide2 releases but now appears to
        #prematurely truncate this column. Oddly, the default behaviour now
        #behaves as expected. Such is our forlorn life in the code trenches.

        # By default, all trees contain only one column. Under the safe
        # assumption this tree will continue to contain only one column,
        # prevent this column's content from automatically resizing to the
        # width of the viewport rather than this column's section (as requested
        # by the prior call). This unfortunate default overrides that request.
        # header_view.setStretchLastSection(False)

    # ..................{ SUPERCLASS ~ setters              }..................
    #FIXME: Consider excising. See commentary preceding the
    #"header_view.setStretchLastSection(False)" line, above.

    # def setColumnCount(self, column_count: int) -> None:
    #
    #     # Defer to the superclass implementation.
    #     super().setColumnCount(column_count)
    #
    #     # If this tree now contains more than one column, permit the last such
    #     # column's content to automatically resize to the viewport width.
    #     if column_count != 1:
    #         self.header().setStretchLastSection(True)

    # ..................{ GETTERS                           }..................
    def get_item_current(self) -> QTreeWidgetItem:
        '''
        **Currently selected tree item** (i.e., tree item that currently has
        the keyboard focus) if any *or* raise an exception otherwise (i.e., if
        no tree item currently has the keyboard focus).

        Caveats
        ----------
        **This method ignores other tree items that have been selected but do
        not currently have the keyboard focus.** If the current selection mode
        for this tree widget is single (i.e., the value of the
        :meth:`selectionMode` property is
        :attr:`QAbstractItemView.SingleSelection`), this distinction is
        meaningless, as the currently selected tree item is guaranteed to have
        the keyboard focus. In all other cases, the more general-purpose
        :meth:`selectedItems` property should typically be called instead.

        Returns
        ----------
        QTreeWidgetItem
            Currently selected tree item.

        Raises
        ----------
        BetseePySideTreeWidgetException
            If no tree item currently has the keyboard focus.
        '''

        # Tree item that currently has the keyboard focus.
        item_current = self.currentItem()

        # If no such item exists, raise an exception.
        if item_current is None:
            raise BetseePySideTreeWidgetException(QCoreApplication.translate(
                'QBetseeTreeWidget', 'No tree item selected.'))

        # Return this item.
        return item_current


    @type_check
    def get_item_with_text_path(self, *text_path: str) -> QTreeWidgetItem:
        '''
        First tree item with the passed **absolute first-column text path**
        (i.e., sequence of one or more strings uniquely identifying this tree
        item in this tree) if any *or* raise an exception otherwise (i.e., if
        this tree contains no such item).

        Parameters
        ----------
        text_path: Tuple[str]
            Tuple of one or more first-column texts uniquely identifying the
            tree item of this tree to be returned.

        Returns
        ----------
        QTreeWidgetItem
            First tree item satisfying this absolute first-column text path.

        See Also
        ----------
        :func:`guitreeitem.get_child_item_with_text_path`
            Further details.
        '''

        # Avoid circular import dependencies.
        from betsee.util.widget.stock.tree import guitreeitem

        # Return the child tree item of the root tree item with this path.
        return guitreeitem.get_child_item_with_text_path(
            parent_item=self.invisibleRootItem(), text_path=text_path)

    # ..................{ ITERATORS                         }..................
    def iter_items_top(self) -> GeneratorType:
        '''
        Generator iteratively yielding each **top-level tree item** (i.e.,
        :class:`QTreeWidgetItem` owned by this tree such that the parent item
        of this child item is the invisible root item returned by the
        :meth:`invisibleRootItem` method) of this tree widget.

        Yields
        ----------
        QTreeWidgetItem
            Current top-level tree item of this tree widget.

        See Also
        ----------
        https://stackoverflow.com/a/8961820/2809027
            StackOverflow answer strongly inspiring this implementation.
        '''

        # Avoid circular import dependencies.
        from betsee.util.widget.stock.tree import guitreeitem

        # Root tree item of this tree widget.
        root_item = self.invisibleRootItem()

        # Return a generator comprehension yielding each top-level tree item
        # (i.e., child tree item of this root tree item).
        yield from guitreeitem.iter_child_items(root_item)
