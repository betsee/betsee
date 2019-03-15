#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **stacked widget pager** (i.e., controller controlling the flow of
application execution for a single page of a :mod:`QStackedWidget`) hierarchy.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QObject
from PySide2.QtWidgets import QMainWindow
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlabc import QBetseeControllerABC

# ....................{ MIXINS                            }....................
# To avoid metaclass conflicts with the "QObject" base class inherited by all
# objects also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseePagerItemizedMixin(object):
    '''
    Mixin of all **itemized stacked widget pager** (i.e., controller
    controlling the flow of application execution for a single page of a
    stacked widget associated with zero or more tree items of a tree widget
    masquerading as list items dynamically defined at runtime) subclasses.

    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be inherited *first* rather than *last* in subclasses.

    See Also
    ----------
    :class:`QBetseePagerItemizedABC`
        Abstract base class conveniently mixing this mixin with the lower-level
        abstract base :class:`QBetseePagerABC` class. Where
        feasible, subclasses should typically inherit from this higher-level
        superclass rather than this lower-level mixin.
    '''

    # ..................{ SUBCLASS                          }..................
    # Abstract methods required to be implemented by subclasses. Ideally, these
    # methods would be decorated by the standard @abstractmethod decorator.
    # Since doing so conflicts with metaclass semantics, these methods are
    # instead defined as concrete methods raising exceptions here.

    @type_check
    def reinit(self, main_window: QMainWindow, list_item_index: int) -> None:
        '''
        Reassociate this pager with the **dynamic list item** (i.e., tree item
        of a :mod:`QTreeWidget` masquerading as a list item dynamically defined
        at runtime) with the passed index against the passed parent main
        window.

        This method is typically called by the parent object owning this pager
        (e.g., :mod:`QStackedWidget`) from a slot signalled immediately
        *before* the page controlled by this pager is switched to, ensuring
        that page to be prepopulated *before* being displayed.

        To avoid circular references, this method is guaranteed to *not* retain
        a reference to this main window on returning. References to child
        widgets (e.g., simulation configuration stack widget) of this window
        may be retained, however.

        Design
        ----------
        Subclasses are required to redefine this quasi-abstract method
        *without* calling this superclass implementation, which unconditionally
        raises an exception to enforce such redefinition.

        Subclasses typically implement this method by synchronizing all
        editable widgets on the stacked widget page controlled by this pager
        with their current values in the underlying data model (e.g., the
        currently open simulation configuration).

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this controller.
        list_item_index: int
            0-based index of the list item to reassociate this pager with.
        '''

        raise BetseMethodUnimplementedException()


    #FIXME: Consider excising this method -- which we initially assumed to be
    #required but which we currently call nowhere, suggesting this assumption
    #to have been just that.
    #FIXME: In the unlikely edge case that we do actually require this method,
    #we clearly do so only for a proper subset of subclasses. In other words,
    #this method appears to be strictly optional. Given that:
    #
    #* Revise the default implementation to simply log this deinitialization
    #  rather than raising a fatal exception.
    #* Actually call this method elsewhere (e.g., in the "guisimconfstack"
    #  submodule) under at least the following circumstances:
    #  * When the low-level YAML-backed list item currently associated with
    #    this stack page is removed. Note that this should cleanly generalize
    #    to handle both the explicit removal of a single such item by the end
    #    user *AND* the closure of the current simulation configuration file.
    #    Ergo, we should *NOT* to manually handle such closure; detecting the
    #    condition when the item currently associated with this stack page is
    #    removed should thus gracefully scale to all possible cases. When this
    #    condition occurs *AND* this stack page is currently displayed, the
    #    parent page (which is guaranteed to exist) should be automatically
    #    switched to.
    def deinit(self) -> None:
        '''
        Deassociate this pager from the **dynamic list item** (i.e., tree item
        of a :mod:`QTreeWidget` masquerading as a list item dynamically defined
        at runtime) previously associated with this pager by the most recent
        call to the :meth:`reinit` method.

        This method is typically called by the parent object owning this pager
        (e.g., :mod:`QStackedWidget`) from a slot signalled immediately
        *after* the dynamic list item previously associated with this pager is
        removed, ensuring the page controlled by this pager to be depopulated
        *before* being subsequently displayed.

        Design
        ----------
        Subclasses are required to redefine this pseudo-abstract method
        *without* calling this superclass implementation, which unconditionally
        raises an exception to enforce such redefinition.

        Subclasses typically implement this method by desynchronizing all
        editable widgets on the stacked widget page controlled by this pager
        from any previous values in the underlying data model (e.g., the
        currently open simulation configuration).
        '''

        raise BetseMethodUnimplementedException()

# ....................{ SUPERCLASSES                      }....................
# This class is currently a trivial placeholder intended to eventually
# centralize common behaviour shared between all stacked widget pagers.
class QBetseePagerABC(QBetseeControllerABC):
    '''
    Abstract base class of all **stacked widget pager** (i.e., controller
    controlling the flow of application execution for a single page of a
    :mod:`QStackedWidget`) subclasses.
    '''

    pass


class QBetseePagerItemizedABC(QBetseePagerItemizedMixin, QBetseePagerABC):
    '''
    Abstract base class of all **itemized stacked widget pager** (i.e.,
    controller controlling the flow of application execution for a single page
    of a stacked widget associated with zero or more tree items of a tree
    widget masquerading as list items dynamically defined at runtime)
    subclasses.
    '''

    pass
