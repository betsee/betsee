#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
**Export item simulation configuration pager** (i.e., :mod:`PySide2`-based
controller for stack widget pages applicable to exports of a certain type
associated with tree widget items masquerading as dynamic list items)
hierarchy.
'''

#FIXME: Substantially improve the display of the "_widget_kind" widget (i.e.,
#the widget enabling end users to configure the type of the currently selected
#export). Currently, this widget is constrained to be a combo box whose
#contents are non-human-readable export pipeline runner type names (e.g.,
#"pump_nakatpase"). Navigating this widget when a large number of such names
#exist is overly cumbersome. Ideally, we should peplace each such combo box for
#each such page with the following buddy (i.e., companion) widgets:
#
#* Either:
#  * A list, whose contents are the sorted human-readable names associated with
#    each such exporter rather than non-human-readable types of that exporter
#    (e.g., "Ion Pump: Pump Rate: Na-K-ATPase" rather than "pump_nakatpase").
#    Although overly simplistic, a list would certainly suffice.
#  * A tree, whose contents are the nested human-readable names associated with
#    each such exporter rather than non-human-readable types of that exporter
#    (e.g., "Ion Pump" -> "Pump Rate" -> "Na-K-ATPase" rather than
#    "pump_nakatpase"). Although overly complex, a tree would certainly provide
#    the most structured and hence user-usable interface for displaying this
#    metadata in a reasonable manner.
#* A label, whose contents are the human-readable description (presumably
#  culled from the method docstring) for the currently selected exporter. Some
#  care should be taken here to either:
#  * Strip ReST-specific syntax (e.g., "*" characters) entirely. *DO THIS.*
#  * Convert ReST-specific syntax to the corresponding HTML. Sadly, doing so
#    sanely is pragmatically infeasible, thanks to the lack of Python-builtin
#    parsing methodologies like parser expression grammars (PEGs). In short,
#    *ABSOLUTELY DO NOT DO THIS.* Well, not at first, anyway. We'll probably
#    want to do this eventually, but the up-front implementation cost is
#    absolutely *NOT* worth the dismal, meagre payoff.

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.pipe.export.pipeexpabc import SimPipeExportABC
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.iterable import sequences
from betse.util.type.obj import objects
from betse.util.type.types import type_check
from betsee.util.widget.abc.control.guictlpageabc import (
    QBetseePagerItemizedABC)

# ....................{ SUPERCLASSES                      }....................
class QBetseeSimConfPagerExportABC(QBetseePagerItemizedABC):
    '''
    Abstract base class of all **simulation export configuration pager** (i.e.,
    :mod:`PySide2`-based controller connecting all editable widgets of a
    stack widget page applicable to simulation exports of a particular type
    with corresponding settings of a YAML-backed list item of the currently
    open simulation configuration) subclasses.

    Attributes
    ----------
    _p : Parameters
        Simulation configuration singleton.

    Attributes (Widget)
    ----------
    _widget_kind : QBetseeSimConfComboBoxSequence
        Combo box widget editing the type of this simulation export, whose Qt
        object name is :meth:`_widget_name_prefix` appended by ``kind``.
    _widget_name : QBetseeSimConfLineEdit
        Line edit widget editing the name of this simulation export, whose Qt
        object name is :meth:`_widget_name_prefix` appended by ``name``.
    '''

    # ..................{ PROPERTIES ~ abstract             }..................
    # Subclasses are required to implement the following abstract properties.

    @abstractproperty
    def _pipe_cls(self) -> SimPipeExportABC:
        '''
        Type of simulation export pipeline exporting all possible simulation
        exports associated with this pager.
        '''

        pass


    @abstractproperty
    def _widget_name_prefix(self) -> str:
        '''
        Substring prefixing the name of all instance variables of the
        :class:`QBetseeMainWindow`` singleton whose values are all child
        widgets of the page controlled by this pager.
        '''

        pass


    @abstractproperty
    def _yaml_list(self) -> str:
        '''
        YAML-backed list subconfiguration (i.e., :class:`YamlList` instance) of
        the current simulation configuration whose currently selected item in
        the top-level tree widget is edited by the child widgets of the page
        controlled by this pager.

        Subclasses should note that the :attr:`_p` instance variable
        (guaranteed to be non-``None`` whenever this property is accessed)
        provides direct access to this list subconfiguration.
        '''

        pass

    # ..................{ INITIALIZERS                      }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this pager.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Nullify all remaining instance variables for safety.
        self._p = None
        self._widget_kind = None
        self._widget_name = None


    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Avoid circular import dependencies.
        from betsee.gui.simconf.stack.widget.guisimconfcombobox import (
            QBetseeSimConfComboBoxSequence)
        from betsee.gui.simconf.stack.widget.guisimconflineedit import (
            QBetseeSimConfLineEdit)

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Classify variables of this main window required by most subclasses.
        self._p = main_window.sim_conf.p

        # Widgets editing this export's name and type.
        self._widget_kind = main_window.get_widget(
            widget_name=self._widget_name_prefix + 'kind')
        self._widget_name = main_window.get_widget(
            widget_name=self._widget_name_prefix + 'name')

        # If any of these are *NOT* of the expected type, raise an exception.
        objects.die_unless_instance(
            obj=self._widget_kind, cls=QBetseeSimConfComboBoxSequence)
        objects.die_unless_instance(
            obj=self._widget_name, cls=QBetseeSimConfLineEdit)

        # Sequence of the string types of all exports supported by the pipeline
        # associated with this pager (in sorted lexicographic order).
        export_confs_kind = self._pipe_cls.iter_runners_metadata_kind()

        # Prepopulate the widget editing this export's type with this sequence,
        # which remains constant across repeated reinitializations of this
        # combo box (i.e., calls to the reinit() method).
        self._widget_kind.add_items_iconless(items_text=export_confs_kind)


    @type_check
    def reinit(self, main_window: QMainWindow, list_item_index: int) -> None:

        # YAML-backed export configuration currently controlled by this pager.
        export_conf = sequences.get_index(
            sequence=self._yaml_list, index=list_item_index)

        # Type of this export configuration.
        export_conf_cls = type(export_conf)

        # Initialize these widgets.
        self._widget_name.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=export_conf_cls.name,
            sim_conf_alias_parent=export_conf,
            is_reinitable=True,
        )
        self._widget_kind.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=export_conf_cls.kind,
            sim_conf_alias_parent=export_conf,
            is_reinitable=True,
        )
