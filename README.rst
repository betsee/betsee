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

=====
BETSEE
=====

**BETSEE** (**B**\ io\ **E**\ lectric **T**\ issue **S**\ imulation
**E**\ ngine **E**\ nvironment) is the open-source cross-platform graphical user
interface (GUI) for BETSE_, a  `finite volume`_ simulator for 2D computational
multiphysics problems in the life sciences – including electrodiffusion_,
electro-osmosis_, galvanotaxis_, `voltage-gated ion channels`_, `gene regulatory
networks`_, and `biochemical reaction networks`_ (e.g., metabolism). BETSE is
associated with the `Paul Allen Discovery Center`_ at `Tufts University`_ and
supported by a `Paul Allen Discovery Center award`_ from the `Paul G. Allen
Frontiers Group`_.

Like BETSE_, BETSEE is `portably implemented <codebase_>`__ in pure `Python 3`_,
`continuously stress-tested <testing_>`__ with GitLab-CI_ **×** Appveyor_ **+**
py.test_, and `permissively distributed <License_>`__ under the `BSD 2-clause
license`_.

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

License
=======

BETSEE is open-source software `released <LICENSE>`__ under the permissive `BSD
2-clause license`_.

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

.. # ------------------( LINKS ~ betsee : docs              )------------------
.. _BETSE 0.4 documentation:
   https://www.dropbox.com/s/n8qfms2oks9cvv2/BETSE04_Documentation_Dec1st2016.pdf?dl=0
.. _BETSE 0.3 documentation:
   https://www.dropbox.com/s/fsxhjpipbiog0ru/BETSE_Documentation_Nov1st2015.pdf?dl=0

.. # ------------------( LINKS ~ academia                   )------------------
.. _Pietak, Alexis:
   https://www.researchgate.net/profile/Alexis_Pietak
.. _Levin, Michael:
   https://ase.tufts.edu/biology/labs/levin
.. _Channelpedia:
   http://channelpedia.epfl.ch
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
.. _bioelectricity:
   https://en.wikipedia.org/wiki/Bioelectromagnetics
.. _biochemical reaction networks:
   http://www.nature.com/subjects/biochemical-reaction-networks
.. _electrodiffusion:
   https://en.wikipedia.org/wiki/Nernst%E2%80%93Planck_equation
.. _electro-osmosis:
   https://en.wikipedia.org/wiki/Electro-osmosis
.. _enzyme activity:
   https://en.wikipedia.org/wiki/Enzyme_assay
.. _ephaptic coupling:
   https://en.wikipedia.org/wiki/Ephaptic_coupling
.. _epigenetics:
   https://en.wikipedia.org/wiki/Epigenetics
.. _extracellular environment:
   https://en.wikipedia.org/wiki/Extracellular
.. _finite volume:
   https://en.wikipedia.org/wiki/Finite_volume_method
.. _galvanotaxis:
   https://en.wiktionary.org/wiki/galvanotaxis
.. _gap junction:
.. _gap junctions:
   https://en.wikipedia.org/wiki/Gap_junction
.. _gene products:
   https://en.wikipedia.org/wiki/Gene_product
.. _gene regulatory networks:
   https://en.wikipedia.org/wiki/Gene_regulatory_network
.. _genetics:
   https://en.wikipedia.org/wiki/Genetics
.. _Hodgkin-Huxley (HH) formalism:
   https://en.wikipedia.org/wiki/Hodgkin%E2%80%93Huxley_model
.. _local field potentials:
   https://en.wikipedia.org/wiki/Local_field_potential
.. _membrane permeability:
   https://en.wikipedia.org/wiki/Cell_membrane
.. _resting potential:
   https://en.wikipedia.org/wiki/Resting_potential
.. _tight junctions:
   https://en.wikipedia.org/wiki/Tight_junction
.. _transmembrane voltage:
   https://en.wikipedia.org/wiki/Membrane_potential
.. _transepithelial potential:
   https://en.wikipedia.org/wiki/Transepithelial_potential_difference

.. # ------------------( LINKS ~ science : ions             )------------------
.. _anionic proteins:
   https://en.wikipedia.org/wiki/Ion#anion
.. _bicarbonate: https://en.wikipedia.org/wiki/Bicarbonate
.. _calcium:     https://en.wikipedia.org/wiki/Calcium_in_biology
.. _chloride:    https://en.wikipedia.org/wiki/Chloride
.. _hydrogen:    https://en.wikipedia.org/wiki/Hydron_(chemistry)
.. _sodium:      https://en.wikipedia.org/wiki/Sodium_in_biology
.. _potassium:   https://en.wikipedia.org/wiki/Potassium_in_biology

