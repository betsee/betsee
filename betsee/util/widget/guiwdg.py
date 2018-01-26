#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`PySide2`-specific widget facilities universally applicable to
all (or at least most) widget types.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid circular import dependencies, avoid importing from *ANY*
# application-specific submodules of this subpackage (i.e.,
# "betsee.util.widget"). Since those submodules must *ALWAYS* be able to safely
# import from this submodule, circularities are best avoided here.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtWidgets import QWidget
# from betse.util.io.log import logs
from betse.util.type.types import type_check, CallableTypes
from betsee.guiexception import BetseePySideWidgetException
from betsee.util.type.guitype import QWidgetOrNoneTypes

# ....................{ EXCEPTIONS                         }....................
@type_check
def die_unless_widget_parent_satisfies(
    widget: QWidget, predicate: CallableTypes) -> None:
    '''
    Raise an exception unless some transitive parent widget of the passed widget
    satisfies the passed predicate.

    Equivalently, this function raises an exception if *no* transitive parent
    widget of the passed widget satisfies the passed predicate.

    Parameters
    ----------
    widget : QWidgetOrNoneTypes
        Child widget to be inspected.
    predicate : CallableTypes
        Callable accepting one passed parent widget, returning ``True`` only if
        this widget satisfies this predicate. Hence, this predicate should have
        a signature resembling: ``def predicate(widget: QWidget) -> bool``.

    Raises
    ----------
    BetseePySideWidgetException
        If *no* transitive parent widget of this child widget satisfies this
        boolean predicate.
    '''

    if not is_widget_parent_satisfies(widget=widget, predicate=predicate):
        raise BetseePySideWidgetException(
            'Parent widget of child widget "{0}" '
            'satsifying predicate {1!r} not found.'.format(
                widget.objectName(), predicate))

# ....................{ TESTERS                            }....................
@type_check
def is_widget_parent_satisfies(
    widget: QWidget, predicate: CallableTypes) -> bool:
    '''
    ``True`` only if some transitive parent widget of the passed widget
    satisfies the passed predicate.

    For each transitive parent widget of the passed widget in ascending order
    from the immediate to root parent widget (e.g., :class:`QMainWindow` widget)
    of the passed widget, this function iteratively:

    #. Passes that parent widget to the passed predicate.
    #. If that predicate returns ``True``, this function halts searching and
       immediately returns ``True``.
    #. Else if that parent widget itself has a parent widget, this function
       continues searching by iterating up the widget ownership hierarchy to
       that parent parent widget and repeating the above logic.
    #. Else, returns ``False``.

    Parameters
    ----------
    widget : QWidgetOrNoneTypes
        Child widget to be inspected.
    predicate : CallableTypes
        Callable accepting one passed parent widget, returning ``True`` only if
        this widget satisfies this predicate. Hence, this predicate should have
        a signature resembling: ``def predicate(widget: QWidget) -> bool``.

    Returns
    ----------
    bool
        ``True`` only if some parent of this widget satisfies this predicate.
    '''

    # Currently visited child widget, starting at the passed child widget.
    widget_child = widget

    # Currently visited parent widget if this child widget has a parent widget
    # (i.e., is not the root widget) *OR* "None" otherwise.
    widget_parent = None

    # For here to eternity...
    while True:
        # Currently visited parent widget if any *OR* "None" otherwise.
        widget_parent = widget_child.parentWidget()

        # If this parent satisfies this predicate, halt searching with success.
        if predicate(widget_parent):
            return True

        # Else, this parent does *NOT* satisfy this predicate. In this case,
        # continue searching by iterating into the parent of this parent widget.
        widget_child = widget_parent

    # If no parents satisfy this predicate, halt searching with failure.
    return False

# ....................{ GETTERS                            }....................
@type_check
def get_label(widget: QWidgetOrNoneTypes) -> str:
    '''
    Human-readable label synopsizing the passed widget if any.

    Parameters
    ----------
    widget : QWidgetOrNoneTypes
        Widget to be synopsized *or* ``None``, in which case the absence of a
        widget is synopsized.

    Returns
    ----------
    str
        Human-readable label synopsizing this widget if any.
    '''

    return (
        'widget "{}"'.format(widget.objectName()) if widget is not None else
        'no widget')
