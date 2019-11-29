#!/usr/bin/env python3
# --------------------( LICENSE                           )--------------------
# Copyright 2017-2019 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
:mod:`setuptools`-based makefile instrumenting all high-level administration
tasks (e.g., installation, freezing, test running) for this application.
'''

# ....................{ KLUDGES                           }....................
# Explicitly register all files and subdirectories of the root directory
# containing this top-level "setup.py" script to be importable modules and
# packages (respectively) for the remainder of this Python process if this
# directory has yet to be registered.
#
# Technically, this should *NOT* be required. The current build framework
# (e.g., "pip", "setuptools") should implicitly guarantee this to be the case.
# Indeed, the "setuptools"-based "easy_install" script does just that.
# Unfortunately, "pip" >= 19.0.0 does *NOT* guarantee this to be the case for
# projects defining a "pyproject.toml" file -- which, increasingly, is all of
# them. Although "pip" purports to have resolved this upstream, current stable
# release appear to suffer the same deficiencies. See also:
#     https://github.com/pypa/pip/issues/6163
#
# Note this logic necessarily duplicates the implementation of the
# betse.util.py.module import pyimport.register_dir() function. *sigh*

# Isolate this kludge to a private function for safety.
def _register_dir() -> None:

    # Avert thy eyes, purist Pythonistas!
    import os, sys

    # Absolute dirname of this directory, inspired by the following
    # StackOverflow answer: https://stackoverflow.com/a/8663557/2809027
    setup_dirname = os.path.dirname(os.path.realpath(__file__))

    # If the current PYTHONPATH does *NOT* already contain this directory...
    if setup_dirname not in sys.path:
        # Print this registration.
        print(
            'WARNING: Registering "setup.py" directory for importation under '
            'broken installer (e.g., pip >= 19.0.0)...',
            file=sys.stderr)
        # print('setup_dirname: {}\nsys.path: {!r}'.format(setup_dirname, sys.path))

        # Append this directory to the current PYTHONPATH.
        sys.path.append(setup_dirname)

# Kludge us up the bomb.
_register_dir()

# ....................{ IMPORTS                           }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid race conditions during setuptools-based installation, this
# module may import *ONLY* from packages guaranteed to exist at the start of
# installation. This includes all standard Python and application packages but
# *NOT* third-party dependencies, which if currently uninstalled will only be
# installed at some later time in the installation.
#
# Technically, this script may import from all subpackages and submodules of
# the this application's eponymous package. By Python mandate, the first
# element of the "sys.path" list is guaranteed to be the directory containing
# this script. Python necessarily searches this directory for imports from the
# local version of this application *BEFORE* any other directories (including
# system directories containing older versions of this application). To quote:
#
#     "As initialized upon program startup, the first item of this list,
#      path[0], is the directory containing the script that was used to invoke
#      the Python interpreter."
#
# See also: https://stackoverflow.com/a/10097543/2809027
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import setuptools
from betsee import guimetadata, guimetadeps
from betsee_setup import beupbuild, beuputil

# ....................{ EXCEPTIONS                        }....................
# Validate the currently installed version of setuptools to meet all
# installation-time requirements of this application.
beuputil.die_unless_setuptools_version_at_least(
    guimetadeps.SETUPTOOLS_VERSION_MIN)

# ....................{ METADATA                          }....................
# PyPI-specific metadata declared here rather than in the "betsee.metadata"
# submodule, as the main codebase neither requires nor desires this metadata.

# ....................{ METADATA ~ seo                    }....................
_KEYWORDS = ['biology', 'multiphysics', 'science', 'simulator',]
'''
List of all lowercase alphabetic keywords synopsising this application.

These keywords may be arbitrarily selected so as to pretend to improve search
engine optimization (SEO). In actuality, they do absolutely nothing.
'''


# To minimize desynchronization woes, all
# "Programming Language :: Python :: "-prefixed strings are dynamically
# appended to this list by the get_classifiers() function called below.
_CLASSIFIERS = [
    # PyPI-specific version type. The number specified here is a magic constant
    # with no relation to this application's version numbering scheme. *sigh*
    'Development Status :: 5 - Production/Stable',

    # Sublist of all supported platform-specific CLI and GUI components.
    'Environment :: MacOS X',
    'Environment :: Win32 (MS Windows)',
    'Environment :: X11 Applications',

    # Miscellaneous metadata.
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
]
'''
List of all PyPI-specific trove classifier strings synopsizing this
application.

