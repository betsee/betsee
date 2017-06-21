#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Metadata constants synopsizing high-level application behaviour.
'''

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during setuptools-based installation, this
# module may import *ONLY* from modules guaranteed to exist at the start of
# installation. This includes all standard Python and application modules but
# *NOT* third-party dependencies, which if currently uninstalled will only be
# installed at some later time in installation.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import sys

# ....................{ METADATA                           }....................
NAME = 'BETSEE'
'''
Human-readable application name.
'''


LICENSE = '2-clause BSD'
'''
Human-readable name of the license this application is licensed under.
'''

# ....................{ PYTHON ~ version                   }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this section *MUST* be synchronized with:
# * The corresponding section of the "betsee.metadata" submodule.
# * Front-facing documentation (e.g., "README.rst", "doc/md/INSTALL.md").
# On bumping the minimum required version of Python, consider also documenting
# the justification for doing so in the "Python Version" section of this
# submodule's docstring above.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

PYTHON_VERSION_MIN = '3.4.0'
'''
Human-readable minimum version of Python required by this application as a
``.``-delimited string.
'''


def _convert_version_str_to_tuple(version_str: str) -> tuple:
    '''
    Convert the passed human-readable ``.``-delimited version string into a
    machine-readable version tuple of corresponding integers.
    '''
    assert isinstance(version_str, str), (
        '"{}" not a version string.'.format(version_str))

    return tuple(
        int(version_part) for version_part in version_str.split('.'))


PYTHON_VERSION_MIN_PARTS = _convert_version_str_to_tuple(PYTHON_VERSION_MIN)
'''
Machine-readable minimum version of Python required by this application as a
tuple of integers.
'''


# Validate the version of the active Python interpreter *BEFORE* subsequent code
# possibly depending on such version. Since such version should be validated
# both at setuptools-based install time and post-install runtime *AND* since
# this module is imported sufficiently early by both, stash such validation here
# to avoid duplication of such logic and hence the hardcoded Python version.
#
# The "sys" module exposes three version-related constants for this purpose:
#
# * "hexversion", an integer intended to be specified in an obscure (albeit
#   both efficient and dependable) hexadecimal format: e.g.,
#    >>> sys.hexversion
#    33883376
#    >>> '%x' % sys.hexversion
#    '20504f0'
# * "version", a human-readable string: e.g.,
#    >>> sys.version
#    2.5.2 (r252:60911, Jul 31 2008, 17:28:52)
#    [GCC 4.2.3 (Ubuntu 4.2.3-2ubuntu7)]
# * "version_info", a tuple of three or more integers *OR* strings: e.g.,
#    >>> sys.version_info
#    (2, 5, 2, 'final', 0)
#
# For sanity, this application will *NEVER* conditionally depend upon the
# string-formatted release type of the current Python version exposed via the
# fourth element of the "version_info" tuple. Since the first three elements of
# that tuple are guaranteed to be integers *AND* since a comparable 3-tuple of
# integers is declared above, comparing the former and latter yield the simplest
# and most reliable Python version test.
#
# Note that the nearly decade-old and officially accepted PEP 345 proposed a new
# field "requires_python" configured via a key-value pair passed to the call to
# setup() in "setup.py" (e.g., "requires_python = ['>=2.2.1'],"), that field has
# yet to be integrated into either disutils or setuputils. Hence, that field is
# validated manually in the typical way. Behead the infidel setuptools!
if sys.version_info[:3] < PYTHON_VERSION_MIN_PARTS:
    # Human-readable current version of Python. "sys.version" is sufficiently
    # overly verbose as to be unusuable, sadly.
    PYTHON_VERSION = '.'.join(
        str(version_part) for version_part in sys.version_info[:3])

    # Die ignominiously.
    raise RuntimeError(
        '{} requires at least Python {}, but the active Python interpreter '
        'is only Python {}. We feel deep sadness for you.'.format(
            NAME, PYTHON_VERSION_MIN, PYTHON_VERSION))

# ....................{ METADATA ~ version                 }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: When modifying the current version of this application below,
# consider adhering to the Semantic Versioning schema. Specifically, the version
# should consist of three "."-delimited integers "{major}.{minor}.{patch}",
# where:
#
# * "{major}" specifies the major version, incremented only when either:
#   * Breaking configuration file backward compatibility. Since this
#     application's public API is its configuration file format rather than a
#     subset of the code itself (e.g., public subpackages, submodules, classes),
#     no change to the code itself can be considered to break backward
#     compatibility unless that change breaks the configuration file format.
#   * Implementing headline-worthy functionality (e.g., a GUI). Technically,
#     this condition breaks the Semantic Versioning schema, which stipulates
#     that *ONLY* changes breaking backward compatibility warrant major bumps.
#     But this is the real world. In the real world, significant improvements
#     are rewarded with significant version changes.
#   In either case, the minor and patch versions both reset to 0.
# * "{minor}" specifies the minor version, incremented only when implementing
#   customary functionality in a manner preserving such compatibility. In this
#   case, the patch version resets to 0.
# * "{patch}" specifies the patch version, incremented only when correcting
#   outstanding issues in a manner preserving such compatibility.
#
# When in doubt, increment only the minor version and reset the patch version.
# For further details, see http://semver.org.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

VERSION = '0.0.1'
'''
Human-readable application version as a ``.``-delimited string.
'''


VERSION_PARTS = _convert_version_str_to_tuple(VERSION)
'''
Machine-readable application version as a tuple of integers.
'''

# ....................{ METADATA ~ synopsis                }....................
# Note that a human-readable multiline description is exposed via the top-level
# "setup.py" script. This description is inefficiently culled from the contents
# of the top-level "README.rst" file and hence omitted here. (Doing so here
# would significantly increase program startup costs with little to no benefit.)
SYNOPSIS = 'BETSEE, the Bioelectric Tissue Simulation Engine Environment.'
'''
Human-readable single-line synopsis of this application.

