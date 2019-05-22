#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Submodule both instantiating and initializing the :class:`QApplication`
singleton for this application.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT*
#   include BETSE modules, which are *NOT* guaranteed to exist at this point.
#   For simplicity, however, all core PySide2 submodules are assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import logging
from PySide2.QtCore import Qt, QCoreApplication
from PySide2.QtGui import QGuiApplication
from PySide2.QtWidgets import QApplication, qApp
from betsee import guimetadata
from betsee.guiexception import BetseePySideApplicationException

# ....................{ GLOBALS                           }....................
_IS_INITTED = False
'''
``True`` only if the :func:`init` function has already been called.

That function uses this private boolean to guard against repeated invocations
of the :func:`init` function from multiple modules in the same Python process.
Unlike the comparable :func:`betse.lib.libs.init` function, the :func:`init`
function defined by this submodule does *not* support repeated calls and hence
*must* explicitly guard against that uncommon edge case.
'''

# ....................{ EXCEPTIONS                        }....................
def die_unless_initted() -> None:
    '''
    Raise an exception unless the :func:`init` function has been called and
    hence instantiated the :class:`QApplication` singleton for this
    application.

    For safety, this function additionally raises an exception if the
    :func:`init` function has been called but the :class:`QApplication`
    singleton instantiated by that function no longer exists.

    Raises
    ----------
    BetseePySideApplicationException
        If either:
        * The :func:`init` function has yet to be called.
        * The :class:`QApplication` singleton has yet to be instantiated.
    '''

    # If this function has yet to be be called, raise an exception.
    if not _IS_INITTED:
        raise BetseePySideApplicationException(QCoreApplication.translate(
            'guiapp',
            'betsee.util.app.guiapp.init() has yet to be called.'))

    # If the "QApplication" singleton is uninstantiated. raise an exception.
    if qApp is None:
        raise BetseePySideApplicationException(QCoreApplication.translate(
            'guiapp',
            '"QApplication" singleton uninstantiated '
            '(e.g., as betsee.util.app.guiapp.init() has yet to be called).'))

# ....................{ GETTERS                           }....................
def get_app() -> QApplication:
    '''
    Initialized :class:`QApplication` singleton for this application if
    instantiated by a prior call to the :func:`init` function *or* raise an
    exception otherwise (i.e., if that function has yet to be called).

    Contrary to nomenclature, the :class:`QApplication` class confusingly
    subclasses the :class:`QGuiApplication` base class in a manner optimized
    for widgets. Ergo, the former is *always* preferable to the latter.

    Design
    ----------
    This function does *not* implicitly call the :func:`init` function if the
    :class:`QApplication` singleton has yet to be instantiated. While
    non-intuitive and arguably inconvenient, this is intentional. Implicitly
    calling that function would technically be trivial but invite subtle (and
    hence non-debuggable) issues; in particular, the order in which the
    :func:`init` and :func:`betse.lib.libs.reinit` methods are called is very
    significant and hence must *not* be left up to non-deterministic chance.

    Caveats (Exceptions)
    ----------
    Avoid directly accessing the low-level :attr:`PySide2.QtWidgets.qApp`
    global, which this higher-level function wraps. Since that global is
    typically ``None`` prior to the first call to the :func:`init` function,
    directly accessing that global sufficiently early in runtime may raise
    non-human-readable exceptions *or* induce low-level segmentation faults
    from Qt itself resembling:

        QWidget: Must construct a QApplication before a QWidget
        [1]    30475 abort      betsee -v

    In contrast, this function *always* raises human-readable exceptions.

    Caveats (Attributes)
    ----------
    Avoid attempting to add application-specific instance variables to the
    low-level :attr:`PySide2.QtWidgets.qApp` global returned by this function,
    as that global silently ignores all such attempts. While this constraint
    could technically be circumvented by globally persisting the
    :class:`QApplication` singleton created by the :func:`init` function as a
    module-scoped Python singleton, doing so would incur subtle issues of its
    own -- including complications in both garbage collection and accidental
    collision with standard Qt attributes.

    Returns
    ----------
    QApplication
        Initialized :class:`QApplication` singleton for this application.

    Raises
    ----------
    BetseePySideApplicationException
        If either:
        * The :func:`init` function has yet to be called.
        * The :class:`QApplication` singleton has yet to be instantiated.
    '''

    # If either the init() funtion has yet to be called *OR* the "QApplication"
    # singleton is uninstantiated. raise an exception.
    die_unless_initted()

    # Else, this singleton is *NOT* "None". Return this singleton.
    return qApp

