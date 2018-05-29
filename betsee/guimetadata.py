#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
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


PYTHON_VERSION_MINOR_MAX = 7
'''
Maximum minor stable version of this major version of Python currently released
(e.g., ``5`` if Python 3.5 is the most recent stable version of Python 3.x).
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
VERSION = '0.8.1.0'
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
SYNOPSIS = 'BETSEE, the BioElectric Tissue Simulation Engine Environment.'
'''
Human-readable single-line synopsis of this application.

By PyPI design, this string must *not* span multiple lines or paragraphs.
'''


DESCRIPTION = (
    'The BioElectric Tissue Simulation Engine Environment (BETSEE) is the '
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

# ....................{ METADATA ~ organization            }....................
ORG_NAME = 'Paul Allen Discovery Center'
'''
Human-readable list of the single organization principally responsible for
funding the authors of this application.
'''


ORG_DOMAIN_NAME = 'alleninstitute.org'
'''
Machine-readable name of the top-level domain (TLD) hosting the organization
signified by the :data:`ORG_NAME` global.
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

# ....................{ METADATA ~ private                 }....................
_IS_TESTING = False
'''
``True`` only if the active Python interpreter is running a test session (e.g.,
with the ``py.test`` test harness).

This private global is subject to change and thus *not* intended to be publicly
accessed. Consider calling the public :func:`betse.util.py.pys.is_testing`
function instead.
'''
