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

    # Iteratively delete each child of this parent.
    #
    # Note that calling the existing QTreeWidgetItem.takeChildren() method
    # would be considerably more efficient, but would also fail to ensure that
    # these items be scheduled for garbage collection. Which would be bad.
    for child_item in iter_child_items(parent_item):
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

    # Parent item of the passed child item.
    parent_item = get_parent_item(item)

    # Remove this child from this parent.
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
    tree item.

    Parameters
    ----------
    parent_item : QTreeWidgetItem
        Parent tree item to iterate all child tree items of.

    Yields
    ----------
    QTreeWidgetItem
        Current top-level tree item of this tree widget.
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
