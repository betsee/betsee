#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2020 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Metadata constants synopsizing high-level application dependencies.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during setuptools-based installation, this
# module may import *ONLY* from modules guaranteed to exist at the start of
# installation. This includes all standard Python and application modules but
# *NOT* third-party dependencies, which if currently uninstalled will only be
# installed at some later time in the installation.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from betsee.guimetadata import VERSION
from collections import namedtuple

# ....................{ LIBS ~ install : mandatory        }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid dependency conflicts between "pip", "setuptools", BETSE,
# and BETSEE, the value of this global variable *MUST* be synchronized (i.e.,
# copied) across numerous files in both codebases. Specifically, the following
# strings *MUST* be identical:
# * "betse.metadeps.SETUPTOOLS_VERSION_MIN".
# * "betsee.guimetadeps.SETUPTOOLS_VERSION_MIN".
# * The "build-backend" setting in:
#   * "betse/pyproject.toml".
#   * "betsee/pyproject.toml".
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# This public global is externally referenced by "setup.py".
SETUPTOOLS_VERSION_MIN = '38.2.0'
'''
Minimum version of :mod:`setuptools` required at both application install- and
runtime as a human-readable ``.``-delimited string.

See Also
----------
:attr:`betse.metadeps.SETUPTOOLS_VERSION_MIN`
    Further details.
'''

# ....................{ LIBS ~ runtime : mandatory        }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this subsection *MUST* be synchronized with:
# * Front-facing documentation (e.g., "doc/md/INSTALL.md").
# * The "betse.util.type.modules.DISTUTILS_PROJECT_NAME_TO_MODULE_NAME"
#   dictionary, converting between the setuptools-specific names listed below
#   and the Python-specific module names imported by this application.
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# This is externally referenced by "betsee.__main__" and hence public.
#
# See the "Design" section below for commentary.
BETSE_VERSION = VERSION[:VERSION.rindex('.')]
'''
Version of BETSE (i.e., the low-level CLI underlying this high-level GUI)
required by this version of BETSEE as a human-readable ``.``-delimited string.

Design
----------
Whereas all other minimum versions of third-party dependencies required by this
application are specified as key-value pairs of various dictionary globals of
this submodule, this version is specified as an independent global --
simplifying inspection and validation of this version elsewhere (e.g., in the
:func:`betsee.__main__.die_unless_betse` function).

See Also
----------
:data:`betsee.guimetadata.VERSION`
    Further details.
'''


RUNTIME_MANDATORY = {
    # setuptools is currently required at both install and runtime. At runtime,
    # setuptools is used to validate that dependencies are available.
    'setuptools': '>= ' + SETUPTOOLS_VERSION_MIN,

    # Each version of BETSEE strictly requires the same version of BETSE
    # excluding the trailing patch number of the former (e.g., BETSEE 0.8.1.1
    # and 0.8.1.0 both strictly require BETSE 0.8.1). Since newer versions of
    # BETSE typically break backward compatibility with older versions of
    # BETSEE, this dependency does *NOT* extend to newer versions of BETSE.
    'betse': '== ' + BETSE_VERSION,

    # Versioned dependencies directly required by this application.
    # Specifically, this application requires:
    #
    # * PySide2 >= 5.14.0, which removed the requisite "pyside2-uic" and
    #   "pyside2-rcc" commands in favour of the "uic --generate python" and
    #   "rcc --generate python" commands provided by both the optional
    #   "pyside2-tools" dependency and mandatory C++ Qt dependencies. In short,
    #   "pyside2-tools" is mostly no longer required at runtime.
    'PySide2': '>= 5.14.0',

    # Unversioned dependencies directly required by this application. Since
    # the modules providing these dependencies define no PEP-8-compliant
    # "__version__" or "__version_info__" attributes. merely validating these
    # modules to be importable is the most we can do.
    #
    # Note that this is guaranteed to be the case for users installing PySide2
    # from official PyPI-hosted wheels, but *NOT* for users installing PySide2
    # from other sources (e.g., system-wide package managers).
    'PySide2.QtGui': '',
    'PySide2.QtSvg': '',
    'PySide2.QtWidgets': '',
}
'''
Dictionary mapping from the :mod:`setuptools`-specific project name of each
mandatory runtime dependency for this application to the suffix of a
:mod:`setuptools`-specific requirements string constraining this dependency.

See Also
----------
:func:`get_runtime_mandatory_sans_submodules`
    Function returning a copy of this dictionary excluding all :mod:`PySide2`
    submodules (e.g., :mod:`PySide2.QtGui`).
:data:`betse.metadata.RUNTIME_MANDATORY`
    Further details on dictionary structure.
:download:`/doc/rst/INSTALL.rst`
    Human-readable list of these dependencies.
'''