# ....................{ INITIALIZERS                      }....................
def init() -> None:
    '''
    Instantiate and initialize the :class:`QApplication` singleton for this
    application (i.e., the :attr:`PySide2.QApplication.qApp` instance) if this
    function has not already been called *or* silently reduce to a noop
    otherwise (i.e., if this function has already been called).
    '''

    # If this function has already been called, noop.
    global _IS_INITTED
    if     _IS_INITTED:
        return

    # Destroy the existing "QApplication" singleton (if any).
    _deinit_qt_app()

    # Set static attributes of the "QApplication" class *BEFORE* defining the
    # singleton instance of this class.
    _init_qt()

    # Instantiate a singleton of this class.
    _init_qt_app()

    # Record this function as having been called *AFTER* successfully doing so.
    _IS_INITTED = True

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
    initialize this singleton on first importation without our explicit
    consent. There isn't much we can do about it; this is the next best thing.

    If this singleton is _not_ explicitly destroyed, PySide2 raises the
    following exception on attempting to re-initialize another such singleton:

        RuntimeError: Please destroy the QApplication singleton before creating
        a new QApplication instance.
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

# ....................{ INITIALIZERS : qt                 }....................
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
    _init_qt_metadata()

    # Initialize all application-wide dots per inch (DPI) attributes.
    _init_qt_dpi()

    # Initialize all application-wide QSettings attributes.
    guisettings.init()


def _init_qt_metadata() -> None:
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
        from betse.util.os import displays

        # If none of the following conditions is satisfied:
        #
        # * The current platform is macOS, which natively supports high-DPI
        #   scaling out-of-the-box. Moreover, the official documentation for
        #   the Qt attribute set below explicitly states: "Supported platforms
        #   are X11, Windows and Android." For safety, this attribute is *NOT*
        #   enabled under macOS.
        # * The current platform is Linux and the current display server is a
        #   Wayland compositor, which all natively support high-DPI scaling.
        # * The current platform is Windows >= 10, which mostly natively
        #   supports high-DPI scaling to a sufficient degree to warrant
        #   avoiding non-native emulation here.
        #
        # Then the current display environment does *NOT* natively support
        # high-DPI scaling. Notably, the Windows and X11 display environments
        # both fail to do so. In this case, we inform Qt that it should attempt
        # to do so via emulation at the framework level, converting all
        # previously physical pixels defined throughout this application into
        # logical pixels portable across displays sporting varying DPI.
        if not displays.is_dpi_scaling():
            logging.debug('Initializing high-DPI scaling emulation...')
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # If any such submodule is unimportable, log a non-fatal error and
    # continue.  Since BETSE is a mandatory dependency, its unimportability
    # would typically constitute a fatal error. Since subsequent dependency
    # checking is guaranteed to raise a human-readable exception on our behalf,
    # however, we needn't uselessly duplicate this checking here.
    except ImportError as exception:
        logging.error(str(exception))

    # Permit the QIcon.pixmap() method to generate high-DPI pixmaps larger
    # than the requested size (i.e., a devicePixelRatio() larger than 1.0).
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

# ....................{ INITIALIZERS : globals            }....................
def _init_qt_app() -> QApplication:
    '''
    Instantiate and return the :class:`QApplication` singleton for this
    application.
    '''

    # Avoid circular import dependencies.
    # from betsee.util.filter.guifiltertooltip import (
    #     QBetseePlaintextTooltipEventFilter)

    # Log this instantiation.
    logging.debug('Instantiating Qt application singleton...')

    #FIXME: Actually, this isn't *QUITE* right. At least the "-session" option
    #should be forwarded on to the "QApplication" constructor, required for
    #application restoration after having been previously suspended. See the
    #QSessionManager::setRestartCommand() method documentation for details.
    #
    #Note that this option *MUST* be named "-session" unless the
    #setRestartCommand() method is called to override this default. We'd
    #certainly prefer a *nix-style option named "--session-id" instead,
    #however. Can we make this happen?

    # For safety, initialize this application with *NO* command-line arguments
    # regardless of whether the current CLI was passed arguments. The subset of
    # arguments parsed by this widget are of no interest to end users and
    # developers alike. Since this object consumes all arguments it parses,
    # permitting this object to arbitrarily parse and hence consume arguments
    # encourages conflicts with future versions of Qt. In theory, Qt could
    # expand the subset of arguments parsed by this object to those already
    # parsed by the current CLI! That's bad.
    gui_app = QApplication([])

    #FIXME: Document why this might be an awful idea: notably, the GIL blocking
    #multithreaded event handling. If this is indeed one of several culprits
    #(which seems fairly likely), we'll want to revise our original
    #StackOverflow answer advising usage of this paradigm under Python. Clearly,
    #this approach only applies to languages other than Python -- notably, C++.
    #FIXME: O.K.; we've verified by manual inspection that this event filter
    #does indeed slow event handling down by approximately 200% when attempting
    #to perform multithreading -- clearly due to the GIL. Given that, we'll
    #need to manually implement the equivalent of this filter by:
    #
    #* For each plaintext (i.e., non-HTML) tooltip across the entire
    #  application...
    #  * Coercively embed that tooltip in HTML tags.
    #
    #To do so sanely, we'll probably want to perform a simple global
    #search-and-replace in our "betsee.ui" file. *sigh*

    # Install an application-wide event filter globally addressing severe
    # issues in Qt's default plaintext tooltip behaviour.
    # gui_app.installEventFilter(QBetseePlaintextTooltipEventFilter(gui_app))

    # Return this application.
    return gui_app
