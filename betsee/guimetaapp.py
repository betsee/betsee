#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2014-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
High-level **application metadata singleton** (i.e., application-wide object
synopsizing application metadata via read-only properties).
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: This subclass must *NOT* be accessed from the top-level "setup.py"
# script of this or any other application. This application and hence this
# subclass is *NOT* guaranteed to exist at setuptools-based installation-time
# for downstream consumers (e.g., BETSEE).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from betse.metaapp import BetseMetaApp
from betse.util.path import dirs, files, pathnames
from betse.util.type.decorator.decmemo import property_cached
from betse.util.type.types import type_check
from betsee import guimetadata
from betsee.lib.pyside2.cache.guipsdcache import CachePolicy

# ....................{ SUBCLASSES                        }....................
class BetseeMetaApp(BetseMetaApp):
    '''
    **Application metadata singleton** (i.e., application-wide object
    synopsizing application metadata via read-only properties) subclass.

    Caveats
    ----------
    **This subclass must not be accessed from the top-level ``setup.py`` script
    of this or any other application.** This application and hence this
    subclass is *not* guaranteed to exist at setuptools-based installation-time
    for downstream consumers (e.g., BETSEE).

    See Also
    ----------
    :mod:`betsee.util.path.guipathsys`
        Collection of the absolute paths of numerous core files and
        directories describing the structure of the local filesystem.
    '''

    # ..................{ INITIALIZERS                      }..................
    def init_sans_libs(self) -> None:
        '''
        Initialize this application *except* mandatory third-party dependencies
        of this application, which requires external resources (e.g.,
        command-line options, configuration files) to have been parsed.

        Specifically, this method (in order):

        #. Initializes BETSE itself by calling the superclass method.
        #. Validates but does *not* initialize all mandatory third-party
           dependencies of this application, which the :meth:`init_libs` method
           does so subsequently.
        #. Validates the active Python interpreter to support multithreading.
        '''

        # Avoid circular import dependencies.
        from betsee.lib import guilib

        # Initialize our superclass and hence BETSE itself.
        super().init_sans_libs()

        # Validate mandatory dependencies *AFTER* initializing BETSE.
        #
        # These dependencies are intentionally *NOT* initialized here (e.g., by
        # calling guilib.init()), as doing so requires the logging
        # configuration to have been finalized (e.g., by parsing CLI options),
        # which has yet to occur this early in the application lifecycle.
        guilib.die_unless_runtime_mandatory_all()


    @type_check
    def init_libs(self, cache_policy: CachePolicy) -> None:
        '''
        Initialize all mandatory runtime dependencies of this application with
        sane defaults, including those required by both BETSE *and* BETSEE.

        Parameters
        ----------
        cache_policy : CachePolicy
            Type of :mod:`PySide2`-based submodule caching to be performed.
        '''

        # Defer heavyweight imports.
        from betsee.lib.pyside2 import guipsd
        from betsee.util.app import guiapp

        # Instantiate the "QApplication" singleton *BEFORE* initializing BETSE
        # dependencies. Our reasoning is subtle, but vital: initializing BETSE
        # initializes matplotlib with the "Qt5Agg" backend, which instantiates
        # the "QApplication" singleton if this singleton has *NOT* already been
        # initialized. However, various application-wide settings (e.g.,
        # metadata, high-DPI scaling emulation) *MUST* be initialized before
        # this singleton is instantiated. Permitting "Qt5Agg" to instantiate
        # this singleton first prevents us from initializing these settings
        # here. This singleton *MUST* thus be instantiated by us first.
        guiapp.init()

        # Initialize PySide2 *AFTER* instantiating the "QApplication"
        # singleton, as PySide2 will implicitly instantiate its own such
        # singleton if we fail to explicitly do so first.
        guipsd.init(cache_policy=cache_policy)

        # Initialize our superclass dependencies (and hence those required by
        # BETSE itself) to strictly require a Qt 5-specific matplotlib backend
        # *AFTER* initializing PySide2 .
        super().init_libs(matplotlib_backend_name='Qt5Agg')

    # ..................{ PROPERTIES ~ dir : data           }..................
    @property_cached
    def data_py_dirname(self) -> str:
        '''
        Absolute dirname of this application's data subdirectory containing
        pure-Python modules and packages generated at runtime by this
        application if found *or* raise an exception otherwise (i.e., if this
        directory is *not* found).
        '''

        # Create this directory if needed and return its dirname.
        return dirs.join_or_die(self.data_dirname, 'py')


    @property_cached
    def data_qrc_dirname(self) -> str:
        '''
        Absolute dirname of this application's data subdirectory containing
        XML-formatted Qt resource collection (QRC) files exported by the
        external Qt Designer application and all binary resource files listed
        in these files if found *or* raise an exception otherwise (i.e., if
        this directory is *not* found).
        '''

        # Return this dirname if this directory exists or raise an exception.
        return dirs.join_or_die(self.data_dirname, 'qrc')


    @property_cached
    def data_ui_dirname(self) -> str:
        '''
        Absolute dirname of this application's data subdirectory containing
        XML-formatted user interface (UI) files exported by the external Qt
        Designer application if found *or* raise an exception otherwise (i.e.,
        if this directory is *not* found).
        '''

        # Return this dirname if this directory exists or raise an exception.
        return dirs.join_or_die(self.data_dirname, 'ui')

    # ..................{ PROPERTIES ~ dir : dot            }..................
    @property_cached
    def dot_py_dirname(self) -> str:
        '''
        Absolute dirname of this application's dot subdirectory containing
        pure-Python modules and packages generated at runtime by this
        application if found *or* raise an exception otherwise (i.e., if this
        directory is *not* found).
        '''

        # Create this directory if needed and return its dirname.
        return dirs.join_and_make_unless_dir(self.dot_dirname, 'py')

    # ..................{ PROPERTIES ~ file : data          }..................
    @property_cached
    def data_qrc_filename(self) -> str:
        '''
        Absolute filename of the XML-formatted Qt resource collection (QRC)
        file exported by the external Qt Designer application structuring all
        external resources (e.g., icons) required by this application's main
        window if found *or* raise an exception otherwise (i.e., if this file
        is *not* found).
        '''

        # Return this filename if this file exists or raise an exception.
        #
        # Note that this basename *MUST* be the same as that specified by the
        # "resources" attribute of all XML tags contained in the file whose
        # path is given by the get_data_ui_filename() function. Why? Because
        # obfuscatory Qt.
        return files.join_or_die(
            self.data_qrc_dirname, self.package_name + '.qrc')


    @property_cached
    def data_ui_filename(self) -> str:
        '''
        Absolute filename of the XML-formatted user interface (UI) file
        exported by the external Qt Designer application structuring this
        application's main window if found *or* raise an exception otherwise
        (i.e., if this file is *not* found).
        '''

        # Return this filename if this file exists or raise an exception.
        return files.join_or_die(
            self.data_ui_dirname, self.package_name + '.ui')

    # ..................{ PROPERTIES ~ file : data : py     }..................
    @property_cached
    def data_py_qrc_filename(self) -> str:
        '''
        Absolute filename of the pure-Python application-wide module generated
        from the XML-formatted Qt resource collection (QRC) file exported by
        the external Qt Designer application structuring all external resources
        (e.g., icons) required by this application's main window.

        If this module exists, this module is guaranteed to be importable but
        *not* necessarily up-to-date with the input paths from which this
        module is dynamically regenerated at runtime; else, the caller is
        assumed to explicitly regenerate this module.

        See Also
        ----------
        :meth:`dot_py_qrc_filename`
            User-specific equivalent of this file.
        :mod:`betsee.lib.pyside2.cache.guipsdcache`
            Submodule dynamically generating this module.
        '''

        # Note that this basename *MUST* be:
        #
        # * Prefixed by the same basename excluding filetype returned by the
        #   get_data_qrc_filename() function.
        # * Suffixed by "_rc.py". Why? Because the Python code generated at
        #   runtime by the "pyside2uic" package assumes this to be the case.
        #   Naturally, this assumption is *NOT* configurable.
        return pathnames.join(
            self.data_py_dirname,
            guimetadata.MAIN_WINDOW_QRC_MODULE_NAME + '.py')


    @property_cached
    def data_py_ui_filename(self) -> str:
        '''
        Absolute filename of the pure-Python application-wide module generated
        from the XML-formatted user interface (UI) file exported by the
        external Qt Designer application structuring this application's main
        window if found *or* raise an exception otherwise (i.e., if this
        directory is *not* found).

        If this module exists, this module is guaranteed to be importable but
        *not* necessarily up-to-date with the input paths from which this
        module is dynamically regenerated at runtime; else, the caller is
        assumed to explicitly regenerate this module.

        See Also
        ----------
        :meth:`dot_py_ui_filename`
            User-specific equivalent of this file.
        :mod:`betsee.lib.pyside2.cache.guipsdcache`
            Submodule dynamically generating this module.
        '''

        return pathnames.join(
            self.data_py_dirname,
            guimetadata.MAIN_WINDOW_UI_MODULE_NAME + '.py')

    # ..................{ PROPERTIES ~ file : dot : py      }..................
    @property_cached
    def dot_py_qrc_filename(self) -> str:
        '''
        Absolute filename of the pure-Python user-specific module generated
        from the XML-formatted Qt resource collection (QRC) file exported by
        the external Qt Designer application structuring all external resources
        (e.g., icons) required by this application's main window.

        See Also
        ----------
        :meth:`data_py_qrc_filename`
            Application-wide equivalent of this file.
        '''

        return pathnames.join(
            self.dot_py_dirname,
            pathnames.get_basename(self.data_py_qrc_filename))


    @property_cached
    def dot_py_ui_filename(self) -> str:
        '''
        Absolute filename of the pure-Python user-specific module generated
        from the XML-formatted user interface (UI) file exported by the
        external Qt Designer application structuring this application's main
        window if found *or* raise an exception otherwise (i.e., if this
        directory is *not* found).

        See Also
        ----------
        :mod:`betsee.lib.pyside2.cache.guipsdcache`
            Submodule dynamically generating this module.
        '''

        return pathnames.join(
            self.dot_py_dirname,
            pathnames.get_basename(self.data_py_ui_filename))
