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

from betse.appmeta import BetseAppMeta
from betse.util.path import dirs, files, pathnames
from betse.util.type.decorator.decmemo import property_cached
from betse.util.type.types import type_check, ModuleType
from betsee import guimetadata
from betsee.lib.pyside2.cache.guipsdcache import CachePolicy

# ....................{ SUBCLASSES                        }....................
class BetseeAppMeta(BetseAppMeta):
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

    # ..................{ SUPERCLASS ~ properties           }..................
    @property
    def _module_metadata(self) -> ModuleType:
        return guimetadata


    @property
    def _module_metadeps(self) -> ModuleType:
        '''
        **Application-wide dependency metadata submodule** (i.e., submodule
        publishing lists of version-pinned dependencies as global constants
        synopsizing all requirements of the current application).

        Design
        ----------
        This property dynamically creates and returns a new in-memory submodule
        that does *not* physically exist on-disk. Rather, this high-level
        submodule merges *all* dependency metadata defined by lower-level
        submodules that do actually exist on-disk. This means:

        * BETSE's :mod:`betse.metadeps` submodule.
        * BETSEE's :mod:`betsee.guimetadeps` submodule.

        This submodule satisfies all requirements of both BETSE and BETSEE,
        thus safeguarding usage of the :mod:`betse.lib.libs` API -- notably
        calls to the :func:`betse.lib.libs.import_runtime_optional` function
        distributed throughout the BETSE and BETSEE codebases, regardless of
        the codebase in which they reside.

        See Also
        ----------
        :meth:`module_metadeps`
            Concrete public property validating the module returned by this
            abstract private property to expose the expected attributes.
        '''

        # Isolate method-specific imports for maintainability.
        from betse import metadeps as betse_metadeps
        from betse.util.app.meta import appmetamod
        from betsee import guimetadeps as betsee_metadeps

        # Application dependency metadata module merging the BETSE and BETSEE
        # application dependency metadata modules.
        module_metadeps_merged = appmetamod.merge_module_metadeps(
            # Fully-qualified name of the module to be created. For simplicity,
            # prefer a guaranteeably unique submodule of the top-level "betsee"
            # package, which is guaranteed to exist.
            module_name='betsee.__betse_plus_betsee_metadeps__',
            modules_metadeps=(betse_metadeps, betsee_metadeps,),
        )

        # Return this module.
        return module_metadeps_merged

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
