#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Submodule both instantiating and initializing the :class:`QApplication`
singleton for this application with sane defaults on submodule importation.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python, PySide2, and BETSEE modules. This does
#   *NOT* include BETSE modules, whose importability has yet to be validated.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import logging
from PySide2.QtCore import Qt, QCoreApplication
from PySide2.QtGui import QGuiApplication
from PySide2.QtWidgets import QApplication
from betsee import guimetadata

# ....................{ GLOBALS                            }....................
#FIXME: This global appears to have been a profound, albeit ultimately trivial,
#mistake. Maintaining yet another in-memory reference to the "qApp" singleton
#appears to invite non-deterministic exceptions on window closure. It's also
#completely unnecessary, as Qt already provides the "QApplication.qApp"
#reference for exactly this purpose.
#
#Refactor the codebase as follows:
#
#* Define a new get_app() function in this submodule as follows:
#
#    def get_app() -> QApplication:
#        return QApplication.qApp
#
#* Replace all references to "GUI_APP" with calls to guiapp.get_app(). Why a
#  separate function? So that we can reuse the extensive (and extremely
#  helpful) docstring defined below. Also, who knows? Having a separate getter
#  function allows for all sorts of essential shenanigans in the future.
#* Remove this global entirely.

# This global is initialized by the _init() function called below.
GUI_APP = None
'''
:class:`QApplication` singleton for this application, containing all Qt objects
(e.g., widgets) to be displayed.

For convenience, this singleton provides application-specific instance
variables whose names are prefixed by ``betsee_`` to avoid nomenclature
conflicts with Qt itself (e.g., ``betsee_main_window``, the main window widget
for this application). See the "Attributes" section for details.

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

Attributes
----------
betsee_main_window : QBetseeMainWindow
    Main window widget for this application.

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

    # Destroy an existing "QApplication" singleton if any.
    _deinit_qt_app()

    # Set static attributes of the "QApplication" class *BEFORE* defining the
    # singleton instance of this class.
    _init_qt()

    # Instantiate a singleton of this class.
    _init_qt_app()

# ....................{ DEINITIALIZERS                     }....................
#FIXME: Actually, this error appears to be induced by initializing third-party
#BETSE libraries and hence the "Qt5Agg" backend *BEFORE* instantiating this
#singleton here. Clearly, the order of these two operations needs to be
#reversed. After that is done, this function should be:
#
#* Renamed to die_if_qt_app().
#* Refactored to raise a human-readable exception, which should explicitly note
#  the likelihood of a previously imported Python package (e.g., "matplotlib")
#  having externally instantiated this singleton already.
#* Redocumented as such.

def _deinit_qt_app() -> None:
    '''
    Destroy the existing :class:`QApplication` singleton with a non-fatal
    warning if such a singleton has been previously initialized elsewhere *or*
    silently reduce to a noop otherwise.

    While this condition should arguably constitute a fatal error inducing a
    raised exception, various versions of PySide2 appear to erroneously
    initialize this singleton on first importation without our explicit consent.
    Since there isn't much we can do about that, this is the next best thing.

    If this singleton is _not_ explicitly destroyed, PySide2 raises the
    following exception on attempting to re-initialize another such singleton:

        RuntimeError: Please destroy the QApplication singleton before creating a new QApplication instance.
    '''

    # Existing "QApplication" singleton if any or "None" otherwise.
    app_prior = QCoreApplication.instance()

    # If an existing "QApplication" singleton has already been initialized...
    if app_prior is not None:
        # Log a non-fatal warning.
        logging.warning(
            'Destroying erroneously instantiated Qt application singleton...')

        # Destroy this singleton.
        app_prior.quit()

# ....................{ INITIALIZERS : qt                  }....................
def _init_qt() -> None:
    '''
    Initialize static attributes of the :class:`QApplication` class or
    subclasses thereof (e.g., :class:`QCoreApplication`,
    :class:`QGuiApplication`) *before* the singleton instance of this class is
    defined.

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

    # Avoid circular import dependencies.
    from betsee.util.io import guisettings

    # Initialize all application-wide core attributes (e.g., name, version).
    _init_qt_core()

    # Initialize all application-wide dots per inch (DPI) attributes.
    _init_qt_dpi()

    # Initialize all application-wide QSettings attributes.
    guisettings.init()


