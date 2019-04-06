#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level :class:`QTreeWidgetItem` functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator
from betse.util.io.log import logs
from betse.util.py.module import pymodname
from betse.util.type.iterable import sequences
from betse.util.type.text.string import strjoin
from betse.util.type.types import type_check, GeneratorType, SequenceTypes
from betsee.guiexception import BetseePySideTreeWidgetItemException
from betsee.util.type.guitype import QTreeWidgetItemOrNoneTypes

# ....................{ EXCEPTIONS                        }....................
@type_check
def die_if_parent_item(item: QTreeWidgetItem) -> None:
    '''
    Raise an exception if the passed tree item is a **parent tree item** (i.e.,
    contains at least one child tree item).

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be tested.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this tree item contains one or more child tree items.
    '''

    # If this tree item is already a parent, raise an exception.
    if is_parent_item(item):
        raise BetseePySideTreeWidgetItemException(QCoreApplication.translate(
            'guitreeitem',
            'Tree item "{0}" already a parent '
            '(i.e., contains {1} child tree items).'.format(
                item.text(0), item.childCount())))


@type_check
def die_unless_parent_item(item: QTreeWidgetItem) -> None:
    '''
    Raise an exception unless the passed tree item is a **parent tree item**
    (i.e., contains at least one child tree item).

    Equivalently, this function raises an exception if this tree item contains
    no child tree items.

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be tested.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this tree item contains no child tree items.
    '''

    # If this tree item is *NOT* a parent, raise an exception.
    if not is_parent_item(item):
        raise BetseePySideTreeWidgetItemException(QCoreApplication.translate(
            'guitreeitem',
            'Tree item "{0}" not a parent '
            '(i.e., contains no child tree items).'.format(item.text(0))))

# ....................{ TESTERS                           }....................
@type_check
def is_parent_item(item: QTreeWidgetItem) -> bool:
    '''
    ``True`` only if the passed tree item is a **parent tree item** (i.e.,
    contains at least one child tree item).

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be tested.

    Returns
    ----------
    bool
        ``True`` only if this tree item contains at least one child tree item.
    '''

    # Well, that was surprisingly non-intuitive.
    return item.childCount() > 0

# ....................{ GETTERS ~ child : text            }....................
@type_check
def get_child_item_with_text_first(
    parent_item: QTreeWidgetItem, child_text: str) -> QTreeWidgetItem:
    '''
    First child tree item with the passed **first-column text** (i.e., text in
    the first column) residing under the passed parent tree item if this parent
    contains at least one such child *or* raise an exception otherwise (i.e.,
    if this parent contains no such child).

    Caveats
    ----------
    **This function only returns the first such child of this parent.** If this
    parent contains multiple children with the same first-column text, this
    function silently ignores all but the first such child.

    **This function performs a linear search through the children of this
    parent** and hence exhibits ``O(n)`` worst-case time complexity, where
    ``n`` is the number of children of this parent. While negligible in the
    common case, this search may be a performance concern on large subtrees.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Parent tree item to retrieve this child tree item from.
    child_text : str
        Text in the first column of the first child tree item to be retrieved
        from this parent tree item.

    Returns
    ----------
    QTreeWidgetItem
        First child tree item with this first-column text residing under this
        parent tree item.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this parent tree item contains no child tree item with this
        first-column text.
    '''

    # If this tree item contains no child tree items, raise an exception.
    die_unless_parent_item(parent_item)
    # Else, this is tree item contains one or more children.

    # For each child tree item of this parent tree item...
    for child_item in iter_child_items(parent_item):
        # If this child's first-column text is the passed string, this is the
        # first matching child. In this case, return this match.
        if child_item.text(0) == child_text:
            return child_item

    # Else, this parent tree item contains no matching child. In this case,
    # raise an exception.
    raise BetseePySideTreeWidgetItemException(QCoreApplication.translate(
        'guitreeitem',
        'Parent tree item "{0}" contains no '
        'child tree item with first-column text "{1}".'.format(
            parent_item.text(0), child_text)))