By PyPI design, this string must *not* span multiple lines or paragraphs.
'''


DESCRIPTION = (
    'The Bioelectric Tissue Simulation Engine Environment (BETSEE) is the '
    'official Qt 5-based graphical user interface (GUI) for BETSE, a '
    'finite volume simulator for 2D computational multiphysics problems in '
    'the life sciences -- including electrodiffusion, electro-osmosis, '
    'galvanotaxis, voltage-gated ion channels, gene regulatory networks, '
    'and biochemical reaction networks.'
)
'''
Human-readable multiline description of this application.

By :mod:`argparse` design, this string may (and typically should) span both
multiple lines and paragraphs. Note that this string is *not* published to PyPI,
which accepts reStructuredText (rst) and is thus passed the contents of the
top-level :doc:`/README` file instead.
'''

# ....................{ METADATA ~ authors                 }....................
AUTHORS = 'Alexis Pietak, Cecil Curry, et al.'
'''
Human-readable list of all principal authors of this application as a
comma-delimited string.

For brevity, this string *only* lists authors explicitly assigned copyrights.
For the list of all contributors regardless of copyright assignment or
attribution, see the top-level `AUTHORS.md` file.
'''


AUTHOR_EMAIL = 'leycec@gmail.com'
'''
Email address of the principal corresponding author (i.e., the principal author
responding to public correspondence).
'''

# ....................{ METADATA ~ urls                    }....................
URL_HOMEPAGE = 'https://gitlab.com/betse/betsee'
'''
URL of this application's homepage.
'''


URL_DOWNLOAD = (
    'https://gitlab.com/betse/betsee/repository/archive.tar.gz?ref=v{}'.format(
        VERSION,
    )
)
'''
URL of the source tarball for the current version of this application.

This URL assumes a tag whose name is ``v{VERSION}`` where ``{VERSION}`` is the
human-readable current version of this application (e.g., ``v0.4.0``) to exist.
Typically, no such tag exists for live versions of this application -- which
have yet to be stabilized and hence tagged. Hence, this URL is typically valid
*only* for previously released (rather than live) versions of this application.
'''

# ....................{ METADATA ~ python                  }....................
PACKAGE_NAME = NAME.lower()
'''
Fully-qualified name of the top-level Python package implementing this
application.
'''


SCRIPT_BASENAME = PACKAGE_NAME
'''
Basename of the CLI-specific Python script wrapper created by :mod:`setuptools`
installation.
'''

# ....................{ METADATA ~ python : main window    }....................
MAIN_WINDOW_QRC_MODULE_NAME = PACKAGE_NAME + '_rc'
'''
Fully-qualified name of the top-level Python package implementing this
this application's main window Qt resource collection (QRC) converted from the
corresponding XML-formatted UI file exported by the external Qt Designer GUI.

This module is dynamically generated at runtime and hence may *not* yet exist,
in which case the caller is assumed to safely generate this module before its
first importation.
'''


MAIN_WINDOW_UI_MODULE_NAME = PACKAGE_NAME + '_ui'
'''
Fully-qualified name of the top-level Python package implementing this
this application's main window user interface (UI) converted from the
corresponding XML-formatted UI file exported by the external Qt Designer GUI.

This module is dynamically generated at runtime and hence may *not* yet exist,
in which case the caller is assumed to safely generate this module before its
first importation.
'''

# ....................{ METADATA ~ libs                    }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this subsection *MUST* be synchronized with:
# * Front-facing documentation (e.g., "doc/md/INSTALL.md").
# * The "betse.util.type.modules.DISTUTILS_PROJECT_NAME_TO_MODULE_NAME"
#   dictionary, converting between the setuptools-specific names listed below
#   and the Python-specific module names imported by this application.
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

BETSE_VERSION_REQUIRED_MIN = '0.5.1'
'''
Minimum version of BETSE, the low-level CLI underlying this high-level GUI,
required by this application as a human-readable ``.``-delimited string.

