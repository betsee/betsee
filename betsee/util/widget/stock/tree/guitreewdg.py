#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :class:`QTreeWidget` subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication  # Signal, Slot
from PySide2.QtWidgets import QHeaderView, QTreeWidget, QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.type.text.string import strjoin
from betse.util.type.types import type_check, GeneratorType
from betsee.guiexception import BetseePySideTreeWidgetException
from betsee.util.widget.abc.guiwdgabc import QBetseeObjectMixin

# ....................{ SUBCLASSES                        }....................
class QBetseeTreeWidget(QBetseeObjectMixin, QTreeWidget):
    '''
    :mod:`QTreeWidget`-based widget marginally improving upon the stock
    :mod:`QTreeWidget` functionality.

    This application-specific widget augments the :class:`QTreeWidget` class
    with additional support for:

    * **Horizontal scrollbars,** automatically displaying horizontal scrollbars
      for all columns whose content exceeds that column's width. For
      inexplicable reasons, this functionality has been seemingly intentionally
      omitted from the stock :class:`QTreeWidget`.
    * **Tree item introspection,** including:

      * Retrieval of arbitrary tree items from absolute text paths.
      * Iteration over all top-level tree items.
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

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
    @type_check
    def get_item_from_text_path(self, *text_path: str) -> QTreeWidgetItem:
        '''
        First tree item with the passed **absolute first-column text path**
        (i.e., sequence of one or more strings uniquely identifying this tree
        item in this tree) if any *or* raise an exception otherwise (i.e., if
        this tree contains no such item).

        Each passed string is the **first-column text** (i.e., text in the
        first column) of either the tree item to be returned *or* a parent tree
        item of that item, such that:

        #. The first passed string is the first-column text of the top-level
           #tree item containing the tree item to be returned.
        #. The second passed string is the first-column text of the child tree
           item of the prior top-level tree item containing the tree item to be
           returned.
        #. The second-to-last passed string is the first-column text of the
           parent tree item of the tree item to be returned.
        #. The last passed string is the first-column text of the tree item to
           be returned.

        Caveats
        ----------
        **This function only returns the first such item satisfying this
        path.** If this tree contains multiple items satisfying the same path,
        this method silently ignores all but the first such item.

        **This function performs a linear search through the items of this
        tree** and hence exhibits ``O(n)`` worst-case time complexity, where
        ``n`` is the number of items in this tree. While negligible in the
        common case, this search may be a performance concern on large trees.

        Parameters
        ----------
        text_path: Tuple[str]
            Tuple of one or more first-column texts uniquely identifying the
            tree item of this tree to be returned.

        Returns
        ----------
        QTreeWidgetItem
            First tree item satisfying this absolute first-column text path.

        Raises
        ----------
        BetseePySideTreeWidgetException
            If the passed ``text_path`` contains no strings.
        BetseePySideTreeWidgetItemException
            If this tree contains no tree item satisfying this path.
        '''

        # Avoid circular import dependencies.
        from betsee.util.widget.stock.tree import guitreeitem

        # Log this query.
        logs.log_debug(
            'Retrieving tree "%s" item with path "%s"...',
            self.obj_name, strjoin.join_on(*text_path, delimiter='/'))

        # If this text path is empty, raise an exception.
        if not text_path:
            raise BetseePySideTreeWidgetException(QCoreApplication.translate(
                'QBetseeTreeWidget', 'Tree path empty.'))

        # Current parent tree item of the next child tree item to be
        # iteratively visited starting with the root tree item.
        parent_item = self.invisibleRootItem()

        # For each passed first-column text...
        for child_item_text in text_path:
            # Find the child with this text of the current parent tree item,
            # replacing the latter with the former.
            parent_item = guitreeitem.get_child_item_first(
                parent_item=parent_item, child_text=child_item_text)

        # Return the last parent tree item visited by the above iteration.
        return parent_item

    # ..................{ ITERATORS                         }..................
    def iter_top_items(self) -> GeneratorType:
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
