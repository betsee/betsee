#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **monkey-patch** (i.e., runtime replacement of Python logic embedded
in third-party dependencies with application-specific Python logic).
'''

# ....................{ IMPORTS                           }....................
import sys
from PySide2 import QtCore, QtWidgets
from betse.util.io.log import logs
# from betse.util.type.types import type_check, IterableTypes
from pyside2uic import uiparser

# ....................{ PATCHERS                          }....................
def patch_all() -> None:
    '''
    Monkey-patch *all* :mod:`PySide2` callables whose version-specific
    implementations are well-known to be broken (if any).
    '''

    patch_pyside2uic_uiparser_UIParser_createWidget()

# ....................{ PATCHERS ~ createWidget           }....................
def patch_pyside2uic_uiparser_UIParser_createWidget() -> None:
    '''
    Monkey-patch the :meth:`pyside2uic.uiparser.UIParser.createWidget` method
    if the :mod:`pyside2uic` package is unimportable *and* the currently
    installed version of :mod:`PySide2` targets the obsolete Qt 5.6 (LTS) line
    of stable releases *or* silently reduce to a noop otherwise.

    That method raises non-human-readable exceptions under Qt 5.6 on attempting
    to parse button group labels: e.g.,

        AttributeError: 'str' object has no attribute 'string'

        Traceback (most recent call last):
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betse/util/cli/cliabc.py", line 180, in run profile_filename=self._profile_filename,
        File "", line 65, in func_type_checked
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betse/util/py/pyprofile.py", line 114, in profile_callable
        profile_filename=profile_filename,
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betse/util/py/pyprofile.py", line 130, in _profile_callable_none
        return call(*args, **kwargs)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betsee/cli/guicli.py", line 236, in _do
        app_gui = BetseeGUI(sim_conf_filename=self._sim_conf_filename)
        File "", line 15, in func_type_checked
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betsee/gui/guimain.py", line 255, in init
        guicache.cache_py_files()
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betsee/gui/guicache.py", line 64, in cache_py_files
        _cache_py_ui_file()
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betsee/gui/guicache.py", line 198, in _cache_py_ui_file
        promote_obj_name_to_class=_PROMOTE_OBJ_NAME_TO_CLASS,
        File "", line 35, in func_type_checked
        File "/home/eric/anaconda3/lib/python3.6/site-packages/betsee/util/io/xml/guiui.py", line 280, in convert_ui_to_py_file_if_able
        from_imports=False,
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/Compiler/compiler.py", line 91, in compileUi
        w = self.parse(input_stream)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 871, in parse
        actor(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 714, in createUserInterface
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 427, in createLayout
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 464, in handleItem
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 427, in createLayout
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 464, in handleItem
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 427, in createLayout
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 464, in handleItem
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 427, in createLayout
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 464, in handleItem
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 197, in createWidget
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 427, in createLayout
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 464, in handleItem
        self.traverseWidgetTree(elem)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 692, in traverseWidgetTree
        handler(self, child)
        File "/home/eric/anaconda3/lib/python3.6/site-packages/pyside2uic/uiparser.py", line 214, in createWidget
        bg_name = bg_i18n.string

    This function resolves this issue by dynamically replacing the entirety of
    this method's in-memory implementation with an implementation back-ported
    from the Qt 5.11 line of stable releases. While non-ideal, this ad-hoc
    solution is the only sane means of doing so.
    '''

    # Avoid circular import dependencies.
    from betsee.lib import guilib
    from betsee.lib.pyside2 import guipsd

    # If...
    if not (
        # The optional "pyside2uic" dependency is available *AND*...
        guilib.is_runtime_optional('pyside2uic') and
        # The currently installed version of PySide2 is *NOT* specific to the
        # obsolete Qt 5.6.* (LTS) line of stable releases...
        guipsd.is_version_5_6()
    ):
        # Log this noop.
        logs.log_debug(
            'Preserving non-broken PySide2 > 5.6.* method '
            'UIParser.createWidget()...')

        # Reduce to a noop.
        return

    # Log this monkey-patch.
    logs.log_debug(
        'Monkey-patching broken PySide2 5.6.* method '
        'UIParser.createWidget()...')

    # Apply this monkey-patch.
    uiparser.UIParser.createWidget = (
        _pyside2uic_uiparser_UIParser_createWidget)


def _pyside2uic_uiparser_UIParser_createWidget(self, elem):
    '''
    :meth:`pyside2uic.uiparser.UIParser.createWidget` method monkey-patched to
    avoid raising non-human-readable exceptions under Qt 5.6 on attempting
    to parse button group labels.

    See Also
    ----------
    :func:`patch_pyside2uic_uiparser_UIParser_createWidget`
        Function conditionally applying this monkey-patch if necessary.
    '''

    self.column_counter = 0
    self.row_counter = 0
    self.item_nr = 0
    self.itemstack = []
    self.sorting_enabled = None

    widget_class = elem.attrib['class'].replace('::', '.')
    if widget_class == 'Line':
        widget_class = 'QFrame'

    # Ignore the parent if it is a container
    parent = self.stack.topwidget

    # if is a Menubar on MacOS
    macMenu = (sys.platform == 'darwin') and (widget_class == 'QMenuBar')

    if isinstance(parent, (QtWidgets.QDockWidget, QtWidgets.QMdiArea,
                           QtWidgets.QScrollArea, QtWidgets.QStackedWidget,
                           QtWidgets.QToolBox, QtWidgets.QTabWidget,
                           QtWidgets.QWizard)) or macMenu:
        parent = None


    # See if this is a layout widget.
    if widget_class == 'QWidget':
        if parent is not None:
            if not isinstance(parent, QtWidgets.QMainWindow):
                self.layout_widget = True

    self.stack.push(self.setupObject(widget_class, parent, elem))

    if isinstance(self.stack.topwidget, QtWidgets.QTableWidget):
        self.stack.topwidget.setColumnCount(len(elem.findall("column")))
        self.stack.topwidget.setRowCount(len(elem.findall("row")))

    self.traverseWidgetTree(elem)
    widget = self.stack.popWidget()

    self.layout_widget = False

    if isinstance(widget, QtWidgets.QTreeView):
        self.handleHeaderView(elem, "header", widget.header())

    elif isinstance(widget, QtWidgets.QTableView):
        self.handleHeaderView(elem, "horizontalHeader",
                              widget.horizontalHeader())
        self.handleHeaderView(elem, "verticalHeader",
                              widget.verticalHeader())

    elif isinstance(widget, QtWidgets.QAbstractButton):
        bg_i18n = self.wprops.getAttribute(elem, "buttonGroup")
        if bg_i18n is not None:
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # PATCH: This monkey-patch replaces the following one-liner:
            #     bg_name = bg_i18n.string
            # ...with the following if conditional harvested from PySide 5.11:
            if isinstance(bg_i18n, str):
                bg_name = bg_i18n
            else:
                bg_name = bg_i18n.string
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            for bg in self.button_groups:
                if bg.objectName() == bg_name:
                    break
                else:
                    bg = self.factory.createQObject("QButtonGroup", bg_name,
                                                    (self.toplevelWidget, ))
                    bg.setObjectName(bg_name)
                    self.button_groups.append(bg)

            bg.addButton(widget)

    if self.sorting_enabled is not None:
        widget.setSortingEnabled(self.sorting_enabled)
        self.sorting_enabled = None

    if self.stack.topIsLayout():
        lay = self.stack.peek()
        gp = elem.attrib["grid-position"]

        if isinstance(lay, QtWidgets.QFormLayout):
            lay.setWidget(gp[0], self._form_layout_role(gp), widget)
        else:
            lay.addWidget(widget, *gp)

    topwidget = self.stack.topwidget

    if isinstance(topwidget, QtWidgets.QToolBox):
        icon = self.wprops.getAttribute(elem, "icon")
        if icon is not None:
            topwidget.addItem(widget, icon, self.wprops.getAttribute(elem, "label"))
        else:
            topwidget.addItem(widget, self.wprops.getAttribute(elem, "label"))

        tooltip = self.wprops.getAttribute(elem, "toolTip")
        if tooltip is not None:
            topwidget.setItemToolTip(topwidget.indexOf(widget), tooltip)

        elif isinstance(topwidget, QtWidgets.QTabWidget):
            icon = self.wprops.getAttribute(elem, "icon")
            if icon is not None:
                topwidget.addTab(widget, icon, self.wprops.getAttribute(elem, "title"))
            else:
                topwidget.addTab(widget, self.wprops.getAttribute(elem, "title"))

        tooltip = self.wprops.getAttribute(elem, "toolTip")
        if tooltip is not None:
            topwidget.setTabToolTip(topwidget.indexOf(widget), tooltip)

        elif isinstance(topwidget, QtWidgets.QWizard):
            topwidget.addPage(widget)

        elif isinstance(topwidget, QtWidgets.QStackedWidget):
            topwidget.addWidget(widget)

        elif isinstance(topwidget, (QtWidgets.QDockWidget, QtWidgets.QScrollArea)):
            topwidget.setWidget(widget)

        elif isinstance(topwidget, QtWidgets.QMainWindow):
            if type(widget) == QtWidgets.QWidget:
                topwidget.setCentralWidget(widget)
            elif isinstance(widget, QtWidgets.QToolBar):
                tbArea = self.wprops.getAttribute(elem, "toolBarArea")

            if tbArea is None:
                topwidget.addToolBar(widget)
            else:
                topwidget.addToolBar(tbArea, widget)

            tbBreak = self.wprops.getAttribute(elem, "toolBarBreak")

            if tbBreak:
                topwidget.insertToolBarBreak(widget)

            elif isinstance(widget, QtWidgets.QMenuBar):
                topwidget.setMenuBar(widget)
            elif isinstance(widget, QtWidgets.QStatusBar):
                topwidget.setStatusBar(widget)
            elif isinstance(widget, QtWidgets.QDockWidget):
                dwArea = self.wprops.getAttribute(elem, "dockWidgetArea")
                topwidget.addDockWidget(QtCore.Qt.DockWidgetArea(dwArea),
                                        widget)
