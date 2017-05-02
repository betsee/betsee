#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2014-2017 by Alexis Pietak & Cecil Curry.
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
# installed at some later time in the installation.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ....................{ METADATA                           }....................
NAME = 'BETSEE'
'''
Human-readable application name.
'''


LICENSE = '2-clause BSD'
'''
Human-readable name of the license this application is licensed under.
'''

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


#FIXME: Reuse the existing betse.metadata._get_version_parts_from_str()
#function, which should presumably then be publicized. To do so safely, we'll
#want to guarantee that the "betse" package is importable *BEFORE* this
#submodule is ever imported in this codebase.
def _get_version_parts_from_str(version_str: str) -> tuple:
    '''
    Convert the passed human-readable ``.``-delimited version string into a
    machine-readable version tuple of corresponding integers.
    '''
    assert isinstance(version_str, str), (
        '"{}" not a version string.'.format(version_str))

    return tuple(
        int(version_part) for version_part in version_str.split('.'))


VERSION_PARTS = _get_version_parts_from_str(VERSION)
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

# ....................{ METADATA ~ libs : runtime          }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this dictionary *MUST* be synchronized with:
# * Front-facing documentation (e.g., "doc/md/INSTALL.md").
# * The "betse.util.py.modules.SETUPTOOLS_TO_MODULE_NAME" dictionary, converting
#   between the setuptools-specific names listed below and the Python-specific
#   module names imported by this application.
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEPENDENCIES_RUNTIME_MANDATORY = {
    # Dependencies directly required by this application.
    'BETSE': '>= 0.5.0',
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


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this dictionary *MUST* be synchronized with:
# * Front-facing documentation (e.g., "doc/md/INSTALL.md").
# * The "betse.util.py.modules.SETUPTOOLS_TO_MODULE_NAME" dictionary. See above.
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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

# ....................{ METADATA ~ libs : testing          }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this dictionary *MUST* be synchronized with:
# * Front-facing documentation (e.g., the top-level "README.rst").
# * The "betse.util.py.modules.SETUPTOOLS_TO_MODULE_NAME" dictionary. See above.
# * Gitlab-CI configuration (e.g., the top-level "requirements-conda.txt" file).
# * Third-party platform-specific packages (e.g., Gentoo Linux ebuilds).
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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
