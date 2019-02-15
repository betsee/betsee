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
from betse.exceptions import BetseMethodUnimplementedException
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guicontrolabc import QBetseeControllerABC

# ....................{ SUPERCLASSES                      }....................
# This class is currently a trivial placeholder intended to eventually
# centralize common behaviour shared between all stacked widget pagers.
class QBetseeStackedWidgetPagerABC(QBetseeControllerABC):
    '''
    Abstract base class of all **stacked widget pager** (i.e., controller
    controlling the flow of application execution for a single page of a
    :mod:`QStackedWidget`) subclasses.
    '''

    pass

# ....................{ MIXINS                            }....................
# To avoid metaclass conflicts with the "QObject" base class inherited by all
# objects also inheriting this base class, this base class *CANNOT* be
# associated with another metaclass (e.g., "abc.ABCMeta").
class QBetseeStackedWidgetPagerItemizedMixin(object):
    '''
    Mixin of all **dynamic list item stacked widget pager** (i.e., controller
    controlling the flow of application execution for a single page of a
    :mod:`QStackedWidget` associated with zero or more tree items of a
    :mod:`QTreeWidget`, each of which masquerades as a list item dynamically
    defined at runtime) subclasses.

    This class is suitable for use as a multiple-inheritance mixin. To preserve
    the expected method resolution order (MRO) semantics, this class should
    typically be inherited *first* rather than *last* in subclasses.
    '''

    # ..................{ SUBCLASS                          }..................
    # Abstract methods required to be implemented by subclasses. Ideally, these
    # methods would be decorated by the standard @abstractmethod decorator.
    # Since doing so conflicts with metaclass semantics, these methods are
    # instead defined as concrete methods raising exceptions here.

    @type_check
    def reinit(self, list_item_index: int) -> None:
        '''
        Reassociate this pager with the **dynamic list item** (i.e., tree item
        of a :mod:`QTreeWidget` masquerading as a list item dynamically defined
        at runtime) with the passed index.

        This method is typically called by the parent object owning this pager
        (e.g., :mod:`QStackedWidget`) from a slot signalled immediately
        *before* the page controlled by this pager is switched to, ensuring
        that page to be prepopulated *before* being displayed.

        Design
        ----------
        Subclasses are required to redefine this pseudo-abstract method
        *without* calling this superclass implementation, which unconditionally
        raises an exception to enforce such redefinition.

        Subclasses typically implement this method by synchronizing all
        editable widgets on the stacked widget page controlled by this pager
        with their current values in the underlying data model (e.g., the
        currently open simulation configuration).

        Parameters
        ----------
        list_item_index: int
            0-based index of the list item to reassociate this pager with.
        '''

        raise BetseMethodUnimplementedException()


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