# ....................{ LIBS ~ runtime : optional         }....................
RUNTIME_OPTIONAL = {
    # To simplify subsequent lookup at runtime, project names for optional
    # dependencies should be *STRICTLY LOWERCASE*. Since setuptools parses
    # project names case-insensitively, case is only of internal relevance.

    # Unversioned dependencies directly required by this application. Since
    # the modules providing these dependencies define no PEP-8-compliant
    # "__version__" or "__version_info__" attributes. merely validating these
    # modules to be importable is the most we can do.
    #
    # Note that this is guaranteed to be the case for users installing PySide2
    # from official PyPI-hosted wheels, but *NOT* for users installing PySide2
    # from other sources (e.g., system-wide package managers).

    #FIXME: Add a minimum required version *AFTER* upstream resolves the
    #following open issue: https://bugreports.qt.io/browse/PYSIDE-517
    # Note that the corresponding "uic" command is *NOT* required -- only the
    # pure-Python "pyside2uic" package referenced here.
    'pyside2uic': '',
}
'''
Dictionary mapping from the :mod:`setuptools`-specific project name of each
optional runtime dependency for this application to the suffix of a
:mod:`setuptools`-specific requirements string constraining this dependency.

See Also
----------
:data:`betse.metadata.RUNTIME_MANDATORY`
    Further details on dictionary structure.
:download:`/doc/rst/INSTALL.rst`
    Human-readable list of these dependencies.
'''

# ....................{ LIBS ~ testing : mandatory        }....................
TESTING_MANDATORY = {
    # setuptools is currently required at testing time as well. If ommitted,
    # "tox" commonly fails at venv creation time with exceptions resembling:
    #
    #     GLOB sdist-make: /home/leycec/py/betse/setup.py
    #     py36 inst-nodeps: /home/leycec/py/betse/.tox/.tmp/package/1/betse-1.1.1.zip
    #     ERROR: invocation failed (exit code 1), logfile: /home/leycec/py/betse/.tox/py36/log/py36-3.log
    #     =================================================== log start ===================================================
    #     Processing ./.tox/.tmp/package/1/betse-1.1.1.zip
    #         Complete output from command python setup.py egg_info:
    #         Traceback (most recent call last):
    #           File "<string>", line 1, in <module>
    #           File "/tmp/pip-0j3y5x58-build/setup.py", line 158, in <module>
    #             buputil.die_unless_setuptools_version_at_least(metadeps.SETUPTOOLS_VERSION_MIN)
    #           File "/tmp/pip-0j3y5x58-build/betse_setup/buputil.py", line 74, in die_unless_setuptools_version_at_least
    #             setuptools_version_min, setuptools.__version__))
    #         Exception: setuptools >= 38.2.0 required by this application, but only setuptools 28.8.0 found.
    #
    #         ----------------------------------------
    #     Command "python setup.py egg_info" failed with error code 1 in /tmp/pip-0j3y5x58-build/
    #     You are using pip version 9.0.1, however version 19.3.1 is available.
    #     You should consider upgrading via the 'pip install --upgrade pip' command.
    #
    #     ==================================================== log end ====================================================
    'setuptools': '>= ' + SETUPTOOLS_VERSION_MIN,

    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # WARNING: This py.test requirement *MUST* be manually synchronized to the
    # same requirement in the upstream "betse.metadeps" submodule. Failure to
    # do so will raise exceptions at BETSEE startup.
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    'pytest':      '>= 3.7.0',

    # All subsequent requirements require no such synchronization.
    'pytest-qt':   '>= 3.2.0',
    'pytest-xvfb': '>= 1.2.0',
}
'''
Dictionary mapping from the :mod:`setuptools`-specific project name of each
mandatory testing dependency for this application to the suffix of a
:mod:`setuptools`-specific requirements string constraining this dependency.

See Also
----------
:data:`betse.metadata.RUNTIME_MANDATORY`
    Further details on dictionary structure.
:download:`/doc/rst/INSTALL.rst`
    Human-readable list of these dependencies.
'''