Each such string *must* be contain either two or three `` :: `` substrings
delimiting human-readable capitalized English words formally recognized by the
:mod:`distutils`-specific ``register`` command.

See Also
----------
https://pypi.python.org/pypi?%3Aaction=list_classifiers
    Plaintext list of all trove classifier strings recognized by PyPI.
'''

# ....................{ OPTIONS                           }....................
# Setuptools-specific options. Keywords not explicitly recognized by either
# setuptools or distutils must be added to the above dictionary instead.
_SETUP_OPTIONS = {
    # ..................{ CORE                              }..................
    # Self-explanatory metadata. Note that the following metadata keys are
    # instead specified by the "setup.cfg" file,
    #
    # * "license_file", for unknown reasons. We should probably reconsider
    # * "long_description", since "setup.cfg" supports convenient
    #   "file: ${relative_filename}" syntax for transcluding the contents of
    #   arbitrary project-relative files into metadata values. Attempting to do
    #   so here would require safely opening this file with a context manager,
    #   reading the contents of this file into a local variable, and passing
    #   that variable's value as this metadata outside of that context. (Ugh.)
    'name':             guimetadata.PACKAGE_NAME,
    'version':          guimetadata.VERSION,
    'author':           guimetadata.AUTHORS,
    'author_email':     guimetadata.AUTHOR_EMAIL,
    'maintainer':       guimetadata.AUTHORS,
    'maintainer_email': guimetadata.AUTHOR_EMAIL,
    'description':      guimetadata.SYNOPSIS,
    'url':              guimetadata.URL_HOMEPAGE,
    'download_url':     guimetadata.URL_DOWNLOAD,

    # ..................{ PYPI                              }..................
    # PyPi-specific metadata.
    'classifiers': beuputil.sanitize_classifiers(
        classifiers=_CLASSIFIERS,
        python_version_min_parts=guimetadata.PYTHON_VERSION_MIN_PARTS,
        python_version_minor_max=guimetadata.PYTHON_VERSION_MINOR_MAX,
    ),
    'keywords': _KEYWORDS,
    'license': guimetadata.LICENSE,

    # ..................{ DEPENDENCIES                      }..................
    # Python dependency.
    'python_requires': '>=' + guimetadata.PYTHON_VERSION_MIN,

    # Mandatory nuntime dependencies.
    'install_requires': guimetadeps.get_runtime_mandatory_tuple(),

    # Optional nuntime dependencies. Whereas mandatory dependencies are defined
    # as sequences, optional dependencies are defined as a dictionary mapping
    # from an arbitrary alphanumeric word to a sequence containing one or more
    # such dependencies. Such dependencies are then installable via "pip" by
    # suffixing the name of this project by the "["- and "]"-delimited key
    # defined below whose value lists the dependencies to be installed (e.g.,
    # "sudo pip3 install betse[all]", installing both the application and all
    # mandatory and optional dependencies required by the application).
    'extras_require': {
        # All optional runtime dependencies.
        'all': guimetadeps.get_runtime_optional_tuple(),

        # All mandatory testing dependencies, copied from the "tests_require"
        # key below into an arbitrarily named extra. This is required *ONLY*
        # for integration with the top-level "tox.ini" file. See the "extras"
        # key in that file for further details.
        'test': guimetadeps.get_testing_mandatory_tuple(),
    },

    # Mandatory testing dependencies.
    'tests_require': guimetadeps.get_testing_mandatory_tuple(),

    # ..................{ PACKAGES                          }..................
    # List of the fully-qualified names of all Python packages (i.e.,
    # directories containing zero or more Python modules) to be installed,
    # including the top-level application package and all subpackages of that
    # package. This thus excludes:
    #
    # * The top-level test package and all subpackages of this package, test
    #   functionality *NOT* intended to be installed with this application.
    # * The top-level setup package and all subpackages of this package,
    #   setuptools functionality required only for application installation.
    # * "build", caching both setuptools metadata and a complete copy of this
    #   package, required only by a prior application installation.
    # * "freeze", providing PyInstaller-specific functionality required only
    #   for application freezing (i.e., conversion into an executable binary).
    #
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # WARNING: This inspection intentionally omits subdirectories containing no
    # "__init__.py" file, despite the remainder of the Python ecosystem
    # commonly accepting such subdirectories as subpackages.
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    'packages': setuptools.find_packages(exclude=(
        guimetadata.PACKAGE_NAME + '_test',
        guimetadata.PACKAGE_NAME + '_test.*',
        guimetadata.PACKAGE_NAME + '_setup',
        guimetadata.PACKAGE_NAME + '_setup.*',
        'build',
        'freeze',
    )),

    # ..................{ PATHS                             }..................
    # Cross-platform script wrappers dynamically created at installation time.
    'entry_points': {
        # GUI-specific scripts.
        'gui_scripts': (
            '{0} = {0}.__main__:main'.format(guimetadata.PACKAGE_NAME)),
    },

    # Install all data files (i.e., non-Python files) embedded in the Python
    # package tree for this application.
    #
    # Unlike Python packages, undesirable data files are excludable from
    # installation *ONLY* via the external "MANIFEST.in" file. This is
    # terrible, of course. (Did you expect otherwise?)
    #
    # Data files are *NOT* Python modules and hence should *NOT* be embedded in
    # the Python package tree. Sadly, the "data_files" key supported by
    # setuptools for this purpose is *NOT* cross-platform-portable and is thus
    # inherently broken. Why? Because this key either requires usage of
    # absolute paths *OR* relative paths relative to absolute paths defined by
    # "setup.cfg"; in either case, these paths are absolute. While the current
    # platform could be detected and the corresponding absolute path embedded
    # in 'data_files', that implementation would be inherently fragile. (That's
    # bad.) In lieu of sane setuptools support, we defer to the methodology
    # employed by everyone. Setuptools, your death is coming.
    'include_package_data': True,

    # Install to an uncompressed directory rather than a compressed archive.
    #
    # While nothing technically precludes the latter, doing so substantially
    # complicates runtime access of data files compressed into this archive
    # (e.g., with the pkg_resources.resource_filename() function). How so? By
    # decompressing this archive's contents into a temporary directory on
    # program startup and removing these contents on program shutdown. Since
    # there exists no guarantee this removal will actually be performed (e.g.,
    # due to preemptive SIGKILLs), compressed archives are inherently fragile.
    'zip_safe': False,

    # ..................{ COMMANDS                          }..................
    # Set of all custom setuptools subcommands specific to this makefile (e.g.,
    # "sudo python3 setup.py symlink"), defaulting to the empty set. Each
    # subsequent call to the add_setup_commands() function iteratively
    # performed below adds one or more such subcommands to this set.
    'cmdclass': {},
}
'''
Dictionary passed to the subsequent call to the :func:`setup` function.

