#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Metadata constants synopsizing high-level application dependencies.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during setuptools-based installation, this
# module may import *ONLY* from modules guaranteed to exist at the start of
# installation. This includes all standard Python and application modules but
# *NOT* third-party dependencies, which if currently uninstalled will only be
# installed at some later time in the installation.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ LIBS ~ runtime : mandatory         }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this subsection *MUST* be synchronized with:
# * Front-facing documentation (e.g., "doc/md/INSTALL.md").
# * The "betse.util.type.modules.DISTUTILS_PROJECT_NAME_TO_MODULE_NAME"
#   dictionary, converting between the setuptools-specific names listed below
#   and the Python-specific module names imported by this application.
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

BETSE_VERSION_REQUIRED_MIN = '0.8.1'
'''
Minimum version of BETSE, the low-level CLI underlying this high-level GUI,
required by this application as a human-readable ``.``-delimited string.

Whereas all other minimum versions of third-party dependencies required by this
application are specified as key-value pairs of various dictionary globals of
this submodule, this minimum version is specified as an independent global --
simplifying inspection and validation of this version elsewhere (e.g., in the
:func:`betsee.__main__.die_unless_betse` function).
'''


RUNTIME_MANDATORY = {
    # Versioned dependencies directly required by this application.
    'BETSE': '>= ' + BETSE_VERSION_REQUIRED_MIN,
    'PySide2': '>= 2.0.0~alpha0',

    # Unversioned dependencies directly required by this application. Since
    # the modules providing these dependencies define no PEP-8-compliant
    # "__version__" or "__version_info__" attributes. merely validating these
    # modules to be importable is the most we can do.
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

# ....................{ LIBS ~ runtime : optional          }....................
#FIXME: Should these dependencies also be added to our "setup.py" metadata,
#perhaps as so-called "extras"? Contemplate. Consider. Devise.
RUNTIME_OPTIONAL = {
    # To simplify subsequent lookup at runtime, project names for optional
    # dependencies should be *STRICTLY LOWERCASE*. Since setuptools parses
    # project names case-insensitively, case is only of internal relevance.

    #FIXME: Add a minimum required version *AFTER* upstream resolves the
    #following open issue:
    #    https://bugreports.qt.io/browse/PYSIDE-517
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

# ....................{ LIBS ~ testing : mandatory         }....................
TESTING_MANDATORY = {
    # For simplicity, py.test should remain the only hard dependency for testing
    # on local machines. While our setuptools-driven testing regime optionally
    # leverages third-party py.test plugins (e.g., "pytest-xdist"), these
    # plugins are *NOT* required for simple testing.
    'pytest': '>= 2.5.0',
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

# ....................{ GETTERS                            }....................
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

        #FIXME: Uncomment the following line and remove the line that follows
        #that *AFTER* "PySide2" and "pyside2-tools" become available on PyPI.
        #Ideally, only "PySide2."-prefixed components should be ignored.

        # If this is *NOT* a PySide2-specific submodule...
        #if not dependency_name.startswith('PySide2.')
        if not dependency_name.startswith(('PySide2', 'pyside2'))
    }

    # Return this dictionary converted into a tuple.
    return guisetuptool.convert_requirements_dict_to_tuple(
        runtime_mandatory_sans_submodules)


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