.. # ------------------( LINKS ~ science : channels         )------------------
.. _ion channel:
   https://en.wikipedia.org/wiki/Ion_channel
.. _leak channels:
   https://en.wikipedia.org/wiki/Leak_channel
.. _ligand-gated channels:
   https://en.wikipedia.org/wiki/Ligand-gated_ion_channel
.. _voltage-gated ion channels:
   https://en.wikipedia.org/wiki/Voltage-gated_ion_channel

.. |calcium-gated K+ channels| replace::
   Calcium-gated K\ :sup:`+` channels
.. _calcium-gated K+ channels:
   https://en.wikipedia.org/wiki/Calcium-activated_potassium_channel

.. # ------------------( LINKS ~ science : channels : type  )------------------
.. _HCN1:   http://channelpedia.epfl.ch/ionchannels/61
.. _HCN2:   http://channelpedia.epfl.ch/ionchannels/62
.. _HCN4:   http://channelpedia.epfl.ch/ionchannels/64
.. _Kir2.1: http://channelpedia.epfl.ch/ionchannels/42
.. _Kv1.1:  http://channelpedia.epfl.ch/ionchannels/1
.. _Kv1.2:  http://channelpedia.epfl.ch/ionchannels/2
.. _Kv1.5:  http://channelpedia.epfl.ch/ionchannels/5
.. _Kv3.3:  http://channelpedia.epfl.ch/ionchannels/13
.. _Kv3.4:  http://channelpedia.epfl.ch/ionchannels/14
.. _Nav1.2: http://channelpedia.epfl.ch/ionchannels/121
.. _Nav1.3: http://channelpedia.epfl.ch/ionchannels/122
.. _Nav1.6: http://channelpedia.epfl.ch/ionchannels/125
.. _L-type Ca:   http://channelpedia.epfl.ch/ionchannels/212
.. _T-type Ca:   https://en.wikipedia.org/wiki/T-type_calcium_channel

.. |P/Q-type Ca| replace:: :sup:`P`\ /\ :sub:`Q`-type Ca
.. _P/Q-type Ca:
   http://channelpedia.epfl.ch/ionchannels/78

.. # ------------------( LINKS ~ science : pumps : type     )------------------
.. _ion pumps:
   https://en.wikipedia.org/wiki/Active_transport

.. # ------------------( LINKS ~ science : pumps : type     )------------------
.. _V-ATPase: https://en.wikipedia.org/wiki/V-ATPase

.. |Ca2+-ATPase| replace:: Ca\ :sup:`2+`-ATPase
.. _Ca2+-ATPase: https://en.wikipedia.org/wiki/Calcium_ATPase

.. |H+/K+-ATPase| replace:: H\ :sup:`+`/K\ :sup:`+`-ATPase
.. _H+/K+-ATPase: https://en.wikipedia.org/wiki/Hydrogen_potassium_ATPase

.. |Na+/K+-ATPase| replace:: Na\ :sup:`+`/K\ :sup:`+`-ATPase
.. _Na+/K+-ATPase: https://en.wikipedia.org/wiki/Na%2B/K%2B-ATPase

.. # ------------------( LINKS ~ science : computer         )------------------
.. _Big Data:
   https://en.wikipedia.org/wiki/Big_data
.. _comma-separated values:
   https://en.wikipedia.org/wiki/Comma-separated_values
.. _continuous integration:
   https://en.wikipedia.org/wiki/Continuous_integration
.. _directed graphs:
   https://en.wikipedia.org/wiki/Directed_graph
.. _knowledge-based systems:
   https://en.wikipedia.org/wiki/Knowledge-based_systems

.. # ------------------( LINKS ~ software                   )------------------
.. _Anaconda:
   https://www.continuum.io/downloads
.. _Appveyor:
   https://ci.appveyor.com/project/betse/betse/branch/master
.. _APT:
   https://en.wikipedia.org/wiki/Advanced_Packaging_Tool
.. _Bash on Ubuntu on Windows:
   http://www.windowscentral.com/how-install-bash-shell-command-line-windows-10
.. _BSD 2-clause license:
   https://opensource.org/licenses/BSD-2-Clause
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
.. _MacPorts:
   https://www.macports.org
.. _Matplotlib:
   http://matplotlib.org
.. _NumPy:
   http://www.numpy.org
.. _MEncoder:
   https://en.wikipedia.org/wiki/MEncoder
.. _POSIX:
   https://en.wikipedia.org/wiki/POSIX
.. _Python 3:
   https://www.python.org
.. _py.test:
   http://pytest.org
.. _SciPy:
   http://www.scipy.org
.. _YAML:
   http://yaml.org
