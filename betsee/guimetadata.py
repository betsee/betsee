#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Metadata constants synopsizing high-level application behaviour.
'''

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during setuptools-based installation, this
# module may import *ONLY* from modules guaranteed to exist at the start of
# installation. This includes all standard Python and application modules but
# *NOT* third-party dependencies, which if currently uninstalled will only be
# installed at some later time in installation.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import sys

# ....................{ METADATA                          }....................
NAME = 'BETSEE'
'''
Human-readable application name.
'''


LICENSE = '2-clause BSD'
'''
Human-readable name of the license this application is licensed under.
'''

# ....................{ PYTHON ~ version                  }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: Changes to this section *MUST* be synchronized with:
# * Front-facing documentation (e.g., "README.rst", "doc/md/INSTALL.md").
# On bumping the minimum required version of Python, consider also documenting
# the justification for doing so in the "Python Version" section of this
# submodule's docstring above.
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

PYTHON_VERSION_MIN = '3.5.0'
'''
Human-readable minimum version of Python required by this application as a
``.``-delimited string.
'''


PYTHON_VERSION_MINOR_MAX = 8
'''
Maximum minor stable version of the current Python 3.x mainline (e.g., ``9`` if
Python 3.9 is the most recent stable version of Python 3.x).
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
tuple of integers (e.g., ``(3, 5, 0)`` if this application requires at least
Python 3.5.0).
'''


# Validate the active Python interpreter version *BEFORE* subsequent code
# depending on this version. See "betse.metadata" for further details.
if sys.version_info[:3] < PYTHON_VERSION_MIN_PARTS:
    PYTHON_VERSION = '.'.join(
        str(version_part) for version_part in sys.version_info[:3])

    raise RuntimeError(
        '{} requires at least Python {}, but the active interpreter '
        'is only Python {}. We feel deep sadness for you.'.format(
            NAME, PYTHON_VERSION_MIN, PYTHON_VERSION))

# ....................{ METADATA ~ version                }....................
VERSION = '1.1.0.0'
'''
Human-readable application version as a ``.``-delimited string.

Caveats
----------
**This string must be prefixed by the exact version of BETSE required by this
version of BETSEE.** Each version of BETSEE requires the same version of BETSE,
excluding the trailing patch number of that version of BETSEE (e.g., BETSEE
1.1.0.0 and 1.1.0.1 both require BETSE 1.1.0). Since newer versions of BETSE
typically break backward compatibility with older versions of BETSEE, this
dependency does *not* extend to newer versions of BETSE -- which *cannot* be
guaranteed to preserve backward compatibility.

Equivalently, this string must be of the form
``{betse_version}.{patch_version}``, where:

* ``{betse_version}`` is the version of BETSE required by this version of
  BETSEE.
* ``{patch_version}`` is the patch number of this version of BETSEE relative to
  this version of BETSE.

For example, if this is the second iteration of BETSE to require BETSE 0.8.5,
this version is expected to be ``0.8.5.2``.

This is *not* merely a style convention; this is a hard prerequisite. Why?
Because this string is parsed elsewhere (e.g., the `:mod:`betsee.guimetadeps`
submodule) to produce a setuptools-specific dependency on this BETSE version.
Failure to conform to this specification will induce user dependency hell at
both distribution and installation time, which is (rather) bad.
'''


VERSION_PARTS = _convert_version_str_to_tuple(VERSION)
'''
Machine-readable application version as a tuple of integers.
'''

# ....................{ METADATA ~ synopsis               }....................
# Note that a human-readable multiline description is exposed via the top-level
# "setup.py" script. This description is inefficiently culled from the contents
# of the top-level "README.rst" file and hence omitted here. (Doing so here
# would significantly increase program startup costs with little to no gain.)
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
multiple lines and paragraphs. Note that this string is *not* published to
PyPI, which accepts reStructuredText (rst) and is thus passed the contents of
the top-level :doc:`/README` file instead.
'''

# ....................{ METADATA ~ authors                }....................
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

# ....................{ METADATA ~ organization           }....................
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

# ....................{ METADATA ~ urls                   }....................
URL_HOMEPAGE = 'https://gitlab.com/betse/betsee'
'''
URL of this application's homepage.
'''


URL_DOWNLOAD = '{}/repository/archive.tar.gz?ref=v{}'.format(
    URL_HOMEPAGE, VERSION)
'''
URL of the source tarball for the current version of this application.

This URL assumes a tag whose name is ``v{VERSION}`` where ``{VERSION}`` is the
human-readable current version of this application (e.g., ``v0.4.0``) to exist.
Typically, no such tag exists for live versions of this application -- which
have yet to be stabilized and hence tagged. Hence, this URL is typically valid
*only* for previously released (rather than live) versions of this application.
'''

# ....................{ METADATA ~ python                 }....................
#FIXME: Replace all references to this global with
#"betse.appmeta.app_meta.package_name", which supports both BETSE and BETSEE;
#then excise this global.
PACKAGE_NAME = NAME.lower()
'''
Fully-qualified name of the top-level Python package implementing this
application.
'''

# ....................{ METADATA ~ python : main window   }....................
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
