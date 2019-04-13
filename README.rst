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

**BETSEE** (**B**\ io\ **E**\ lectric **T**\ issue **S**\ imulation **E**\
ngine **E**\ nvironment) is the open-source cross-platform graphical user
interface (GUI) for BETSE_, a  `finite volume`_ simulator for 2D computational
multiphysics problems in the life sciences – including electrodiffusion_,
electro-osmosis_, galvanotaxis_, `voltage-gated ion channels`_, `gene
regulatory networks`_, and `biochemical reaction networks`_ (e.g., metabolism).

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

BETSEE is installable under **Linux**, **macOS**, and **Windows** as follows:

- [\ *Windows*\ ] Emulate **Ubuntu Linux** via the `Windows Subsystem for Linux
  (WSL) <WSL_>`__. [#windows_not]_
- Install the **Python 3.x** [#python2_not]_ (e.g., 3.6) variant of Anaconda_.
  [#anaconda_not]_
- Open a **Bash terminal.** [#terminal]_
- Run the following commands.

  - Enable conda-forge_.

    .. code-block:: console

       conda config --add channels conda-forge

  - Install **BETSEE.** [#conda_package]_

    .. code-block:: console

       conda install betsee

  - [\ *Optional*\ ] Run **BETSEE.**

    .. code-block:: console

       betsee

.. [#windows_not]
   The `Windows Subsystem for Linux (WSL) <WSL_>`__ and – hence BETSEE itself –
   is *only* installable under **Windows 10.** Under older Windows versions,
   BETSEE may be installed from a `virtual Linux guest <VirtualBox_>`__.

.. [#python2_not]
   Do *not* install the **Python 2.7** variant of Anaconda_. BETSEE requires
   **Python 3.x.**

.. [#anaconda_not]
   BETSEE is currently *only* installable via Anaconda_, a cross-platform
   scientific Python distribution simplifying installation of non-Python
   dependencies (e.g., OpenBLAS_, PySide2_). While a `PyPI package`_ for
   installing BETSEE under ``pip`` (the standard Python package manager) does
   exist, `that package <PyPI package_>`__ is currently uninstallable due to
   a lack of official PySide2_ wheels. Even when official PySide2_ wheels are
   published, Anaconda_ will remain the official installation path for BETSE_
   and hence BETSEE. ``pip`` commonly produces a performance-crippled
   single-core installation of BETSE_. Anaconda_ suffers no such issues and is
   guaranteed to produce a performance-optimized multicore installation of
   BETSE_ on *all* supported platforms. We strongly recommend Anaconda_ – even
   when you think you know better.

.. [#terminal]
   To open a `POSIX`_\ -compatible terminal under:

   - **Windows:**

     #. Install **Ubuntu Linux** via the `Windows Subsystem for Linux (WSL) <WSL_>`__.
     #. Open an *Ubuntu Linux terminal.*

   - **macOS:**

     #. Open the *Finder*.
     #. Open the *Applications* folder.
     #. Open the *Utilities* folder.
     #. Open *Terminal.app*.

   - **Ubuntu Linux:**

     #. Type ``Ctrl``\ +\ ``Alt``\ +\ ``t``.

.. [#conda_package]

   This command installs both the `most recent stable release of BETSEE <conda
   package_>`__ *and* all mandatory and most optional dependencies of this
   release. Older stable releases are installable in a similar manner (e.g.,
   ``conda install betsee=0.8.2`` for BETSEE 0.8.2). All `Anaconda packages`_
   are kindly hosted by the `non-profit conda-forge organization
   <conda-forge_>`__.

License
=======

BETSEE is open-source software `released <LICENSE>`__ under the permissive `BSD
2-clause license`_. BETSEE contains third-party assets also released under
`BSD-compatible licenses <license compatibility_>`__, including:

* All `Entypo+ icons`_ `distributed with BETSEE <BETSEE Entypo+ icons_>`__,
  `kindly released <Entypo+ license_>`__ under the permissive `CC BY-SA 4.0
  license`_ by `Daniel Bruce`_.
* All `Noun Project icons`_ `distributed with BETSEE <BETSEE Noun Project
  icons_>`__, `kindly released <Noun Project license_>`__ under the permissive
  `CC BY 3.0 license`_ by various authors, including:

  * `Maxim Kulikov`_, author of the `salubrious bovine <Cows collection_>`__
    prominently displayed on this `project page <project_>`__.

* All `Open Iconic icons`_ `distributed with BETSEE <BETSEE Open Iconic
  icons_>`__, `kindly released <Open Iconic license_>`__ under the permissive
  `MIT license`_.

Citation
=========

BETSE_ is formally described in our `introductory paper <2016 article_>`__.
Third-party papers, theses, and other texts leveraging BETSEE (and hence
BETSE_) should ideally cite the following:

    `Alexis Pietak`_ and `Michael Levin`_, 2016. |2016 article name|_
    |2016 article supplement|_ [#supplement]_ |2016 journal name|_ *4*\ (55).
    :sup:`https://doi.org/10.3389/fbioe.2016.00055`

See also `this list of BETSE-centric papers <BETSE citation_>`__ for
additional material.

.. [#supplement]
   This article's supplement extends the cursory theory presented by this
   article with a rigorous treatment of the mathematics, formalisms, and
   abstractions required to fully reproduce this work. If theoretical questions
   remain after completing the main article, please consult this supplement.

Authors
=======

BETSEE comes courtesy a dedicated community of `authors <author list_>`__ and
contributors_ – without whom this project would be computationally
impoverished, biologically misaligned, and simply unusable.

**Thanks, all.**

Funding
=======

BETSEE is currently independently financed as a volunteer open-source project.
Prior grant funding sources include (in chronological order):

#. For the three year period spanning 2017—2019, BETSEE was graciously
   associated with the `Paul Allen Discovery Center`_ at `Tufts University`_
   and supported by a `Paul Allen Discovery Center award`_ from the `Paul G.
   Allen Frontiers Group`_ .

.. # ------------------( LINKS ~ betse                      )------------------
.. _BETSE:
   https://gitlab.com/betse/betse
.. _BETSE citation:
   https://gitlab.com/betse/betse#citation
.. _BETSE live:
   https://gitlab.com/betse/betse#advanced

.. # ------------------( LINKS ~ betsee                     )------------------
.. _author list:
   doc/rst/AUTHORS.rst
.. _codebase:
   https://gitlab.com/betse/betsee/tree/master
.. _conda package:
   https://anaconda.org/conda-forge/betsee
.. _contributors:
   https://gitlab.com/betse/betsee/graphs/master
.. _dependencies:
   doc/md/INSTALL.md
.. _project:
   https://gitlab.com/betse/betsee
.. _PyPI package:
   https://pypi.org/project/betsee
.. _testing:
   https://gitlab.com/betse/betsee/pipelines
.. _tarballs:
   https://gitlab.com/betse/betsee/tags
.. _Ubuntu 16.04 installer:
   https://gitlab.com/betse/betsee/blob/master/bin/install/linux/betsee_ubuntu_16_04.bash

.. # ------------------( LINKS ~ academia                   )------------------
.. _Alexis Pietak:
.. _Pietak, Alexis:
   https://www.researchgate.net/profile/Alexis_Pietak
.. _Michael Levin:
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

.. # ------------------( LINKS ~ paper : 2016               )------------------
.. _2016 article:
   http://journal.frontiersin.org/article/10.3389/fbioe.2016.00055/abstract

.. |2016 article name| replace::
   **Exploring instructive physiological signaling with the bioelectric tissue
   simulation engine (BETSE).**
.. _2016 article name:
   http://journal.frontiersin.org/article/10.3389/fbioe.2016.00055/abstract

.. |2016 article supplement| replace::
   **(**\ Supplement\ **).**
.. _2016 article supplement:
   https://www.frontiersin.org/articles/file/downloadfile/203679_supplementary-materials_datasheets_1_pdf/octet-stream/Data%20Sheet%201.PDF/1/203679

.. |2016 journal name| replace::
   *Frontiers in Bioengineering and Biotechnology,*
.. _2016 journal name:
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

.. # ------------------( LINKS ~ os : linux                 )------------------
.. _APT:
   https://en.wikipedia.org/wiki/Advanced_Packaging_Tool
.. _Arch Linux:
   https://www.archlinux.org
.. _CentOS:
   https://www.centos.org
.. _Gentoo Linux:
   https://gentoo.org
.. _Ubuntu:
.. _Ubuntu Linux:
   https://www.ubuntu.com
.. _Ubuntu Linux 16.04 (Xenial Xerus):
   http://releases.ubuntu.com/16.04

.. # ------------------( LINKS ~ os : windows               )------------------
.. _WSL:
   https://msdn.microsoft.com/en-us/commandline/wsl/install-win10

.. # ------------------( LINKS ~ software                   )------------------
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
.. _Miniconda:
   https://conda.io/miniconda.html
.. _NumPy:
   http://www.numpy.org
.. _MEncoder:
   https://en.wikipedia.org/wiki/MEncoder
.. _OpenBLAS:
   https://www.openblas.net
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
.. _VirtualBox:
   https://www.virtualbox.org
.. _YAML:
   http://yaml.org

.. # ------------------( LINKS ~ software : conda           )------------------
.. _Anaconda:
   https://www.anaconda.com/download
.. _Anaconda packages:
   https://anaconda.org
.. _conda-forge:
   https://conda-forge.org

.. # ------------------( LINKS ~ software : icon            )------------------
.. _BETSEE Entypo+ icons:
   betsee/data/qrc/icon/entypo+
.. _BETSEE Noun Project icons:
   betsee/data/qrc/icon/nounproject
.. _BETSEE Open Iconic icons:
   betsee/data/qrc/icon/open_iconic
.. _Cows collection:
   https://thenounproject.com/maxim221/collection/cows
.. _Daniel Bruce:
   http://www.danielbruce.se
.. _Entypo+ icons:
   http://entypo.com
.. _Maxim Kulikov:
   https://thenounproject.com/maxim221
.. _Noun Project:
.. _Noun Project icons:
   https://thenounproject.com
.. _Noun Project license:
   https://thenounproject.com/legal
.. _Open Iconic icons:
   https://github.com/iconic/open-iconic

.. # ------------------( LINKS ~ software : pyside2         )------------------
.. _PySide2:
   https://wiki.qt.io/PySide2
.. _PySide2 5.9:
   http://code.qt.io/cgit/pyside/pyside-setup.git/log/?h=5.9
.. _PySide2 feedstock:
   https://github.com/conda-forge/pyside2-feedstock
.. _PySide2 installation:
   https://wiki.qt.io/PySide2_GettingStarted
.. _PySide2 PPA:
   https://launchpad.net/~thopiekar/+archive/ubuntu/pyside-git
.. _PySide2 wheels:
   https://github.com/fredrikaverpil/pyside2-wheels/blob/master/QUICKSTART.md
.. _Qt:
   https://www.qt.io
.. _Qt 5.9:
   https://wiki.qt.io/Qt_5.9_Release

.. # ------------------( LINKS ~ software : licenses        )------------------
.. _license compatibility:
   https://en.wikipedia.org/wiki/License_compatibility#Compatibility_of_FOSS_licenses
.. _BSD 2-clause license:
   https://opensource.org/licenses/BSD-2-Clause
.. _CC BY 3.0 license:
   https://creativecommons.org/licenses/by/3.0
.. _CC BY-SA 4.0 license:
   https://creativecommons.org/licenses/by-sa/4.0
.. _Entypo+ license:
   licenses/entypo+
.. _MIT license:
   https://opensource.org/licenses/MIT
.. _Open Iconic license:
   licenses/open_iconic