@type_check
def get_child_item_with_text_path(
    parent_item: QTreeWidgetItem, text_path: SequenceTypes) -> QTreeWidgetItem:
    '''
    First transitive child tree item of the passed parent tree item with the
    passed **absolute first-column text path** (i.e., sequence of one or more
    strings uniquely identifying this child tree item in the subtree rooted at
    this parent tree item) if any *or* raise an exception otherwise (i.e., if
    this parent tree item transitively contains no such child tree item).

    Each passed string is the **first-column text** (i.e., text in the first
    column) of either the child tree item to be returned *or* a parent tree
    item of that item, such that:

    #. The first passed string is the first-column text of the top-level
       child tree item of this parent tree item transitively containing the
       child tree item to be returned.
    #. The second passed string is the first-column text of the next-level
       child tree item of the prior top-level child tree item transitively
       containing the child tree item to be returned.
    #. The second-to-last passed string is the first-column text of the
       direct parent tree item of the child tree item to be returned.
    #. The last passed string is the first-column text of the child tree item
       to be returned.

    Caveats
    ----------
    **This function only returns the first such item satisfying this path.** If
    this parent contains multiple children ambiguously satisfying this path,
    this function silently ignores all but the first such child tree item.

    **This function performs a linear search through the items of the subtree
    rooted at this parent tree item** and hence exhibits ``O(n)`` worst-case
    time complexity, where ``n`` is the number of items in this subtree. While
    negligible in the common case, this search may be a performance concern on
    large subtrees.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Parent tree item to retrieve this child tree item from.
    text_path: SequenceTypes
        Sequence of one or more first-column texts uniquely identifying the
        child tree item of this parent tree item to be returned.

    Returns
    ----------
    QTreeWidgetItem
        First child tree item with this path.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If either:

        * The passed ``text_path`` parameter is empty.
        * This parent tree item contains no child tree item with this path.
    '''

    # If this tree item contains no child tree items, raise an exception.
    die_unless_parent_item(parent_item)
    # Else, this is tree item contains one or more children.

    # Log this query.
    logs.log_debug(
        'Retrieving parent tree item "%s" child with path "%s"...',
        #FIXME: We probably want a helper getter implementing this, which we
        #should then call everywhere we currently query "item.text(0)" for use
        #in log messages.
        parent_item.text(0) or 'ROOT',
        strjoin.join_on(*text_path, delimiter='/'))

    # If this text path is empty, raise an exception.
    sequences.die_if_empty(text_path, label='Tree path')

    # For each passed first-column text...
    for child_item_text in text_path:
        # Find the child with this text of the current parent tree item,
        # replacing the latter with the former.
        parent_item = get_child_item_with_text_first(
            parent_item, child_item_text)

    # Return the last parent tree item visited by the above iteration.
    return parent_item

# ....................{ GETTERS ~ parent                  }....................
@type_check
def get_parent_item(child_item: QTreeWidgetItem) -> QTreeWidgetItem:
    '''
    Parent tree item of the passed child tree item if this child has a parent
    *or* raise an exception otherwise (i.e., if this child has *no* parent).

    Caveats
    ----------
    **This higher-level function should always be called in lieu of the
    low-level :meth:`QTreeWidgetItem.parent` method.** Whereas this function
    unambiguously returns the expected tree item or raises an exception, that
    method ambiguously returns ``None`` for both top-level tree items whose
    parent is the root tree item of the tree containing those items *and* tree
    items with no parent.

    Parameters
    ----------
    child_item : QTreeWidgetItem
        Child tree item to retrieve this parent tree item of.

    Returns
    ----------
    QTreeWidgetItem
        Either:

        * If this child tree item is a top-level tree item, the root tree item
          of the :class:`QTreeWidget` containing this item.
        * Else, the parent tree item of this child tree item.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this child tree item has no parent.

    See Also
    ----------
    https://stackoverflow.com/a/12134662/2809027
        StackOverflow answer mildly inspiring this implementation.
    '''

    # Parent tree item of this child tree item if any *OR* "None" otherwise.
    parent_item = get_parent_item_or_none(child_item)

    # If this child tree item has no such parent, raise an exception.
    if parent_item is None:
        raise BetseePySideTreeWidgetItemException(QCoreApplication.translate(
            'guitreeitem',
            'Tree item "{0}" has no parent.'.format(child_item.text(0))))
    # Else, this child tree item has such a parent.

    # Return this parent.
    return parent_item


