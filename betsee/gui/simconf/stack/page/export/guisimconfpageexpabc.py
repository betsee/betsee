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

# ....................{ IMPORTS                           }....................
# from PySide2.QtCore import QCoreApplication #, Signal, Slot
from PySide2.QtWidgets import QMainWindow
from betse.science.pipe.export.pipeexpabc import SimPipeExportABC
# from betse.util.io.log import logs
from betse.util.type.decorator.deccls import abstractproperty
from betse.util.type.iterable import sequences
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


    @type_check
    def init(self, main_window: QMainWindow) -> None:

        # Initialize our superclass with all passed parameters.
        super().init(main_window)

        # Classify variables of this main window required by most subclasses.
        self._p = main_window.sim_conf.p


    @type_check
    def reinit(self, main_window: QMainWindow, list_item_index: int) -> None:

        # YAML-backed export configuration currently controlled by this pager.
        export_conf = sequences.get_index(
            sequence=self._yaml_list, index=list_item_index)

        # Type of this export configuration.
        export_conf_cls = type(export_conf)

        # Sequence of the string types of all exporters supported by the
        # pipeline associated with this pager (in sorted lexicographic order).
        export_confs_kind = self._pipe_cls.iter_runners_metadata_kind()

        # Widgets editing this export's name and type.
        widget_name = main_window.get_widget(
            widget_name=self._widget_name_prefix + 'name')
        widget_kind = main_window.get_widget(
            widget_name=self._widget_name_prefix + 'kind')

        # Remove all items previously added to the combo box editing this type
        # *BEFORE* adding these items back to this box. If *NOT* done, the
        # subsequent widget_kind.init() call would correctly raise an exception
        # on detecting an attempt to add duplicate items to this combo box.
        widget_kind.clear()

        # Initialize these widgets.
        widget_name.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=export_conf_cls.name,
            sim_conf_alias_parent=export_conf,
            is_reinitable=True,
        )

        #FIXME: *UGH.* This currently induces infinite recursion due to an undo
        #push cycle. To correct this, we'll need to generalize the
        #superclass reinit() implementation to avoid pushing undo commands for
        #the duration of this method call. *sigh*
        widget_kind.init(
            sim_conf=main_window.sim_conf,
            sim_conf_alias=export_conf_cls.kind,
            sim_conf_alias_parent=export_conf,
            items_iconless_text=export_confs_kind,
            is_reinitable=True,
        )
