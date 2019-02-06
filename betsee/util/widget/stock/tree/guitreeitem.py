#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level :class:`QTreeWidgetItem` functionality.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication
from PySide2.QtWidgets import QTreeWidgetItem
from betse.util.io.log import logs
from betse.util.py.module import pymodname
from betse.util.type.types import type_check, GeneratorType
from betsee.guiexception import BetseePySideTreeWidgetItemException

# ....................{ EXCEPTIONS                        }....................
@type_check
def die_unless_parent_item(item: QTreeWidgetItem) -> bool:
    '''
    Raise an exception unless the passed tree item is a **parent tree item**
    (i.e., contains at least one child tree item).

    Equivalently, this function raises an exception if this tree item contains
    no child tree items.

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be tested.

    Returns
    ----------
    bool
        ``True`` only if this tree item contains at least one child tree item.
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

# ....................{ GETTERS                           }....................
@type_check
def get_parent_item(item: QTreeWidgetItem) -> QTreeWidgetItem:
    '''
    Parent tree item of the passed child tree item if the latter has a parent
    (i.e., is *not* a top-level tree item) *or* the **root tree item** (i.e.,
    parent tree item of all top-level tree items) otherwise.

    Caveats
    ----------
    **This higher-level function should always be called in lieu of the
    low-level :meth:`QTreeWidgetItem.parent` method.** Whereas this function is
    *always* returns the parent tree item of any child tree item, that method
    only returns the parent tree item of non-top-level tree items; when passed
    a top-level tree item, that method uselessly returns ``None``.

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
        If this child tree item is the root tree item and hence has no parent.

    See Also
    ----------
    https://stackoverflow.com/a/12134662/2809027
        StackOverflow answer strongly inspiring this implementation.
    '''

    # Root tree item of the tree widget containing this child tree item.
    root_item = item.treeWidget().invisibleRootItem()

    # If this child tree item is this root tree item and hence has no parent,
    # raise an exception.
    if item is root_item:
        raise BetseePySideTreeWidgetItemException(QCoreApplication.translate(
            'guitreeitem',
            'Tree item parent not found '
            '(i.e., due to being the root tree item).'))

    # Parent tree item of this child tree item if this child is not already a
    # top-level tree item *OR* the root tree item otherwise.
    parent_item = item.parent() or root_item

    # Return this item.
    return parent_item


@type_check
def get_child_item_first(
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

# ....................{ REMOVERS                          }....................
@type_check
def remove_item(item: QTreeWidgetItem) -> None:
    '''
    Remove the passed tree item from its parent tree item and hence the parent
    tree transitively containing those items.

    Caveats
    ----------
    **This item may contain to consume.**

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be removed from its parent tree item and tree widget.

    Raises
    ----------
    BetseePySideTreeWidgetItemException
        If this tree item is the root tree item and hence cannot be removed.

    See Also
    ----------
    https://stackoverflow.com/a/8961820/2809027
        StackOverflow answer strongly inspiring this implementation.
    '''

    # Parent item of the passed child item.
    parent_item = get_parent_item(item)

    # Remove this child from this parent.
    parent_item.removeChild(item)

    # If the current PySide2 installation provides the technically optional
    # "PySide2.shiboken2" submodule...
    if pymodname.is_module('PySide2.shiboken2'):
        # Import this submodule.
        from PySide2 import shiboken2

        # Free all resources consumed by the passed item.
        #
        # Yes, this recursively visits each transitive child of the passed item
        # and both removes that child from its parent *AND* frees all resources
        # consumed by that item. Why? Because the Python-level
        # shiboken2.delete() function wraps the C++-level "delete" operator.
        # Naturally, the "QTreeWidgetItem" class overrides the "delete"
        # operator to remove itself from its parent tree -- which, in C++, is
        # the established means of doing so. Ergo, this is the established
        # means of doing so in Python as well.
        shiboken2.delete(item)
    #FIXME: Non-ideal. This common edge case can be sanely handled by
    #recursively iterating through all children of the passed tree item in a
    #bottom-up fashion (i.e., starting with the leaf tree items of the subtree
    #rooted at the passed tree item) and removing each such child from its
    #parent tree item. Non-ideal, but certainly feasible.
    #
    #Why is this necessary? Because the QTreeWidgetItem.removeChild() method
    #called above *ONLY* superficially removes that child from its parent, but
    #does *NOT* recursively remove any children of that child. Since each child
    #item internally retains a reference to its parent, failing to recursively
    #remove all children of that child guarantees that Python's garbage
    #collector will fail to free any resources consumed by that child. Woops.

    # Else, resources consumed by the passed item cannot be freed. In this
    # case, log a non-fatal warning.
    else:
        logs.log_warning(
            'Tree item "{}" not deletable '
            '(i.e., as PySide2 submodule "shiboken2" not found.'.format(
                item.text(0)))

# ....................{ ITERATORS                         }....................
@type_check
def iter_child_items(parent_item: QTreeWidgetItem) -> GeneratorType:
    '''
    Generator iteratively yielding each child tree item of the passed parent
    tree item.

    Yields
    ----------
    QTreeWidgetItem
        Current top-level tree item of this tree widget.

    Remove the passed tree item from its parent tree item and hence the parent
    tree transitively containing those items.

    Caveats
    ----------
    **This item may contain to consume.**

    Parameters
    ----------
    item : QTreeWidgetItem
        Tree item to be removed from its parent tree item and tree widget.
    '''

    # Number of child tree items of this parent tree item.
    child_items_count = parent_item.childCount()

    # Return a generator comprehension yielding...
    return (
        # Child tree item with the current 0-based index...
        parent_item.child(child_item_index)
        # For the 0-based index of each child tree item of this parent.
        for child_item_index in range(child_items_count)
    )