@type_check
def get_parent_item_or_none(
    child_item: QTreeWidgetItem) -> QTreeWidgetItemOrNoneTypes:
    '''
    Parent tree item of the passed child tree item if this child has a parent
    *or* ``None`` otherwise (i.e., if this child has *no* parent).

    Caveats
    ----------
    **This higher-level function should always be called in lieu of the
    low-level :meth:`QTreeWidgetItem.parent` method.** Whereas this function
    unambiguously returns either the expected tree item or ``None``, that
    method ambiguously returns ``None`` for both top-level tree items whose
    parent is the root tree item of the tree containing those items *and* tree
    items with no parent.

    Parameters
    ----------
    child_item : QTreeWidgetItem
        Child tree item to retrieve this parent tree item of.

    Returns
    ----------
    QTreeWidgetItemOrNoneTypes
        Either:

        * If this child tree item is a top-level tree item, the root tree item
          of the :class:`QTreeWidget` containing this item.
        * Else if this child tree item has a parent tree item, that item.
        * Else, ``None``.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this child tree item is the root tree item and hence has no parent.

    See Also
    ----------
    https://stackoverflow.com/a/12134662/2809027
        StackOverflow answer strongly inspiring this implementation.
    '''

    # Parent tree item of this child tree item if any *OR* "None" otherwise.
    parent_item = child_item.parent()

    # If this child has no explicit parent...
    if parent_item is None:
        # Tree widget containing this child tree item if this item belongs to
        # such a tree *OR* "None" otherwise.
        tree_widget = child_item.treeWidget()

        # If this item belongs to such a tree...
        if tree_widget is not None:
            # Root tree item of this tree, which is guaranteed to exist.
            #
            # Indeed, since this child tree item has no explicit parent but
            # belongs to a tree widget, this child tree item *MUST* necessarily
            # be a child of this root tree item and hence itself be a top-level
            # tree item of this tree widget.
            parent_item = tree_widget.invisibleRootItem()

            # Assert this to be the case for safety.
            assert parent_item.indexOfChild(child_item) != -1

    # Return this item if any *OR* "None" otherwise.
    return parent_item

# ....................{ GETTERS ~ preceding               }....................
@type_check
def get_item_preceding(item: QTreeWidgetItem) -> QTreeWidgetItemOrNoneTypes:
    '''
    Tree item preceding the passed tree item in the tree widget containing that
    tree item if the passed tree item is *not* the first top-level item of this
    tree widget *or* raise an exception otherwise (i.e., if this is the first
    top-level item of this tree widget).

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If the passed tree item is the first top-level item of its tree widget.

    See Also
    ----------
    :func:`get_item_preceding_or_none`
        Further details.
    '''

    # Tree item preceding this tree item if any *OR* "None" otherwise.
    item_preceding = get_item_preceding_or_none(item)

    # If no such item exists, raise an exception.
    if item_preceding is None:
        raise BetseePySideTreeWidgetItemException(QCoreApplication.translate(
            'guitreeitem',
            'Tree item "{0}" preceded by no tree item '
            '(i.e., due to being the first top-level tree item).'.format(
                item.text(0))))
    # Else, this item exists.

    # Return this item.
    return item_preceding


@type_check
def get_item_preceding_or_none(
    item: QTreeWidgetItem) -> QTreeWidgetItemOrNoneTypes:
    '''
    Tree item preceding the passed tree item in the tree widget containing that
    tree item if the passed tree item is *not* the first top-level item of this
    tree widget *or* ``None`` otherwise (i.e., if this is the first top-level
    item of this tree widget).

    Specifically, this function returns:

    * If the passed tree item has a **preceding sibling** (i.e., a child tree
      item with the same parent tree item as the passed tree item whose index
      in the parent is one less than that of the passed tree item), this
      sibling.
    * Else if the passed tree item has a **non-root parent** (i.e., a parent
      tree item that is *not* the invisible root tree item of this tree widget,
      in which case the passed tree item is *not* a top-level tree item), this
      parent.
    * Else, the passed tree item is the first top-level tree item of this tree
      widget, in which case an exception is raised.

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to retrieve the preceding tree item of.

    Returns
    ----------
    QTreeWidgetItem
        Tree item preceding the passed tree item.
    '''

    # Tree item iterator iterating from this tree item.
    item_iter = QTreeWidgetItemIterator(item, QTreeWidgetItemIterator.All)

    # Iterate this iterator to the tree item preceding this tree item if any
    # *OR* silently fail (without raising an exception) otherwise.
    #
    # Yes, this is balls crazy. Yes, this works as expected. Why? Because the
    # "QTreeWidgetItemIterator" API was designed from the arguably arcane C++
    # perspective. In C++, overloading mathematical operators to perform
    # non-mathematical iteration (commonly referred to as "pointer
    # arithmetic") is a standard idiom. In Python, the corresponding operation
    # is fundamentally non-Pythonic and hence divorced from anything resembling
    # sanity. For further details, see the PySide2-specific documentation at:
    #     https://doc.qt.io/qtforpython/PySide2/QtWidgets/QTreeWidgetItemIterator.html
    item_iter -= 1

    # Tree item preceding the passed tree item if any *OR* "None" otherwise.
    item_preceding = item_iter.value()

    # Return this object.
    return item_preceding