def _init_qt_core() -> None:
    '''
    Initialize all static attributes of the :class:`QCoreApplication` class
    signifying application-wide core properties (e.g., name, version).
    '''

    # Log this initialization.
    logging.debug('Initializing static Qt attributes...')

    # High-level human-readable application name intended *ONLY* for display.
    QGuiApplication.setApplicationDisplayName(guimetadata.NAME)

    # Low-level machine-readable application name and version, each intended
    # both for display (e.g., to end users) and internal inspection.
    QCoreApplication.setApplicationName(guimetadata.NAME)
    QCoreApplication.setApplicationVersion(guimetadata.VERSION)

    # Low-level machine-readable organization name and domain.
    QCoreApplication.setOrganizationName(guimetadata.ORG_NAME)
    QCoreApplication.setOrganizationDomain(guimetadata.ORG_DOMAIN_NAME)


def _init_qt_dpi() -> None:
    '''
    Initialize all static attributes of the :class:`QApplication` class
    pertaining to dots per inch (DPI) and, specifically, high-DPI displays.

    See Also
    ----------
    https://blog.qt.io/blog/2016/01/26/high-dpi-support-in-qt-5-6
        *High-DPI Support in Qt 5.6,* article colloquially describing the
        attributes initialized by this method.
    '''

    # Attempt to...
    try:
        # Import BETSE submodules, whose importability has yet to be validated.
        from betse.util.os import oses
        from betse.util.os import displays

        # If none of the following conditions is satisfied:
        #
        # * The current platform is macOS, which natively supports high-DPI
        #   scaling out-of-the-box. Moreover, the official documentation for the
        #   Qt attribute set below explicitly states: "Supported platforms are
        #   X11, Windows and Android." For safety, this attribute is *NOT*
        #   enabled under macOS.
        # * The current platform is Linux and the current display server is a
        #   Wayland compositor, which all natively support high-DPI scaling.
        #
        # Then the current display environment does *NOT* natively support
        # high-DPI scaling. Notably, the Windows and X11 display environments
        # both fail to do so. In this case, we inform Qt that it should attempt
        # to do so via emulation at the framework level, converting all
        # previously physical pixels defined throughout this application into
        # logical pixels portable across displays sporting varying DPI.
        if not (oses.is_macos() or displays.is_linux_wayland()):
            logging.debug('Initializing high-DPI scaling emulation...')
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # If any such submodule is unimportable, log a non-fatal error and continue.
    # Since BETSE is a mandatory dependency, its unimportability would typically
    # constitute a fatal error. Since subsequent dependency checking is
    # guaranteed to raise a human-readable exception on our behalf, however, we
    # needn't uselessly duplicate this checking here.
    except ImportError as exception:
        logging.error(str(exception))

    # Permit the QIcon.pixmap() method to generate high-DPI pixmaps larger
    # than the requested size (i.e., a devicePixelRatio() larger than 1.0).
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

# ....................{ INITIALIZERS : globals             }....................
def _init_qt_app() -> None:
    '''
    Instantiate the :class:`QApplication` singleton for this application.
    '''

    # Avoid circular import dependencies.
    from betsee.util.filter.guifiltertooltip import (
        QBetseePlaintextTooltipEventFilter)

    # Permit the following globals to be redefined.
    global GUI_APP

    # Log this instantiation.
    logging.debug('Instantiating application singleton...')

    #FIXME: Actually, this isn't *QUITE* right. At least the "-session" option
    #should be forwarded on to the "QApplication" constructor, required for
    #application restoration after having been previously suspended. See the
    #QSessionManager::setRestartCommand() method documentation for details.
    #
    #Note that this option *MUST* be named "-session" unless the
    #setRestartCommand() method is called to override this default. We'd
    #certainly prefer a *nix-style option named "--session-id" instead, however.
    #Can we make this happen?

    # For safety, initialize this application with *NO* command-line arguments
    # regardless of whether the current CLI was passed arguments. The subset of
    # arguments parsed by this widget are of no interest to end users and
    # developers alike. Since this object consumes all arguments it parses,
    # permitting this object to arbitrarily parse and hence consume arguments
    # encourages conflicts with future versions of Qt. In theory, Qt could
    # expand the subset of arguments parsed by this object to those already
    # parsed by the current CLI! That's bad.
    GUI_APP = QApplication([])

    # Nullify all application-specific instance variables of this singleton.
    GUI_APP.betsee_main_window = None

    # Install an application-wide event filter globally addressing severe issues
    # in Qt's default plaintext tooltip behaviour.
    GUI_APP.installEventFilter(QBetseePlaintextTooltipEventFilter(GUI_APP))

# ....................{ MAIN                               }....................
# Initialize this submodule.
_init()
