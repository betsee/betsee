#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Application-specific exception hierarchy.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To raise human-readable exceptions on application startup, the
# top-level of this module may import *ONLY* from submodules guaranteed to:
# * Exist, including standard Python and BETSEE modules. This does *NOT* include
#   BETSE modules, which are *NOT* guaranteed to exist at this point. For
#   simplicity, however, all core PySide2 submodules are assumed to exist.
# * Never raise exceptions on importation (e.g., due to module-level logic).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from PySide2.QtCore import QCoreApplication
from abc import ABCMeta

# ....................{ EXCEPTIONS ~ superclass            }....................
#FIXME: Introduce into the "betse.exceptions" submodule as a new
#"BetseVerboseException" base class from which all other exception classes
#defined by that submodule should eventually subclass.
class BetseeException(Exception, metaclass=ABCMeta):
    '''
    Abstract base class of all application-specific exceptions.

    Attributes
    ----------
    title : str
        Human-readable title associated with this exception, typically
        constrained to at most two to three words.
    synopsis : str
        Human-readable synopsis tersely describing this exception, typically
        constrained to a single sentence.
    exegesis : optional[str]
        Human-readable explanation fully detailing this exception if any,
        typically spanning multiple sentences, *or* ``None`` otherwise (i.e.,
        if no such explanation is defined).
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(
        self,
        synopsis: str,
        title: str = None,
        exegesis: str = None,
    ) -> None:
        '''
        Initialize this exception.

        Parameters
        ----------
        synopsis : str
            Human-readable synopsis tersely describing this exception, typically
            constrained to a single sentence.
        title : optional[str]
            Human-readable title associated with this exception, typically
            constrained to at most two to three words. Defaults to ``None``, in
            which case the title defaults to the translated string returned by
            the :meth:`_title_default` property.
        exegesis : optional[str]
            Human-readable explanation fully detailing this exception, typically
            spanning multiple sentences. Defaults to ``None``, in which case no
            such explanation is defined.
        '''

        # Since the @type_check decorator is unavailable at this early point in
        # application startup, manually assert the types of these parameters.
        assert isinstance(synopsis, str), '"{}" not a string.'.format(synopsis)
        assert isinstance(title, (str, type(None))), (
            '"{}" neither a string nor "None".'.format(title))
        assert isinstance(exegesis, (str, type(None))), (
            '"{}" neither a string nor "None".'.format(exegesis))

        # Initialize our superclass with the concatenation of this
        # exception's synopsis, a space, and exegesis (defaulting to the empty
        # string when unpassed).
        super().__init__(
            synopsis + (' ' + exegesis if exegesis is not None else ''))

        # If no title was explicitly passed, fallback to the default title
        # defined by this exception subclass.
        if title is None:
            title = self._title_default

        # Classify all passed parameters.
        self.title = title
        self.synopsis = synopsis
        self.exegesis = exegesis

    # ..................{ PROPERTIES                         }..................
    @property
    def _title_default(self) -> str:
        '''
        Default human-readable title associated with *all* exceptions of this
        type for which no ``title`` parameter is passed at instantiation time.
        '''

        return QCoreApplication.translate('BetseeException', 'Horrible Error')

# ....................{ EXCEPTIONS ~ general               }....................
class BetseeCacheException(BetseeException):
    '''
    General-purpose exception applicable to user-specific caching, including
    dynamic generation of pure-Python modules imported at runtime.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate('BetseeCacheException', 'Cache Error')


class BetseeLibException(BetseeException):
    '''
    General-purpose exception applicable to all optional and mandatory
    third-party dependencies, including :mod:`PySide2`.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideException', 'Dependency Error')


class BetseeSimConfException(BetseeException):
    '''
    General-purpose exception applicable to simulation configuration state
    handling (e.g., whether a simulation configuration is currently open).
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseeSimConfException', 'Simulation Configuration Error')

# ....................{ EXCEPTIONS ~ psd                   }....................
class BetseePySideException(BetseeLibException):
    '''
    General-purpose exception applicable to :mod:`PySide2`, this application's
    principal third-party dependency.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideException', 'PySide2 Error')


class BetseePySideClipboardException(BetseePySideException):
    '''
    General-purpose exception applicable to all interaction with the
    platform-specific system clipboard.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideClipboardException', 'Clipboard Error'),