# ....................{ DELETERS                          }....................
@type_check
def delete_child_items(parent_item: QTreeWidgetItem) -> None:
    '''
    Permanently delete *all* child tree items of the passed parent tree item.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Parent tree item to delete all child tree items of.

    See Also
    ----------
    :func:`delete_item`
        Further details.
    '''

    # Log this recursion.
    logs.log_debug(
        'Recursively deleting tree item "%s" children...', parent_item.text(0))

    # Sequence of zero or more child tree items removed from this parent tree
    # item, each possibly themselves containing child tree items.
    child_items = parent_item.takeChildren()

    # Recursively delete the subtree rooted at each such child.
    for child_item in child_items:
        delete_item(child_item)

# ....................{ DELETERS ~ item                   }....................
@type_check
def delete_item(item: QTreeWidgetItem) -> None:
    '''
    Permanently delete the passed tree item.

    Specifically, this function (in order):

    #. Removes this item from its parent tree item and hence the
       :class:`QTreeWidget` containing both items.
    #. Schedules this item for garbage collection.

    Caveats
    ----------
    **This function should always be called in lieu of lower-level Qt methods
    (e.g., :meth:`QTreeWidgetItem.removeChild`,
    :meth:`QTreeWidgetItem.takeChild`, :meth:`QTreeWidgetItem.takeChildren`).**
    Why? Because those methods are *not* guaranteed to schedule this item for
    garbage collection. Hidden references to this item preventing Python from
    garbage collecting this item may continue to silently persist -- notably,
    circular references between this item and its child tree items (if any).

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be deleted.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this tree item is the root tree item and hence cannot be deleted.

    See Also
    ----------
    https://stackoverflow.com/a/8961820/2809027
        StackOverflow answer mildly inspiring this implementation.
    '''

    # Log this deletion.
    logs.log_debug('Deleting tree item "%s"...', item.text(0))

    # Parent item of the passed child item if any *OR* "None" otherwise.
    parent_item = get_parent_item_or_none(item)

    # If this child item has a parent item, remove this child from this parent.
    if parent_item is not None:
        parent_item.removeChild(item)

    # If the current PySide2 installation provides the technically optional
    # "PySide2.shiboken2" submodule...
    if pymodname.is_module('PySide2.shiboken2'):
        # Import this submodule.
        from PySide2 import shiboken2

        # Free all resources consumed by this item.
        #
        # Yes, this recursively visits each transitive child of this item and
        # both removes that child from its parent *AND* frees all resources
        # consumed by that item. Why? Because the Python-level
        # shiboken2.delete() function wraps the C++-level "delete" operator.
        # Naturally, the "QTreeWidgetItem" class overrides the "delete"
        # operator to remove itself from its parent tree -- which, in C++, is
        # the established means of doing so. Ergo, this is the established
        # means of doing so in Python as well.
        shiboken2.delete(item)
    # Else, the convenient deletion algorithm implemented by the
    # technically optional "PySide2.shiboken2" submodule must be manually
    # reimplemented here. (This is why we can't have good things.)
    #
    # If this item contains one or more children...
    elif is_parent_item(item):
        # Log a non-fatal warning of this inefficiency.
        logs.log_warning(
            'Suboptimally deleting subtree '
            '(i.e., as PySide2 submodule "shiboken2" not found)...')

        # Recursively delete the subtree rooted at the passed tree item.
        _delete_item_subtree(item)
    # Else, this item contains *NO* children. In this case, no warning or
    # iterations need be performed. This item is childless and hence
    # participates in no circular references, guaranteeing that this item will
    # be scheduled for garbage collection shortly.