This dictionary signifies the set of all application-specific :mod:`setuptools`
options. Submodules of the top-level :mod:`betsee_setup` package subsequently
customize these options (e.g., by defining custom commands).
'''
# print('extras: {}'.format(setup_options['extras_require']))


# While currently empty, it's likely we'll want this again... someday.
_SETUP_OPTIONS_CUSTOM = {}
'''
Non-setuptools-specific metadata, used to inform custom subcommands (e.g.,
``freeze_file``) of other metadata *not* already declared by the
:data:`setup_options` dictionary.

Setuptools raises fatal exceptions when the :data:`setup_options` dictionary
contains unrecognized keys. For safety, these keys are added to this dictionary
instead.
'''

# ....................{ SUBCOMMANDS                       }....................
# List of all submodules defining custom setuptools subcommands.
_subcommand_submodules = [beupbuild]

# Attempt to...
try:
    # Import BETSE-specific submodules defining custom setuptools subcommands.
    from betse.lib.setuptools.command import supcmdtest

    # Append these submodules to this list.
    _subcommand_submodules.append(supcmdtest)
# If setuptools has yet to install BETSE, silently ignore these subcommands.
# Since none of these subcommands are required (or desired) at installation
# time, the lack of these subcommands does *NOT* constitute an error.
except ImportError:
    pass

# Define these subcommands.
for _subcommand_submodule in _subcommand_submodules:
    _subcommand_submodule.add_subcommand(_SETUP_OPTIONS, _SETUP_OPTIONS_CUSTOM)

# ....................{ SETUP                             }....................
setuptools.setup(**_SETUP_OPTIONS)
