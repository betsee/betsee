#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :class:`QTreeWidget` subclasses.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QHeaderView, QTreeWidget
from betse.util.type.types import GeneratorType  # type_check,
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
