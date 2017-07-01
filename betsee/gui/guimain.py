#!/usr/bin/env python3
# Copyright 2017 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Root-level classes defining this application's graphical user interface (GUI).
'''

#FIXME: To simplify future localization efforts, all human-readable strings to
#be displayed should be filtered through the Qt tr() or translate() methods.
#Note that the external "pyside2-lupdate" command will probably need to be
#called to convert raw translation files into importable Python modules. For
#further details, see the following PySide-specific articles:
#
#* "Internationalisation of PyQt5 Applications." (Superb article.
#  Unsurprisingly, this is the canonical resource for PySide translations, which
#  conforms to the exact same API and hence suffers similar issues.)
#  http://pyqt.sourceforge.net/Docs/PyQt5/i18n.html
#* "Internationalizing PySide programs." (Crude ELI5 on PySide translations.
#  Insufficient in many respects, but a tolerable introduction to the subject.)
#  https://wiki.qt.io/PySide_Internationalization
#
#Generic Qt articles pertaining to this topic additionally include:
#
#* "Writing Source Code for Translation." (Superb "Qt Assistant" article.)
#* "Qt Linguist Manual: Translators." (Useful "Qt Linguist" usage instructions.)
#  https://doc.qt.io/qt-5/linguist-translators.html
#FIXME: Sadly, the behaviour of the "pyside2-lupdate" command is fairly awkward.
#Unlike the remainder of the PySide2 ecosystem, this command requires a ".pro"
#file whose syntax appears to superficially resemble that of traditional *nix
#makefiles. In turn, this file requires the absolute or relative path to the
#Python... *WAIT.* No, all is well. The ".pro" support is largely vestigial and
#only required for projects *NOT* already providing one or more ".ui" files.
#Fortunately, "pyside2-lupdate" supports both. *WAIT.* O.K.; so, we'll have
#translatable strings residing in:
#
#* Our ".ui" files. These files are guaranteed to be convertible into ".ts"
#  files which may then be translated via the "Qt Linguist" GUI, like so:
#
#    pyside2-lupdate \
#        ~/py/betsee/data/ui/betsee.ui -ts \
#        ~/py/betsee/data/ts/en_US.ts \
#        ~/py/betsee/data/ts/ru_RU.ts   # ...and so on for all needed languages.
#
#* All ".py" files under the ~/py/betsee/betsee/gui/ directory that may contain
#  dynamic calls to the tr() and translate() methods. In theory, these files
#  should also be convertible into ".ts" files which may then be translated via
#  the "Qt Linguist" GUI by recursively finding all such files in pure-Python
#  and then passing the absolute paths of these files in the same manner:
#
#    pyside2-lupdate \
#        ~/py/betsee/betsee/gui/guimain.py \    # ...and so on, recursively.
#        ~/py/betsee/betsee/gui/widget/guimainwindow.py \
#        -ts \
#        ~/py/betsee/data/ts/en_US.ts \
#        ~/py/betsee/data/ts/ru_RU.ts   # ...and so on for all needed languages.
#
#  If passing ".py" files directly to "pyside2-lupdate" fails, we'll then need
#  to dynamically generate (and probably cache) a ".pro" file listing the paths
#  of these files, which may then be passed to "pyside2-lupdate" directly. See
#  "pyside2-lupdate --help" for a terse usage synopsis.
#
#Note that ".ts" files are *NOT* usable as is by Qt and hence by PySide2. Such
#files are only intended to be consumed and modified by the "Qt Linguist" GUI.
#Qt and hence PySide2 requires ".ts" files be converted to corresponding ".qm"
#(i.e., [Q]t [M]essage) files by either:
#
#* Manually selecting "File" -> "Release" in the "Qt Linguist" GUI.
#* Programmatically running the "lrelease" command.
#
#Naturally, we overwhelmingly prefer the latter approach -- or we would, at
#least, if the "lrelease" command were distributed as a mandatory core Qt
#component. It's not, which admittedly makes sense. While most Linux
#distributions do provide "lrelease" packages, there's little sense in adding
#yet another runtime dependency to this application... Hmm. Or maybe there is?
#
#O.K., I fully admit: I strongly prefer programmatically running the "lrelease"
#command at runtime and caching the resulting ".qm" files into
#"~/.betse/betsee/qm/" (e.g., "~/.betse/betsee/qm/en_US.qm"). Since translations
#are technically optional, we should simply make "lrelease" an optional
#dependency. Specifically:
#
#* If the "lrelease" command is pathable, the ".qm" target file specific to the
#  current system local should be automatically generated from the corresponding
#  ".ts" source file and cached into the "~/.betse/betsee/qm/" subdirectory.
#* Else, translations are ignored and a non-fatal warning should be issued.
#
#Assuming ".qm" files to be generated and cached in this fashion, we should then
#be able to leverage application-wide translations by adding the following
#initialization functionality to our existing "betsee.util.psdapp" submodule:
#
#    from PySide2.QtCore import QLocale, QTranslator
#
#    app_translator = QTranslator()
#
#    # Obviously, replace "~/.betse/betsee/qm" with the corresponding metadata.
#    #
#    # Perhaps more importantly, this should be strictly optional. Hence, any
#    # exception raised by this call should be converted into a non-fatal logged
#    # warning or (probably) error message. Does Qt provide a means beforehand
#    # of testing whether this ".qm" file exists? I suppose we can just manually
#    # concatenate this file's absolute path ourselves and test for the
#    # existance of this file. Hey, whatever works -- right?
#    app_translator.load(QLocale.system().name(), "~/.betse/betsee/qm")
#
#    APP_GUI.installTranslator(app_translator)
#
#There exists one last minefield: the QObject.tr() versus
#QCoreApplication::translate() split. Basically:
#
#* The QObject.tr() instance method provides a more convenient interface that
#  (unfortunately) is broken by design.
#* QCoreApplication::translate() class method provides a less convenient
#  interface that actually behaves as intended.
#
#Riverbank themselves strongly recommend that QCoreApplication::translate()
#rather than QObject.tr() *ALWAYS* be called. For example, see
#http://pyqt.sourceforge.net/Docs/PyQt5/i18n.html:
#
#"The PyQt5 behaviour is unsatisfactory and may be changed in the future. It is
# recommended that translate() be used in preference to tr(). This is guaranteed
# to work with current and future versions of PyQt5 and makes it much easier to
# share message files between Python and C++ code."
#
#PySide2 is, of course, no different. To compound matters, the "pyside2-lupdate"
#command appears to have difficulty properly associating QObject.tr() calls with
#their appropriate context. For example, see this StackOverflow response:
#    https://stackoverflow.com/a/41174550/2809027
#
#tl;dr
#=====
#Always call QCoreApplication::translate(). To do so, a minimal-length example:
#
#    from QtCore import QCoreApplication
#
#    class MuhObject(QtCore.QObject):
#        def hello(self):
#            return QCoreApplication.translate('MuhObject', 'Muh hello world!')
#
#Hence, calling QCoreApplication.translate requires that the first parameter be
#the explicit name of the desired context -- which, for parity with C++, should
#*ALWAYS* be the name of the custom class performing this call.
#
#Annnnnnd we are done.

# ....................{ IMPORTS                            }....................
from betse.util.io.log import logs
from betsee.gui import guicache

# Importing from this submodule has a substantial side effect: specifically, the
# the "QApplication" singleton is instantiated and assigned to this module
# global. All subsequent logic may safely assume this singleton to exist.
from betsee.util.psdapp import APP_GUI

# ....................{ CLASSES                            }....................
class BetseeGUI(object):
    '''
    Graphical user interface (GUI) for this application, doubling as both the
    main window and root Qt widget for this application.

    Attributes
    ----------
    _main_window : QBetseeMainWindow
        Main window widget for this GUI.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Generate all modules required at runtime by this GUI.
        guicache.cache_py_files()

    # ..................{ RUNNERS                            }..................
    def run(self) -> int:
        '''
        Run this GUI's main event loop and display this GUI.

        Returns
        ----------
        int
            Exit status of this event loop as an unsigned byte.
        '''

        # Main window Qt widget class for this application. Since this class
        # subclasses the custom user interface (UI) base class defined by a
        # module generated at runtime above, this importation is deferred until
        # *AFTER* this module is guaranteed to be importable.
        from betsee.gui.widget.guimainwindow import QBetseeMainWindow

        # Log this initialization.
        logs.log_info('Initiating PySide2 UI...')

        # Main window widget for this GUI.
        #
        # For safety, this window is scoped to an instance rather than global
        # variable, ensuring that this window is destroyed before the root Qt
        # application widget containing this window,
        self._main_window = QBetseeMainWindow()

        # Log this display.
        logs.log_info('Displaying PySide2 UI...')

        # Run this GUI's event loop and propagate the resulting exit status to
        # our caller. This displays this window and thus all of this GUI.
        return APP_GUI.exec_()
