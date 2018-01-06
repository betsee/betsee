#!/usr/bin/env python3
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level :mod:`QSettings`-based application-wide slottable settings classes.
'''

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QObject, Slot
from betse.util.io.log import logs
from betse.util.type.types import type_check
from betsee.gui.window.guimainwindow import QBetseeMainWindow
from betsee.util.io import guisettings

# ....................{ CLASSES                            }....................
class QBetseeSettings(QObject):
    '''
    :class:`QSettings`-based object exposing all application-wide settings with
    cross-platform, thread- and process-safe slots permitting external callers
    to request restoration and storage of these settings to and from their
    on-disk backing store (e.g., an application- and user-specific dotfile).

    Attributes
    ----------
    _main_window : QBetseeMainWindow
        Main window for this application.

    See Also
    ----------
    :class:`betsee.gui.guisignal.QBetseeSignaler`
        Sibling class, whose signals are connected to this object's slots.
    '''

    # ..................{ INITIALIZERS                       }..................
    @type_check
    def __init__(self, main_window: QBetseeMainWindow, *args, **kwargs) -> None:
        '''
        Initialize this slotter, connecting each slot to the corresponding
        signal of the :class:`QBetseeSettingsSignaler` instance owned by the
        passed main window widget.

        Parameters
        ----------
        main_window : QBetseeMainWindow
            Initialized application-specific parent :class:`QMainWindow` widget
            against which to initialize this object.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Classify all remaining parameters.
        self._main_window = main_window

        # Signaler owned by this window.
        signaler = self._main_window.signaler

        # Connect this signaler to this slotter.
        signaler.restore_settings_signal.connect(self.restore_settings)
        signaler.store_settings_signal.connect(self.store_settings)

    # ..................{ SLOTS                              }..................
    #FIXME: This should be called:
    #
    #* By the QGuiApplication::saveStateRequest() slot, which Qt triggers on
    #  the current desktop session manager beginning a restoration from a prior
    #  shutdown or suspend.
    @Slot()
    def restore_settings(self) -> None:
        '''
        Read and restore application-wide settings previously written to a
        predefined application- and user-specific on-disk file by the most
        recent execution of this application if any *or* reduce to a noop.
        '''

        #FIXME: Excise this.
        # return

        # Log this restoration.
        logs.log_info('Restoring application settings...')

        # Previously written application settings.
        settings = guisettings.make()

        # Read settings specific to this main window.
        settings.beginGroup('MainWindow')

        # Restore all previously written properties of this window.
        #
        # Note that there exist numerous means of doing so. While the canonical
        # means of doing so appears to be the QMainWindow.restoreGeometry() and
        # QMainWindow.restoreState() methods, QSettings documentation explicitly
        # states that:
        #
        #     "See Window Geometry for a discussion on why it is better to call
        #      QWidget::resize() and QWidget::move() rather than
        #      QWidget::setGeometry() to restore a window's geometry."
        #
        # Sadly, the "Window Geometry" article fails to actually discuss why the
        # QWidget.resize() and QWidget.move() methods are preferable to
        # QWidget.setGeometry() with respect to the main window. We do note,
        # however, that QWidget.setGeometry() documentation cautions:
        #
        #     "Warning: Calling setGeometry() inside resizeEvent() or
        #      moveEvent() can lead to infinite recursion."
        #
        # In the absence of compelling evidence, the current approach prevails.

        #FIXME: This logic currently appears to produce a bizarrely unusable
        #window on some platforms (e.g., Ubuntu Linux), presumably due to the
        #QBetseeMainWindow.resize_full() method and hence Qt.WindowFullScreen
        #mode being fundamentally broken in some respect -- possibly due to
        #Qt 5.6.x-specific issues resolved in subsequent Qt versions. In any
        #event, this logic *MUST* be disabled for the moment.

        # If a preferred window full screen state was previously stored...
        # if settings.contains('isFullScreen'):
        #     # Previously stored window full-screen state.
        #     main_window_is_full_screen = bool(settings.value('isFullScreen'))
        #
        #     # Log this restoration.
        #     logs.log_debug(
        #         'Restoring window full-screen state "%r"...',
        #         main_window_is_full_screen)
        #
        #     # If restoring this window to a full-screen state, do so.
        #     if main_window_is_full_screen:
        #         self._main_window.resize_full()

        # If a preferred window position was previously stored...
        if settings.contains('pos'):
            # Previously stored window position.
            main_window_position = settings.value('pos')

            # Log this restoration.
            logs.log_debug(
                'Restoring window position %r...', main_window_position)

            # Restore this position.
            self._main_window.move(main_window_position)
        # Else, position this window at the origin -- ensuring that subsequently
        # maximizing this window consumes all available screen space.
        else:
            self._main_window.move(0, 0)

        # If a preferred window size was previously stored...
        if settings.contains('size'):
            # Previously stored window size.
            main_window_size = settings.value('size')

            # Log this restoration.
            logs.log_debug('Restoring window size %r...', main_window_size)

            # Restore this size.
            self._main_window.resize(main_window_size)
        # Else, expand this window to consume all available screen space in a
        # non-"full screen" manner. Failing to do so often results in Qt
        # defaulting this window to an inappropriate size for the current
        # screen. On my 1920x1080 display, for example, the default window size
        # exceeds the vertical resolution (and hence is clipped at the bottom)
        # but consumes only two-thirds of the horizontal resolution.
        else:
            self._main_window.resize_max()

        # Cease reading settings specific to this window.
        settings.endGroup()


    #FIXME: This should be called:
    #
    #* Ideally incrementally during the application life cycle to prevent
    #  settings from being lost if the application fails to close gracefully.
    #  "QTimer" is probably our friends, here.
    #* By the QGuiApplication::commitDataRequest() slot, which Qt triggers on
    #  the current desktop session manager beginning a shutdown or suspend.
    #  However, note that:
    #  * This slot will also need to save unsaved data if any and that no
    #    interactive message box should be displayed to the user *UNLESS* this
    #    session manager explicitly permits such interaction. (Sigh.)
    #  * The QGuiApplication.setFallbackSessionManagementEnabled(False) method
    #    will need to be called to prevent fallback session management from
    #    interfering with this slot's behaviour.
    #  * Any concurrent operations (e.g., simulation running) will need to be
    #    temporarily halted until this application is restored. Failure to do so
    #    typically results in the OS killing this application. (Makes sense.) To
    #    respond to this application state change in a robust manner, it will
    #    probably be necessary to connect to the
    #    QGuiApplication::applicationStateChanged() slot.
    @Slot()
    def store_settings(self) -> None:
        '''
        Write application-wide settings to a predefined application- and
        user-specific on-disk file, which the next execution of this application
        will read and restore on startup.
        '''

        # Log this storage.
        logs.log_info('Storing application settings...')

        # Currently written application settings if any.
        settings = guisettings.make()

        # Write settings specific to this main window.
        settings.beginGroup('MainWindow')

        # Current window full-screen state, position, and size.
        main_window_is_full_screen = self._main_window.isFullScreen()
        main_window_position = self._main_window.pos()
        main_window_size = self._main_window.size()

        # Log these window properties.
        logs.log_debug('Storing window full-screen state "%r"...',
                       main_window_is_full_screen)
        logs.log_debug('Storing window position %r...', main_window_position)
        logs.log_debug('Storing window size %r...', main_window_size)

        # Store these window properties.
        settings.setValue('isFullScreen', main_window_is_full_screen)
        settings.setValue('pos', main_window_position)
        settings.setValue('size', main_window_size)

        # Cease writing settings specific to this window.
        settings.endGroup()