@type_check
def _delete_item_subtree(parent_item: QTreeWidgetItem) -> None:
    '''
    Recursively delete the **subtree** (i.e., abstract collection of one or
    more tree items) rooted at the passed tree item.

    This recursive function manually reimplements the convenient deletion
    algorithm implemented by the technically optional :mod:`PySide2.shiboken2`
    submodule. Specifically, this function (in order):

    #. Removes all child tree items from this item.
    #. Recursively calls this function on each such item.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Tree item to recursively delete the entire subtree of.
    '''

    # Log this recursion.
    logs.log_debug(
        'Recursively deleting tree item "%s" subtree...', parent_item.text(0))

    # Sequence of zero or more child tree items removed from this parent tree
    # item, each possibly themselves containing child tree items.
    child_items = parent_item.takeChildren()

    # Recursively delete the subtree rooted at each such child.
    for child_item in child_items:
        _delete_item_subtree(child_item)

# ....................{ ITERATORS                         }....................
@type_check
def iter_child_items(parent_item: QTreeWidgetItem) -> GeneratorType:
    '''
    Generator iteratively yielding each child tree item of the passed parent
    tree item (in ascending order).

    Caveats
    ----------
    **Avoiding deleting items yielded by this generator,** as doing so is
    guaranteed to raise an exception. Consider calling the
    :func:`iter_child_items_reversed` function instead, which suffers no such
    synchronization issues.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Parent tree item to iterate all child tree items of.

    Yields
    ----------
    QTreeWidgetItem
        Current top-level tree item of this tree widget.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If the current child tree item to be yielded no longer exists (e.g.,
        due to having been erroneously deleted by the caller).
    '''

    # Number of child tree items of this parent tree item.
    child_items_count = parent_item.childCount()

    # For the 0-based index of each child tree item of this parent...
    for child_item_index in range(child_items_count):
        # Child tree item with the current 0-based index.
        child_item = parent_item.child(child_item_index)

        # If no such item exists, raise an exception.
        if child_item is None:
            raise BetseePySideTreeWidgetItemException(
                QCoreApplication.translate(
                    'guitreeitem',
                    'Parent tree item "{0}" child "{1}" '
                    'no longer exists.'.format(
                        parent_item.text(0), child_item_index)))
        # Else, this item exists.

        # Yield this item.
        yield child_item


@type_check
def iter_child_items_reversed(parent_item: QTreeWidgetItem) -> GeneratorType:
    '''
    Generator iteratively yielding each child tree item of the passed parent
    tree item (in descending and hence "reversed" order).

    This function explicitly permits callers to safely delete items yielded by
    this generator, unlike the :func:`iter_child_items` function. Indeed, item
    deletion is the principal use case for this function.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Parent tree item to iterate all child tree items of.

    Yields
    ----------
    QTreeWidgetItem
        Current top-level tree item of this tree widget.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If the current child tree item to be yielded no longer exists (e.g.,
        due to having been erroneously deleted by the caller). This edge case
        may occur when the caller attempts to delete any child tree item
        excluding the previously yielded tree item, which may *always* be
        safely deleted.
    '''

    # Number of child tree items of this parent tree item.
    child_items_count = parent_item.childCount()

    # For the 0-based index of each child tree item of this parent (in reversed
    # order)...
    #
    # Note that this duplication of the body of the iter_child_items()
    # generator could be avoided with the following one-liner, but that doing
    # so would substantially increase space complexity -- which is bad:
    #    return reversed(tuple(iter_child_items(parent_item)))
    for child_item_index in reversed(range(child_items_count)):
        # Child tree item with the current 0-based index.
        child_item = parent_item.child(child_item_index)

        # If no such item exists, raise an exception.
        if child_item is None:
            raise BetseePySideTreeWidgetItemException(
                QCoreApplication.translate(
                    'guitreeitem',
                    'Parent tree item "{0}" child "{1}" '
                    'no longer exists.'.format(
                        parent_item.text(0), child_item_index)))
        # Else, this item exists.

        # Yield this item.
        yield child_item