# ....................{ LIBS ~ commands                   }....................
RequirementCommand = namedtuple('RequirementCommand', ('name', 'basename',))
RequirementCommand.__doc__ = '''
    Lightweight metadata describing a single external command required by an
    application dependency of arbitrary type (including optional, mandatory,
    runtime, testing, and otherwise).

    Attributes
    ----------
    name : str
        Human-readable name associated with this command (e.g., ``Graphviz``).
    basename : str
        Basename of this command to be searched for in the current ``${PATH}``.
    '''


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this dictionary *MUST* be synchronized with:
# * Front-facing documentation (e.g., "doc/md/INSTALL.md").
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REQUIREMENT_NAME_TO_COMMANDS = {
    # "pytest-xvfb" requires "Xvfb" to be externally installed.
    'pytest-xvfb': (RequirementCommand(name='Xvfb', basename='Xvfb'),),
}
'''
Dictionary mapping from the :mod:`setuptools`-specific project name of each
application dependency (of any type, including optional, mandatory, runtime,
testing, or otherwise) requiring one or more external commands to a tuple of
:class:`RequirementCommand` instances describing these requirements.

See Also
----------
:download:`/doc/md/INSTALL.md`
    Human-readable list of these dependencies.
'''

# ....................{ GETTERS                           }....................
def get_runtime_mandatory_tuple() -> tuple:
    '''
    Tuple listing the :mod:`setuptools`-specific requirement string containing
    the mandatory name and optional version and extras constraints of each
    mandatory runtime dependency for this application, dynamically converted
    from the :data:`metadata.RUNTIME_MANDATORY` dictionary.

    Caveats
    ----------
    This dictionary notably excludes all submodules whose fully-qualified names
    are prefixed by ``PySide2.`` (e.g., :mod:`PySide2.QtGui`). These submodules
    signify optional :mod:`PySide2` components required by this application but
    unavailable on PyPI. Including these submodules here would erroneously halt
    setuptools-based installation for up to several minutes with output
    resembling:

        Searching for PySide2.QtSvg
        Reading https://pypi.python.org/simple/PySide2.QtSvg/
        Couldn't find index page for 'PySide2.QtSvg' (maybe misspelled?)
        Scanning index of all packages (this may take a while)
        Reading https://pypi.python.org/simple/
    '''

    # Avoid circular import dependencies.
    from betsee.lib.setuptools import guisetuptool

    # Dictionary of all mandatory runtime dependencies excluding submodules.
    runtime_mandatory_sans_submodules = {
        # Map this dependency's name to constraints.
        dependency_name: dependency_constraints

        # For the name and constraints of each mandatory runtime dependency...
        for dependency_name, dependency_constraints in
            RUNTIME_MANDATORY.items()

        # If this is *NOT* a PySide2-specific submodule...
        if not dependency_name.startswith('PySide2.')
    }

    # Return this dictionary converted into a tuple.
    return guisetuptool.convert_requirements_dict_to_tuple(
        runtime_mandatory_sans_submodules)


def get_runtime_optional_tuple() -> tuple:
    '''
    Tuple listing the :mod:`setuptools`-specific requirement string containing
    the mandatory name and optional version and extras constraints of each
    optional runtime dependency for this application, dynamically converted
    from the :data:`metadata.RUNTIME_OPTIONAL` dictionary.
    '''

    # Avoid circular import dependencies.
    from betsee.lib.setuptools import guisetuptool

    # Dictionary of all mandatory runtime dependencies excluding submodules.
    runtime_optional_sans_submodules = {
        # Map this dependency's name to constraints.
        dependency_name: dependency_constraints

        # For the name and constraints of each optional runtime dependency...
        for dependency_name, dependency_constraints in
            RUNTIME_OPTIONAL.items()

        # If this is *NOT* the "pyside2uic" package, which official PySide2
        # wheels now bundle out-of-the-box rather than distributing as a
        # separate PyPI-hosted package. Since this package is *NOT* externally
        # available from PyPI, including this package here would induce fatal
        # install-time errors for users and test-time utilities (e.g., "tox")
        # installing the "all" extra for all optional runtime dependencies.
        if not dependency_name == 'pyside2uic'
    }

    # Return this dictionary converted into a tuple.
    return guisetuptool.convert_requirements_dict_to_tuple(
        runtime_optional_sans_submodules)



def get_testing_mandatory_tuple() -> tuple:
    '''
    Tuple listing the :mod:`setuptools`-specific requirement string containing
    the mandatory name and optional version and extras constraints of each
    mandatory testing dependency for this application, dynamically converted
    from the :data:`metadata.TESTING_MANDATORY` dictionary.
    '''

    # Avoid circular import dependencies.
    from betsee.lib.setuptools import guisetuptool

    # Return this dictionary converted into a tuple.
    return guisetuptool.convert_requirements_dict_to_tuple(TESTING_MANDATORY)
