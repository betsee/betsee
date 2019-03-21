#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QComboBox` widget subclasses.
'''

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication  #, Signal, Slot
from PySide2.QtWidgets import QComboBox
# from betse.util.io.log import logs
from betse.util.type.iterable import iterables, itertest
from betse.util.type.types import (
    type_check,
    GeneratorType,
    SequenceTypes,
    SequenceOrNoneTypes,
    SequenceStandardTypes,
)
# from betsee.guiexception import BetseePySideComboBoxException

# ....................{ SUBCLASSES                        }....................
class QBetseeComboBox(QComboBox):
    '''
    General-purpose :mod:`QComboBox`-based widget implementing a mildly more
    Pythonic API.

    Caveats
    ----------
    To guarantee a one-to-one correspondence between the currently selected
    combo box item and the underlying model constraining these items, this
    combo box defaults to:

    * **Non-editability** (i.e., the text of each item is *not* interactively
      editable by end users).
    * **Uniqueness** (i.e., the text of each item is unique and hence differs
      from the text of each other item).
    '''

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Disable editability, preventing users from manually editing item
        # text. While our superclass already disables editability by default,
        # this is sufficiently vital to warrant doing so explicitly.
        self.setEditable(False)

        # Disable duplicability, preventing users from manually duplicating
        # text across multiple items. Since editability is already disabled by
        # default, this admittedly produces no effect. *shrug*
        self.setDuplicatesEnabled(False)


    @type_check
    def init(
        self,
        items_iconless_text: SequenceOrNoneTypes = None,
        *args, **kwargs
    ) -> None:
        '''
        Finalize the initialization of this widget.

        Parameters
        ----------
        items_iconless_text : SequenceOrNoneTypes
            Sequence of **icon-less item text** (i.e., human-readable text of
            combo box items with *no* corresponding icons) to prepopulate this
            combo box with. Defaults to ``None``, in which case this combo box
            initially contains no items and is thus empty.

        All remaining parameters are passed as is to the superclass method.
        '''

        # Finalize the initialization of our superclass.
        super().init(*args, **kwargs)

        # If prepopulating this combo box with icon-less items, do so.
        if items_iconless_text is not None:
            self.add_items_iconless(items_iconless_text)

    # ..................{ ADDERS                            }..................
    @type_check
    def add_items_iconless(self, items_text: SequenceTypes) -> None:
        '''
        Add **icon-less items** (i.e., plaintext combo box items with *no*
        corresponding icons) with the passed text to this combo box after the
        index of this combo box defined by the :meth:`insertPolicy` property,
        defaulting to appending these items *after* any existing items of
        this combo box.

        Specifically, for each element of this sequence, this method adds a new
        combo box item whose human-readable text is that element.

        Parameters
        ----------
        items_text : SequenceTypes
            Sequence of the text of each item to be added to this combo box.
        '''

        # Iterable aggregating both the passed and existing iterables of combo
        # box item text, optimizing the subsequent validation of uniqueness.
        items_all_text = iterables.iter_items(
            items_text, self.iter_items_text())

        # If at least one combo box item text of the passed iterable duplicates
        # other combo box item text of either the passed or existing iterables
        # of such text, raise an exception.
        #
        # Note that this constraint *MUST* be validated explicitly, as the
        # stock "QComboBox" superclass provides no such validation. Notably,
        # official documentation for the seemingly relevant (but ultimately
        # irrelevant) "duplicatesEnabled" property reads:
        #
        #    Note that it is always possible to programmatically insert
        #    duplicate items into the combobox.
        itertest.die_unless_items_unique(items_all_text)

        # If the passed sequence is neither a standard "list" nor "tuple",
        # coerce this sequence into the latter. Why? Because inadequacies in
        # the Qt API inherited by PySide2.
        #
        # Consider a view of ordered dictionary values (i.e., instance of the
        # "collections.abc.ValuesView" interface instantiated and returned by
        # the OrderedDict.values() method). This view is a valid sequence. In
        # theory, the QComboBox.addItems() method passed this sequence should
        # technically accept this view *WITHOUT* requiring explicit coercion
        # into a tuple. It does not, raising the following exception on
        # attempting to do so:
        #
        #    TypeError: 'PySide2.QtWidgets.QComboBox.addItems' called with wrong argument types:
        #      PySide2.QtWidgets.QComboBox.addItems(ValuesView)
        #    Supported signatures:
        #      PySide2.QtWidgets.QComboBox.addItems(QStringList)
        #
        # Presumably, the underlying bindings generator (i.e., Shiboken2) only
        # implicitly coerces tuples and lists into "QStringList" instances.
        # Curiously, generic sequences appear to remain unsupported.
        if not isinstance(items_text, SequenceStandardTypes):
            items_text = tuple(items_text)

        # Add these icon-less items to this combo box.
        self.addItems(items_text)

    # ..................{ ITERATORS                         }..................
    @type_check
    def iter_items_text(self) -> GeneratorType:
        '''
        Generator iteratively yielding the human-readable text associated with
        each item of this combo box.

        Yields
        ----------
        str
            Human-readable text associated with the currently iterated item of
            this combo box.
        '''

        # Return a generator comprehension yielding...
        return (
            # The text associated with this item...
            self.itemText(item_index)
            # For the 0-based index of each item of this combo box.
            for item_index in range(self.count())
        )
