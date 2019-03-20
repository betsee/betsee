#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
General-purpose :mod:`QComboBox` widget subclasses.
'''

# ....................{ IMPORTS                           }....................
from PySide2.QtCore import QCoreApplication  #, Signal, Slot
from PySide2.QtWidgets import QComboBox
# from betse.util.io.log import logs
from betse.util.type.iterable import itertest
from betse.util.type.types import type_check, SequenceTypes
# from betsee.guiexception import BetseePySideComboBoxException

# ....................{ SUBCLASSES                        }....................
#FIXME: Generalize as follows:
#
#* Define a new "class QBetseeComboBox(QComboBox)" subclass in that submodule.
#  In this class:
#  * Copy the __init__() method defined below.
#  * Define a new add_items_iconless() method resembling:
    # def add_items_iconless(items_text: SequenceTypes) -> None:
    #     '''
    #     Add **icon-less items** (i.e., plaintext combo box items with *no*
    #     corresponding icons) with the passed text to this combo box after the
    #     index of this combo box defined by the :meth:`insertPolicy` property,
    #     defaulting to appending these items *after* any existing items of
    #     this combo box.
    #     '''
    #
    #     #FIXME: Explicitly detect the following types of duplicates:
    #     #
    #     #* Duplicate strings in the passed sequence.
    #     #* Strings in the passed sequence that are already existing items of
    #     #  this combo box.
    #     #
    #     #Consider efficient solutions elegantly handling both cases. If any
    #     #duplicate is detected, raise an exception. Note that this *MUST* be
    #     #done explicitly. The "QComboBox" class itself is sadly of no use here.
    #     #Note the documentation of the seemingly relevant (but ultimately
    #     #irrelevant) "duplicatesEnabled" property:
    #     #
    #     #    Note that it is always possible to programmatically insert duplicate items into the combo box.
    #
    #     # Sequence of the human-readable text of all combo box items.
    #     #
    #     # Since a view of ordered dictionary values is a valid sequence, the
    #     # QComboBox.addItems() method passed this sequence below should
    #     # technically accept this view *WITHOUT* requiring explicit coercion
    #     # into a tuple. It does not, raising the following exception on
    #     # attempting to do so:
    #     #
    #     #    TypeError: 'PySide2.QtWidgets.QComboBox.addItems' called with wrong argument types:
    #     #      PySide2.QtWidgets.QComboBox.addItems(ValuesView)
    #     #    Supported signatures:
    #     #      PySide2.QtWidgets.QComboBox.addItems(QStringList)
    #     #
    #     # Presumably, the underlying bindings generator (i.e., Shiboken2) only
    #     # implicitly coerces tuples and lists into "QStringList" instances.
    #     # Curiously, generic sequences appear to remain unsupported.
    #     if not isinstance(items_text, (tuple, list)):
    #         items_text = tuple(items_text)
    #
    #     # Populate the contents of this combo box from this sequence.
    #     self.addItems(items_text)
#  * Define a new init() method resembling:
#     def init(
#         self, items_iconless_text: SequenceOrNoneTypes, *args, **kwargs) -> None:
#
#         if items_iconless_text is not None:
#             self.add_items_iconless(items_iconless_text)
#* Define a new
#  "class QBetseeSimConfComboBoxABC(QBetseeComboBox)" superclass in this
#  submodule here, copying all of the "MIXIN" subsections below. This may or
#  may not be feasible due to diamond inheritance issues. If generalization
#  ultimately proves infeasible, simply copy-and-paste. *shrug*
#* Define a new
#  "class QBetseeSimConfComboBoxSequence(QBetseeSimConfComboBoxABC)" subclass
#  in this submodule here. The implementation of this subclass may reduce to
#  simply "pass". If that's the case, consider renaming the
#  "QBetseeSimConfComboBoxABC" superclass to "QBetseeSimConfComboBoxSequence"
#  and dispensing with this placeholder subclass entirely.
#* Rename the "QBetseeSimConfEnumComboBox" subclass defined below to
#  "QBetseeSimConfComboBoxEnum" for orthogonality.
#* Refactor this subclass to inherit "QBetseeSimConfComboBoxABC" if feasible.

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
        self.duplicatesEnabled(False)


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

        #FIXME: Explicitly detect the following types of duplicates by calling
        #the itertest.is_items_unique() function here:
        #
        #* Duplicate strings in the passed sequence.
        #* Strings in the passed sequence that are already existing items of
        #  this combo box.
        #
        #Consider efficient solutions elegantly handling both cases. If any
        #duplicate is detected, raise an exception. Note that this *MUST* be
        #done explicitly. The "QComboBox" class itself is sadly of no use here.
        #Note the documentation of the seemingly relevant (but ultimately
        #irrelevant) "duplicatesEnabled" property:
        #
        #    Note that it is always possible to programmatically insert duplicate items into the combobox.

        # Sequence of the human-readable text of all combo box items.
        #
        # Since a view of ordered dictionary values is a valid sequence, the
        # QComboBox.addItems() method passed this sequence below should
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
        if not isinstance(items_text, (tuple, list)):
            items_text = tuple(items_text)

        # Populate the contents of this combo box from this sequence.
        self.addItems(items_text)