class BetseePySideFocusException(BetseePySideException):
    '''
    General-purpose exception applicable to all handling of interactive keyboard
    input focus for widgets.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideFocusException', 'Widget Focus Error')

# ....................{ EXCEPTIONS ~ psd : thread          }....................
class BetseePySideThreadException(BetseePySideException):
    '''
    :class:`PySide2.QtCore.QThread`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideThreadException', 'Thread Error'),

# ....................{ EXCEPTIONS ~ psd : thread : worker }....................
class BetseePySideThreadWorkerException(BetseePySideThreadException):
    '''
    Multithreaded worker object-specific exception, where "worker" implies any
    :class:`QObject`- or :class:`QRunnable`-derived object isolated in whole or
    part to a secondary application thread.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideThreadWorkerException', 'Thread Worker Error'),


class BetseePySideThreadWorkerStopException(BetseePySideThreadWorkerException):
    '''
    Multithreaded worker object-specific exception internally raised by the
    ``_halt_work_if_requested`` methods and caught by the ``start`` methods
    defined on these objects.

    This exception is intended exclusively for private use by the aforementioned
    methods as a crude (albeit sufficient) means of facilitating
    superclass-subclass intercommunication.
    '''

    pass

# ....................{ EXCEPTIONS ~ psd : widget          }....................
class BetseePySideWidgetException(BetseePySideException):
    '''
    General-purpose exception applicable to :mod:`PySide2` widgets.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideWidgetException', 'Widget Error')


class BetseePySideMenuException(BetseePySideWidgetException):
    '''
    :class:`PySide2.QtWidgets.QMenu`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideMenuException', 'Menu Error')


class BetseePySideMessageBoxException(BetseePySideWidgetException):
    '''
    :class:`PySide2.QtWidgets.QMessageBox`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideMessageBoxException', 'Message Box Error')


class BetseePySideSpinBoxException(BetseePySideWidgetException):
    '''
    General-purpose exception applicable to all concrete
    :class:`PySide2.QtWidgets.QAbstractSpinBox` widgets (e.g.,
    :class:`PySide2.QtWidgets.QDoubleSpinBox` widgets).
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideSpinBoxException', 'Spin Box Error')


class BetseePySideTreeWidgetException(BetseePySideWidgetException):
    '''
    :class:`PySide2.QtWidgets.QTreeWidget`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideTreeWidgetException', 'Tree Widget Error')


class BetseePySideWindowException(BetseePySideWidgetException):
    '''
    :class:`PySide2.QtWidgets.QMainWindow`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideWindowException', 'Window Error')

# ....................{ EXCEPTIONS ~ psd : widget : enum   }....................
#FIXME: Rename to "BetseePySideEnumWidgetException" for orthogonality.
class BetseePySideWidgetEnumException(BetseePySideWidgetException):
    '''
    General-purpose exception applicable to mutually exclusive :mod:`PySide2`
    widgets typically converted to and from lower-level enumeration members.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideWidgetEnumException', 'Enumerable Widget Error')


class BetseePySideComboBoxException(BetseePySideWidgetEnumException):
    '''
    :class:`PySide2.QtWidgets.QComboBox`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideComboBoxException', 'Combo Box Error')


class BetseePySideRadioButtonException(BetseePySideWidgetEnumException):
    '''
    :class:`PySide2.QtWidgets.QRadioButton`-specific exception.
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideRadioButtonException', 'Radio Button Error')

# ....................{ EXCEPTIONS ~ psd : widget : betsee }....................
class BetseePySideEditWidgetException(BetseePySideException):
    '''
    General-purpose exception applicable to application-specific editable
    widgets (i.e., instances of the
    :mod:`betsee.util.widget.abc.guiwdgabc.QBetseeObjectMixin` superclass).
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseePySideEditWidgetException', 'Editable Widget Error')

# ....................{ EXCEPTIONS ~ simmer                }....................
class BetseeSimmerException(BetseePySideException):
    '''
    General-purpose exception applicable to the **simulator** (i.e.,
    :mod:`PySide2`-based object both displaying *and* controlling the execution
    of simulation phases).
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseeSimmerException', 'Simulator Error')


class BetseeSimmerBetseException(BetseeSimmerException):
    '''
    General-purpose exception intended to encapsulate *all* low-level exceptions
    raised by BETSE simulations (e.g., computational instabilities).
    '''

    @property
    def _title_default(self) -> str:
        return QCoreApplication.translate(
            'BetseeSimmerBetseException', 'BETSE Error')
