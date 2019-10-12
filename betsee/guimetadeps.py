#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
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
# This is externally referenced by the top-level "setup.py" and hence public.
SETUPTOOLS_VERSION_MIN = '38.2.0'
'''
Minimum version of :mod:`setuptools` required at application installation time
as a human-readable ``.``-delimited string.

Motivation
----------
This application requires :mod:`PySide2`, which is distributed as a wheel and
thus requires wheel support, which in turns requires either ``pip`` >= 1.4.0 or
:mod:`setuptools` >= 38.2.0. While ``pip`` 1.4.0 is relatively ancient,
:mod:`setuptools` 38.2.0 is comparatively newer. If the current version of
:mod:`setuptools` is *not* explicitly validated at installation time, older
:mod:`setuptools` versions fail on attempting to install :mod:`PySide2` with
non-human-readable fatal errors resembling:

    $ sudo python3 setup.py develop
    running develop
    running egg_info
    writing betsee.egg-info/PKG-INFO
    writing dependency_links to betsee.egg-info/dependency_links.txt
    writing entry points to betsee.egg-info/entry_points.txt
    writing requirements to betsee.egg-info/requires.txt
    writing top-level names to betsee.egg-info/top_level.txt
    reading manifest template 'MANIFEST.in'
    writing manifest file 'betsee.egg-info/SOURCES.txt'
    running build_ext
    Creating /usr/lib64/python3.6/site-packages/betsee.egg-link (link to .)
    Saving /usr/lib64/python3.6/site-packages/easy-install.pth
    Installing betsee script to /usr/bin
    changing mode of /usr/bin/betsee to 755

    Installed /home/leycec/py/betsee
    Processing dependencies for betsee==0.9.2.0
    Searching for PySide2
    Reading https://pypi.python.org/simple/PySide2/
    No local packages or working download links found for PySide2
    error: Could not find suitable distribution for Requirement.parse('PySide2')
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
    # Each version of BETSEE strictly requires the same version of BETSE
    # excluding the trailing patch number of the former (e.g., BETSEE 0.8.1.1
    # and 0.8.1.0 both strictly require BETSE 0.8.1). Since newer versions of
    # BETSE typically break backward compatibility with older versions of
    # BETSEE, this dependency does *NOT* extend to newer versions of BETSE.
    'BETSE': '== ' + BETSE_VERSION,

    #FIXME: Convert this into a versioned dependency once the Qt Company
    #releases an official PySide2 release supported under all requisite
    #platforms (e.g., conda-forge, Gentoo). Until then, this suffices.

    'PySide2': '',
    # 'PySide2': '>= 5.12.3',  # First official stable release of PySide2.

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

# ....................{ LIBS ~ runtime : optional         }....................
#FIXME: Should these dependencies also be added to our "setup.py" metadata,
#perhaps as so-called "extras"? Contemplate. Consider. Devise.
RUNTIME_OPTIONAL = {
    # To simplify subsequent lookup at runtime, project names for optional
    # dependencies should be *STRICTLY LOWERCASE*. Since setuptools parses
    # project names case-insensitively, case is only of internal relevance.

    #FIXME: Add a minimum required version *AFTER* upstream resolves the
    #following open issue:
    #    https://bugreports.qt.io/browse/PYSIDE-517
    #FIXME: The official "PySide2" wheel now ships "pyside2uic" out-of-the-box,
    #suggesting this should now resemble:
    #    'pyside2uic': RUNTIME_MANDATORY['PySide2'],
    #Test the above specification when time admits (i.e., sadly never).
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

        # If this is neither a PySide2-specific submodule nor the "pyside2uic"
        # subpackage, which official PySide2 wheels now bundle out-of-the-box
        # and hence are *NOT* externally available from PyPI...
        if not dependency_name.startswith(('PySide2.', 'pyside2uic'))
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

    # Return this dictionary converted into a tuple.
    return guisetuptool.convert_requirements_dict_to_tuple(RUNTIME_OPTIONAL)


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