Whereas all other minimum versions of third-party dependencies required by this
application are specified as key-value pairs of various dictionary globals of
this submodule, this minimum version is specified as an independent global --
simplifying inspection and validation of this version elsewhere (e.g., in the
:func:`betsee.__main__.die_unless_betse` function).
'''


# DEPENDENCIES_RUNTIME_MANDATORY_VERSIONED = {
#     # Versioned dependencies directly required by this application.
#     'BETSE': '>= ' + BETSE_VERSION_REQUIRED_MIN,
#     'PySide2': '>= 2.0.0~alpha0',
# }
# '''
# Dictionary mapping from the :mod:`setuptools`-specific project name of each
# mandatory runtime dependency of this application that is versioned (i.e.,
# mandatory runtime dependency whose top-level module declares a PEP 8-compliant
# ``__version__`` attribute) to the suffix of a :mod:`setuptools`-specific
# requirements string constraining this dependency.
#
# This dictionary is intentionally isolated from the
# :data:`DEPENDENCIES_RUNTIME_MANDATORY` dictionary, which also contains
# unversioned mandatory runtime dependencies. Since :mod:`setuptools` requires all
# dependencies,
#
# See Also
# ----------
# :data:`betse.metadata.DEPENDENCIES_RUNTIME_MANDATORY`
#     Further details on dictionary structure.
# :download:`/doc/rst/INSTALL.rst`
#     Human-readable list of these dependencies.
# '''


DEPENDENCIES_RUNTIME_MANDATORY = {
    # Versioned dependencies directly required by this application.
    'BETSE': '>= ' + BETSE_VERSION_REQUIRED_MIN,
    'PySide2': '>= 2.0.0~alpha0',

    #FIXME: "pyside2uic" currently emits suboptimal code for SVG icons,
    #internally converting them in memory into non-vector raster icons before
    #display rather than simply displaying them as vector icons. For example,
    #the QIcon created from the "lock_fill.svg" icon is as follows:
    #
    #    icon = QtGui.QIcon()
    #    icon.addPixmap(QtGui.QPixmap("://icon/open_iconic/lock_fill.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    #
    #This code should instead resemble:
    #
    #    icon = QtGui.QIcon()
    #    icon.addFile("://icon/open_iconic/lock_fill.svg", QtGui.QIcon.Normal, QtGui.QIcon.Off)
    #
    #Indeed, there doesn't appear to be any benefit to *EVER* calling the
    #icon.addPixmap() method versus the icon.addFile() method here. The latter
    #method suffices for all supported filetypes and hence is always preferable,
    #regardless of icon filetype.
    #
    #Consider filing an upstream PySide2 issue documenting this, ideally with a
    #minimal UI file as an example.

    # Unversioned dependencies directly required by this application. Since
    # the modules providing these dependencies define no PEP-8-compliant
    # "__version__" or "__version_info__" attributes. merely validating these
    # modules to be importable is the most we can do.
    'PySide2.QtSvg': '',

    #FIXME: Add a minimum required version *AFTER* upstream resolves the
    #following open issue:
    #    https://bugreports.qt.io/browse/PYSIDE-517
    'pyside2uic': '',
}
'''
Dictionary mapping from the :mod:`setuptools`-specific project name of each
mandatory runtime dependency for this application to the suffix of a
:mod:`setuptools`-specific requirements string constraining this dependency.

See Also
----------
:data:`betse.metadata.DEPENDENCIES_RUNTIME_MANDATORY`
    Further details on dictionary structure.
:download:`/doc/rst/INSTALL.rst`
    Human-readable list of these dependencies.
'''

# DEPENDENCIES_RUNTIME_MANDATORY.update(DEPENDENCIES_RUNTIME_MANDATORY_VERSIONED)


DEPENDENCIES_RUNTIME_OPTIONAL = {
    # To simplify subsequent lookup at runtime, project names for optional
    # dependencies should be *STRICTLY LOWERCASE*. Since setuptools parses
    # project names case-insensitively, case is only of internal relevance.
}
'''
Dictionary mapping from the :mod:`setuptools`-specific project name of each
optional runtime dependency for this application to the suffix of a
:mod:`setuptools`-specific requirements string constraining this dependency.

See Also
----------
:data:`betse.metadata.DEPENDENCIES_RUNTIME_MANDATORY`
    Further details on dictionary structure.
:download:`/doc/rst/INSTALL.rst`
    Human-readable list of these dependencies.
'''


DEPENDENCIES_TESTING_MANDATORY = {
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
:data:`betse.metadata.DEPENDENCIES_RUNTIME_MANDATORY`
    Further details on dictionary structure.
:download:`/doc/rst/INSTALL.rst`
    Human-readable list of these dependencies.
'''

# ....................{ METADATA ~ private                 }....................
_IS_TESTING = False
'''
``True`` only if the active Python interpreter is running a test session (e.g.,
with the ``py.test`` test harness).

This private global is subject to change and thus *not* intended to be publicly
accessed. Consider calling the public :func:`betse.util.py.pys.is_testing`
function instead.
'''
