.. # ------------------( BADGES                             )------------------
.. #FIXME: Depict the current BETSEE rather than BETSE build status after
.. #creating a BETSEE test suite.

.. image::  https://gitlab.com/betse/betse/badges/master/build.svg
   :target: https://gitlab.com/betse/betse/pipelines
   :alt: Linux Build Status
.. image::  https://ci.appveyor.com/api/projects/status/mow7y8k3vpfu30c6/branch/master?svg=true
   :target: https://ci.appveyor.com/project/betse/betse/branch/master
   :alt: Windows Build Status

.. # ------------------( SYNOPSIS                           )------------------

======
BETSEE
======

**BETSEE** (**B**\ io\ **E**\ lectric **T**\ issue **S**\ imulation
**E**\ ngine **E**\ nvironment) is the open-source cross-platform graphical user
interface (GUI) for BETSE_, a  `finite volume`_ simulator for 2D computational
multiphysics problems in the life sciences – including electrodiffusion_,
electro-osmosis_, galvanotaxis_, `voltage-gated ion channels`_, `gene regulatory
networks`_, and `biochemical reaction networks`_ (e.g., metabolism). BETSE is
associated with the `Paul Allen Discovery Center`_ at `Tufts University`_ and
supported by a `Paul Allen Discovery Center award`_ from the `Paul G. Allen
Frontiers Group`_.

Like BETSE_, BETSEE is `portably implemented <codebase_>`__ in pure `Python 3
<Python_>`__, `continuously stress-tested <testing_>`__ with GitLab-CI_ **×**
Appveyor_ **+** py.test_, and `permissively distributed <License_>`__ under the
`BSD 2-clause license`_.

.. # ------------------( TABLE OF CONTENTS                  )------------------
.. # Blank line. By default, Docutils appears to only separate the subsequent
.. # table of contents heading from the prior paragraph by less than a single
.. # blank line, hampering this table's readability and aesthetic comeliness.

|

.. # Table of contents, excluding the above document heading. While the
.. # official reStructuredText documentation suggests that a language-specific
.. # heading will automatically prepend this table, this does *NOT* appear to
.. # be the case. Instead, this heading must be explicitly declared.

.. contents:: **Contents**
   :local:

.. # ------------------( DESCRIPTION                        )------------------

Installation
============

.. Note::
   BETSEE is pre-release software under active development. No packages
   automating installation of either BETSEE itself *or* BETSEE dependencies are
   currently provided. In particular, there currently exist no:
   
   - Platform-agnostic BETSEE packages (e.g., Anaconda_, PyPI_).
   - platform-specific BETSEE packages (e.g., macOS_ Homebrew_, Ubuntu_ PPA_).

BETSEE is manually installable as follows:

#. Install the `unstable live version <BETSE live_>`__ of BETSE_.
#. Install Qt_ `5.6 <Qt 5.6_>`__. [#pyside2_install]_
#. Install the `stable 5.6 branch <_PySide2 5.6>`__ of PySide2_.
   [#pyside2_install]_
#. Open a **terminal.**
#. Clone the ``master`` branch of this repository.

   .. code:: bash

      git clone https://gitlab.com/betse/betsee.git

#. **Install BETSEE.**

   .. code:: bash

      cd betsee
      sudo python3 setup.py install

.. [#pyside2_install]
   Like BETSEE, PySide2_ is pre-release software under active development.
   Unlike BETSEE, packages automating installation of both PySide2_ itself and
   PySide2_ dependencies (e.g., Qt_) *are* available for various platforms –
   including:

   - `Arch Linux`_ via the `official PySide2 installation instructions
     <PySide2 installation_>`__.
   - `Gentoo Linux`_ via the `official PySide2 installation instructions
     <PySide2 installation_>`__.
   - `Ubuntu Linux <Ubuntu_>`__ via the `unofficial PySide2 PPA
     <PySide2 PPA_>`__.

License
=======

BETSEE is open-source software `released <LICENSE>`__ under the permissive `BSD
2-clause license`_ and containing third-party assets also released under
`BSD-compatible licenses <license compatibility_>`__, including:

* All `Open Iconic`_ icons distributed in the
  ``betsee/data/qrc/icon/open_iconic`` subdirectory, `released <Open Iconic
  license_>`__ under the permissive `MIT license`_.

Reference
=========

When leveraging BETSEE in your own work, consider citing our `introductory
paper`_:

    `Pietak, Alexis`_ and `Levin, Michael`_ (\ *2016*\ ). |article name|_
    |journal name|_ 4, 55. ``doi:10.3389/fbioe.2016.00055``

Authors
=======

BETSEE comes courtesy a dedicated community of `authors <author list_>`__ and
contributors_ – without whom this project would be computationally impoverished,
biologically misaligned, and simply unusable.

**Thanks, all.**

.. # ------------------( LINKS ~ betse                      )------------------
.. _BETSE:
   https://gitlab.com/betse/betse
.. _BETSE live:
   https://gitlab.com/betse/betse#advanced

.. # ------------------( LINKS ~ betsee                     )------------------
.. _author list:
   doc/rst/AUTHORS.rst
.. _codebase:
   https://gitlab.com/betse/betsee/tree/master
.. _contributors:
   https://gitlab.com/betse/betsee/graphs/master
.. _dependencies:
   doc/md/INSTALL.md
.. _testing:
   https://gitlab.com/betse/betsee/pipelines
.. _tarballs:
   https://gitlab.com/betse/betsee/tags

.. # ------------------( LINKS ~ academia                   )------------------
.. _Pietak, Alexis:
   https://www.researchgate.net/profile/Alexis_Pietak
.. _Levin, Michael:
   https://ase.tufts.edu/biology/labs/levin
.. _Paul Allen Discovery Center:
   http://www.alleninstitute.org/what-we-do/frontiers-group/discovery-centers/allen-discovery-center-tufts-university
.. _Paul Allen Discovery Center award:
   https://www.alleninstitute.org/what-we-do/frontiers-group/news-press/press-resources/press-releases/paul-g-allen-frontiers-group-announces-allen-discovery-center-tufts-university
.. _Paul G. Allen Frontiers Group:
   https://www.alleninstitute.org/what-we-do/frontiers-group
.. _Tufts University:
   https://www.tufts.edu

.. # ------------------( LINKS ~ citation                   )------------------
.. _introductory paper:
   http://journal.frontiersin.org/article/10.3389/fbioe.2016.00055/abstract

.. |article name| replace::
   **Exploring Instructive Physiological Signaling with the Bioelectric Tissue
   Simulation Engine (BETSE).**
.. _article name:
   http://journal.frontiersin.org/article/10.3389/fbioe.2016.00055/abstract

.. |journal name| replace::
   *Frontiers in Bioengineering and Biotechnology.*
.. _journal name:
   http://journal.frontiersin.org/journal/bioengineering-and-biotechnology

.. # ------------------( LINKS ~ science                    )------------------
.. _biochemical reaction networks:
   http://www.nature.com/subjects/biochemical-reaction-networks
.. _electrodiffusion:
   https://en.wikipedia.org/wiki/Nernst%E2%80%93Planck_equation
.. _electro-osmosis:
   https://en.wikipedia.org/wiki/Electro-osmosis
.. _finite volume:
   https://en.wikipedia.org/wiki/Finite_volume_method
.. _galvanotaxis:
   https://en.wiktionary.org/wiki/galvanotaxis
.. _gene regulatory networks:
   https://en.wikipedia.org/wiki/Gene_regulatory_network
.. _voltage-gated ion channels:
   https://en.wikipedia.org/wiki/Voltage-gated_ion_channel

.. # ------------------( LINKS ~ software                   )------------------
.. _Anaconda:
   https://www.continuum.io/downloads
.. _Appveyor:
   https://ci.appveyor.com/project/betse/betse/branch/master
.. _Bash on Ubuntu on Windows:
   http://www.windowscentral.com/how-install-bash-shell-command-line-windows-10
.. _FFmpeg:
   https://ffmpeg.org
.. _Git:
   https://git-scm.com/downloads
.. _GitLab-CI:
   https://about.gitlab.com/gitlab-ci
.. _Graphviz:
   http://www.graphviz.org
.. _Homebrew:
   http://brew.sh
.. _Libav:
   https://libav.org
.. _macOS:
   https://en.wikipedia.org/wiki/Macintosh_operating_systems
.. _MacPorts:
   https://www.macports.org
.. _Matplotlib:
   http://matplotlib.org
.. _NumPy:
   http://www.numpy.org
.. _MEncoder:
   https://en.wikipedia.org/wiki/MEncoder
.. _Open Iconic:
   https://github.com/iconic/open-iconic
.. _POSIX:
   https://en.wikipedia.org/wiki/POSIX
.. _PPA:
   https://launchpad.net/ubuntu/+ppas
.. _PyPI:
   https://pypi.python.org
.. _Python:
   https://www.python.org
.. _py.test:
   http://pytest.org
.. _SciPy:
   http://www.scipy.org
.. _YAML:
   http://yaml.org

.. # ------------------( LINKS ~ software : linux           )------------------
.. _APT:
   https://en.wikipedia.org/wiki/Advanced_Packaging_Tool
.. _Arch Linux:
   https://www.archlinux.org
.. _Gentoo Linux:
   https://gentoo.org
.. _Ubuntu:
   https://www.ubuntu.com

.. # ------------------( LINKS ~ software : pyside2         )------------------
.. _PySide2:
   https://wiki.qt.io/PySide2
.. _PySide2 5.6:
   https://code.qt.io/cgit/pyside/pyside.git/log/?h=5.6
.. _PySide2 installation:
   https://wiki.qt.io/PySide2_GettingStarted
.. _PySide2 PPA:
   https://launchpad.net/~thopiekar/+archive/ubuntu/pyside-git
.. _Qt:
   https://www.qt.io
.. _Qt 5.6:
   https://wiki.qt.io/Qt_5.6_Release

.. # ------------------( LINKS ~ software : licenses        )------------------
.. _license compatibility:
   https://en.wikipedia.org/wiki/License_compatibility#Compatibility_of_FOSS_licenses
.. _BSD 2-clause license:
   https://opensource.org/licenses/BSD-2-Clause
.. _MIT license:
   https://opensource.org/licenses/MIT
.. _Open Iconic license:
   licenses/open_iconic
