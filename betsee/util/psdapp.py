#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:class:`QApplication` singleton for this application, containing all Qt objects
(e.g., widgets) to be displayed.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT* include
#   BETSE modules, which is *NOT* guaranteed to exist at this point. For
#   simplicity, PySide2 is assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import logging, platform
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication

# ....................{ GLOBALS                            }....................
# This global is initialized by the _init() function called below.
APP_GUI = None
'''
:class:`QApplication` singleton for this application, containing all Qt objects
(e.g., widgets) to be displayed.

Design
----------
For safety, this object is persisted as a module rather than local variable
(e.g., of the :func:`_show_betse_exception` function). Since the order in which
Python garbage collects local variables that have left scope is effectively
random, persisting this object as a local variable would permit Python to
garbage collect this application *before* this application's child widgets on
program termination, resulting in non-human-readable Qt exceptions on some but
not all terminations. (That would be bad.)

Contrary to expected nomenclature, note that the :class:`QApplication` class
confusingly subclasses the :class:`QGuiApplication` base class in a manner
optimized for widgets; thus, the former is *always* preferable to the latter.

See Also
----------
:data:`PySide2.QtWidgets.qApp`
    Synonym of this attribute, providing the same underlying object.
'''

# ....................{ INITIALIZERS                       }....................
def _init() -> None:
    '''
    Initialize the :class:`QApplication` singleton for this application.
    '''

    # Set static attributes of the "QApplication" class *BEFORE* defining the
    # singleton instance of this class.
    _init_qt()

    # Instantiate a singleton of this class.
    _init_app()

# ....................{ INITIALIZERS : qt                  }....................
def _init_qt() -> None:
    '''
    Set static attributes of the :class:`QApplication` class *before* the
    singleton instance of this class is defined.

    Technically, some of these attributes (e.g.,
    :attr:`Qt.AA_UseHighDpiPixmaps`) are safely definable at any time. Since
    others (e.g. ,:attr:`Qt.AA_EnableHighDpiScaling`) are *not*, all such
    attributes are preemptively defined here for both simplicity and safety.

    These attributes pertain to the :class:`QApplication` singleton rather than
    this singleton's :class:`QMainWindow` instance implemented by the
    XML-formatted UI file exported by Qt Creator; thus, these attributes
    *cannot* be specified by this file but *must* instead be manually
    implemented in Python.
    '''

    # Initialize all application-wide dots per inch (DPI) attributes.
    _init_qt_dpi()


def _init_qt_dpi() -> None:
    '''
    Set static attributes of the :class:`QApplication` class pertaining to dots
    per inch (DPI) and, specifically, high-DPI displays.

    See Also
    ----------
    https://blog.qt.io/blog/2016/01/26/high-dpi-support-in-qt-5-6
        *High-DPI Support in Qt 5.6,* article colloquially describing the
        attributes initialized by this method.
    '''

    #FIXME: Wayland also natively supports high-DPI scaling. If the current
    #display manager is a Wayland compositor (e.g., Weston), this attribute
    #should *NOT* be enabled.

    # If the current platform is *NOT* macOS, emulate high-DPI scaling. The
    # Windows and X11 display environments both fail to natively support
    # high-DPI scaling, mandating that Qt attempt to do so via emulation at
    # the framework level. This emulation converts all previously physical
    # pixels defined throughout the application into logic pixels portable
    # across displays sporting varying DPI.
    #
    # MacOS already implicitly enables high-DPI scaling out-of-the-box.
    # Moreover, this attribute's official documentation explicitly states:
    # "Supported platforms are X11, Windows and Android." For safety, this
    # attribute is *NOT* enabled under macOS.
    #
    # Since BETSE is *NOT* guaranteed to be available at this point, this
    # conditional reimplements the betse.util.os.oses.is_macos() function.
    if platform.system() != 'Darwin':
        logging.debug('Emulating high-DPI scaling...')
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    # Permit the QIcon.pixmap() method to generate high-DPI pixmaps larger
    # than the requested size (i.e., a devicePixelRatio() larger than 1.0).
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

# ....................{ INITIALIZERS : globals             }....................
def _init_app() -> None:
    '''
    Instantiate the :class:`QApplication` singleton for this application.
    '''

    # Permit the following globals to be redefined.
    global APP_GUI

    # Log this instantiation.
    logging.debug('Instantiating application singleton...')

    # For safety, initialize this application with *NO* command-line arguments
    # regardless of whether the current CLI was passed arguments. The subset of
    # arguments parsed by this widget are of no interest to end users and
    # developers alike. Since this object consumes all arguments it parses,
    # permitting this object to arbitrarily parse and hence consume arguments
    # encourages conflicts with future versions of Qt. In theory, Qt could
    # expand the subset of arguments parsed by this object to those already
    # parsed by the current CLI! That's bad.
    APP_GUI = QApplication([])

# ....................{ MAIN                               }....................
# Initialize this submodule.
_init()
