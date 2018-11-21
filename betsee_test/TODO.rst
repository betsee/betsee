======
TODO
======

Create a test suite exercising both functional and unit tests loosely inspired
by BETSE's existing test suite. Note, in particular, the need for:

* Functional tests, including:

  * A test ensuring that the application acutally starts up without exception
    on all supported platforms and Python environments -- particularly "conda".
    * To do so, we'll presumably want to leverage the "pytest-qt" plugin, which
      provides a "qtbot" fixture wrapping the standard "QTest" Qt API with a
      py.test-friendly API. The issue here, of course, is that we probably
      won't be able to invoke functional tests in the manner that we do for
      BETSE; notably, we won't be able to fork the external "betsee" command as
      an external process. Why? Because "pytest-qt" only behaves as expected
      for the current process. Wait. Actually, "pytest-qt" and "QTest" are only
      genuinely of interest when unit testing. Their applicability for
      functional testing appears to be limited and possibly non-existent...
    * Ah-ha! It would seem that we require "pytest-xfvb", which wraps Xvfb
      (i.e., an X.org-based  virtual frame buffer) rather than "pytest-qt" for
      functional testing of Qt-based Python applications. The issue here, of
      course, is that neither Portage nor any third-party overlay currently
      provide "pytest-xfvb", implying that we'll need to produce an ebuild.
      See the official GitHub repository at:
          https://github.com/The-Compiler/pytest-xvfb

* Unit tests, including:

  * test_dirs_recurse_subdirnames, validating all **non-data subdirectories**
    (i.e., subdirectories containing only pure-Python) of *all* top-level
    package directories of this project contain the ``__init__.py`` script.
  * A unit test ensuring that both of the following programmatically generated
    files are synchronized against their source files:

    * ``betse/data/py/betsee_rc.py`` from ``betse/data/qrc/betsee.qrc``.
    * ``betse/data/py/betsee_ui.py`` from ``betse/data/ui/betsee.ui``.
    
    To do so, we'll need to generalize the existing :mod:`betsee.gui.guicache`
    submodule to provide public testers permitting this test to trivially test
    for desynchronization. See *FIXME:* comments at the head of that file.
