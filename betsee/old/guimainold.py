#!/usr/bin/env python3
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
To use a resource file exported by Qt Designer, convert this file to Python
3-compatible PySide2 code as follows: e.g.,

    # What is the name of the PySide2 "rcc" command, actually? Investigate.
    $ pyside2-rcc resources.qrc -o resources_rc.py

The file must be named "resources_rc.py" and reside in the same directory as
"betsee.ui".
'''

#FIXME: To simplify future localization efforts, all human-readable strings to
#be displayed should be filtered through the Qt translate() function.

#FIXME: A huge issue is that, because we need to use Qthread and emit signals
#back to our GUI objects, our message box does not play well with anything
#that's going to report something to the Terminal (e.g. print or betse log
#info, exceptions, etc.) while in any thread. Therefore, we need to think of a
#work around that will let us use the GUI message box to receive messages from
#the Terminal. At present, this functionality is totally disabled, and the GUI
#message box is simply receiving emitted string messages from within the
#threads.

# ....................{ IMPORTS                            }....................
import os, sys, time
import numpy as np
from PySide2.uic import loadUiType
from PySide2.QtWidgets import QApplication, QFileDialog, qApp
from PySide2.QtCore import QMutex, QMutexLocker, QThread, pysideSignal
from betse import ignition, pathtree
from betse.science import filehandling as fh
from betse.science.config import confdefault
from betse.science.parameters import Parameters
from betse.science.sim import Simulator
from betse.science.tissue.handler import TissueHandler
from betse.science.visual.plot import plotutil as pu
# from betse.util.io.log import logs
from betse.util.path import files, pathnames
from collections import OrderedDict
from matplotlib import rcParams
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.figure import Figure

# ....................{ GLOBALS                            }....................
#FIXME: PySide and hence presumably PySide2 as well lacks an analogue to the
#loadUiType() function. To circumvent this, consider defining our own
#loadUiType() function performing the equivalent thereof. This is low-hanging
#fruit. Since doing so on every GUI startup is presumably inefficient, however,
#this should also be improved in the long-term to perform caching: namely,
#
#* On the first execution of the GUI:
#  1. Convert the UI file referenced below into in-memory Python code.
#  2. Convert that code into a Python file, presumably cached in the current
#     dot directory for BETSE (e.g., "~/.betse/").
#* On all subsequent executions of the GUI:
#  1. Compare the time stamps of this UI file and this cached Python file.
#  2. If the time stamps are the same, reuse the latter as is.
#  3. Else, recreate the latter as above and use the newly cached file.
#
#For relevant code doing the first part above under PySide and Python 2.7, see:
#    https://gist.github.com/mstuttgart/bc246b25b8e0f7edd743
#FIXME: Set the absolute path of this UI file in a new "betsee.pathtree" module.
Ui_MainWindow, QMainWindow = loadUiType('betsee.ui')

# ....................{ CLASSES                            }....................
class Main(QMainWindow, Ui_MainWindow):
    '''
    Root Qt widget for this application.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        #FIXME: All of the following functionality should be wrapped in an
        #exception handler embedding error messages in modal dialog widgets.
        #Google is presumably our friend, here.

        # Prepare the BETSE codebase for subsequent use.
        ignition.ignite()

        self.setupUi(self)

        self.fig_dict_seed = OrderedDict({})    # dictionary holds matplotlib figures, relevant to seed, by name
        self.fig_dict_init = OrderedDict({})    # dictionary holds matplotlib figures, relevant to init, by name
        self.fig_dict_sim = OrderedDict({})     # dictionary holds matplotlib figures, relevant to sim, by name

        rcParams.update({'font.size': 14})  # FIXME this should be user-defined

        # initialize the phase and property tracker:
        self.phase_and_property_tracker()

        # define the main activities for the GUI controls:
        self.actions_handler()

        # initialize null canvas objects for plottting in seed, init and sim viewers:
        self.canvas_seed = None
        self.canvas_init = None
        self.canvas_sim = None

        self.seed_fname = None
        self.init_fname = None
        self.sim_fname = None

        # set up the message box:
        self.messageBox.setReadOnly(True)

        # set up the project tree and stacked-widget panels:
        self.initialize_project_tree()



    def initialize_project_tree(self):
        """
        Defines the tree item to stacked widget page index mapping
        required to work with the project tree.
        """

        # set up the Tree-to-StackedWidget page turning dictionary:
        self.tree_dict = {}
        self.tree_dict['File Management'] = 0
        self.tree_dict['Time Settings'] = 1
        self.tree_dict['General Options'] = 2
        self.tree_dict['Cluster Options'] = 3

        self.tree_dict['Tissue Profiles'] = 4
        self.tree_dict['+Add Profile'] = 4

        self.tree_dict['Channels'] = 5
        self.tree_dict['+Add Channel'] = 5

        self.tree_dict['Interventions'] = 6
        self.tree_dict['+Add Intervention'] = 6

        self.tree_dict['Junctions'] = 7
        self.tree_dict['Networks'] = 8
        self.tree_dict['Extra Physics'] = 9
        self.tree_dict['Tools'] = 10
        self.tree_dict['Advanced'] = 11
        self.tree_dict['Results Settings'] = 12

        self.tree_dict['Raw Data Export'] = 13
        self.tree_dict['+Add CSV Export'] = 13

        self.tree_dict['Line Plots'] = 14
        self.tree_dict['+Add Line Plot'] = 14

        self.tree_dict['2D Plots'] = 15
        self.tree_dict['+Add 2D Plot'] = 15

        self.tree_dict['Animations'] = 16
        self.tree_dict['+Add Animation'] = 16

        self.tree_dict['Substances'] = 17
        self.tree_dict['+Add Substance'] = 17

        self.tree_dict['Reactions'] = 18
        self.tree_dict['+Add Reaction'] = 18

        self.tree_dict['Transporters'] = 19
        self.tree_dict['+Add Transporter'] = 19

        self.tree_dict['Channels'] = 20
        self.tree_dict['+Add Channel (Network)'] = 20

        self.tree_dict['Modulators'] = 21
        self.tree_dict['+Add Modulator'] = 21


    def actions_handler(self):
        """
        Defines all signals and slots connections used in the GUI in one
        whopping spaghetti pile!
        """

        #---------Actions-----------------------------------------------------------------------------------------------

        # load config action loads a previously created config file:
        # (active in menu and toobar)
        self.actionLoad_Config_File.triggered.connect(self.load_config)

        # save the GUI-modified config file to (a potentially new) filename or path:
        # (active in menu and toobar)
        self.actionSave_Config_File.triggered.connect(self.save_config)

        # allows the user to build a new config file with default settings in the path of their choice
        # (active in menu and toobar)
        self.actionNew_Config_File.triggered.connect(self.new_config)

        #-------Setting up the Tree Widget clicks to Stacked Widget Page Changes----------------------------------------
        self.treeWidget.itemClicked.connect(self.change_page)
        self.treeWidget.itemDoubleClicked.connect(self.new_page)

        #-------Minor user selection signals/slots----------------------------------------------------------------------

        # quit BETSE muGUI:
        # (active in file menu only)
        self.actionExit.triggered.connect(qApp.quit)

        # allow user to select a bitmap for the clipping profile (not tested for png image type!):
        self.pushButton_clippingBrowse.clicked.connect(self.select_clippingBitmap)

        # allow user to select an "extra config file" to run as the network:
        self.pushButton_netBrowse.clicked.connect(self.select_networkConfig)

        # manage the "seed lock" control, which greys out parts of Options Panels that break init/sim compatibility
        # with the seed if they're edited:
        self.rb_lockSeed.clicked.connect(self.manage_seed_lock)

        #----Plot viewer controls---------------------------------------------------------------------------------------

        # plotting controls, allowing user to change the plot that appears in the viewpoint, selecting from a list
        # of available choices:
        self.comboBox_seedPlots.activated.connect(self.changePlotSeed)
        self.lineEdit_seedColormap.editingFinished.connect(self.change_seed_plot_settings)

        self.comboBox_initPlots.activated.connect(self.changePlotInit)
        self.radioButton_initAutoscale.clicked.connect(self.toggle_initAutoscale)

        self.comboBox_simPlots.activated.connect(self.changePlotSim)
        self.radioButton_simAutoscale.clicked.connect(self.toggle_simAutoscale)

        #----Message logger---------------------------------------------------------------------------------------------
        # FIXME due to Qt issues, the following logger set up and QLogger class can't receive messages directly from
        # the Terminal when a terminal message is issued from inside a thread...

        # initialize and start the logger, which reports Terminal messages at the "info" level:
        # self.log_handler = QLogger(self.messageBox)
        # self.log_handler.setLevel(20)                   # set level of the handler's message reporting
        # logging.getLogger().addHandler(self.log_handler)

        # Initiate the Consol window with some happy greeting:
        self.write_message_to_box("Welcome to BETSE v0.5")
        self.write_message_to_box("------------------------------------")
        self.write_message_to_box("                     ")

        #---------------------------------------------------------------------------------------------------------------
        #   THREADING
        #---------------------------------------------------------------------------------------------------------------

        #---Seeds-------------------------------------------------------------------------------------------------------

        # Define thread for running a seed:
        self.seedRun = SeedThread()

        # Define the two ways users can start a seed run:
        self.pushButton_startSeed.clicked.connect(self.seedRun.start)
        self.actionRun_Seed.triggered.connect(self.seedRun.start)

        # if seed pushButton connected, stop the seed:
        self.pushButton_stopSeed.clicked.connect(self.seedRun.stop)

        # allow the seed to report to the BETSE Consol message box:
        self.seedRun.emit_message.connect(self.write_message_to_box)

        # allow the seed to talk to the progress bar:
        self.seedRun.emit_progress.connect(self.set_seed_progress)

        # these signals prevent user from trying to run another seed, init or sim while seed thread is running,
        # but unlock the controls when the seed thread finishes:
        self.seedRun.emit_controlLock_startSeed.connect(self.lock_seed_start)
        self.seedRun.emit_controlUnLock_startSeed.connect(self.unlock_seed_start)
        self.seedRun.emit_controlLock_init.connect(self.lock_init_controls)
        self.seedRun.emit_controlUnLock_init.connect(self.unlock_init_controls)
        self.seedRun.emit_controlLock_sim.connect(self.lock_sim_controls)
        self.seedRun.emit_controlUnLock_sim.connect(self.unlock_sim_controls)
        self.seedRun.emit_controlUnlock_play.connect(self.unlock_play_button)

        # allow the seed Thread to report if it completed successfully, and do follow ups:
        self.seedRun.mission_completed.connect(self.completed_successful_seed_run)

        # Inits--------------------------------------------------------------------------------------------------------

        # Define thread for running an init:
        self.initRun = InitThread()

        self.pushButton_startInit.clicked.connect(self.initRun.start)

        self.pushButton_stopInit.clicked.connect(self.initRun.stop)

        self.initRun.emit_message.connect(self.write_message_to_box)

        # allow the init to talk to the progress bar:
        self.initRun.emit_progress.connect(self.set_init_progress)

        # these signals prevent user from trying to run another init, or a seed/sim while init thread is running,
        # but unlock the controls when the init thread finishes:
        self.initRun.emit_controlLock_startInit.connect(self.lock_init_start)
        self.initRun.emit_controlUnLock_startInit.connect(self.unlock_init_start)
        self.initRun.emit_controlLock_seed.connect(self.lock_seed_controls)
        self.initRun.emit_controlUnLock_seed.connect(self.unlock_seed_controls)
        self.initRun.emit_controlLock_sim.connect(self.lock_sim_controls)
        self.initRun.emit_controlUnLock_sim.connect(self.unlock_sim_controls)

        # allow the init Thread to report if it completed successfully, and do follow ups:
        self.initRun.mission_completed.connect(self.completed_successful_init_run)

        # Sims---------------------------------------------------------------------------------------------------------

        # Define simulation thread:
        self.simRun = SimThread()

        self.pushButton_startSim.clicked.connect(self.simRun.start)
        self.actionRun_Sim.triggered.connect(self.simRun.start)

        self.pushButton_stopSim.clicked.connect(self.simRun.stop)

        self.simRun.emit_message.connect(self.write_message_to_box)

        # allow the sim to talk to the progress bar:
        self.simRun.emit_progress.connect(self.set_sim_progress)

        # these signals prevent user from trying to run another sim, or a seed/init while sim thread is running,
        # but unlock the controls when the sim thread finishes:
        self.simRun.emit_controlLock_startSim.connect(self.lock_sim_start)
        self.simRun.emit_controlUnLock_startSim.connect(self.unlock_sim_start)

        self.simRun.emit_controlLock_seed.connect(self.lock_seed_controls)
        self.simRun.emit_controlUnLock_seed.connect(self.unlock_seed_controls)

        self.simRun.emit_controlLock_init.connect(self.lock_init_controls)
        self.simRun.emit_controlUnLock_init.connect(self.unlock_init_controls)


        # allow the sim Thread to report if it completed successfully, and do follow ups:
        self.simRun.mission_completed.connect(self.completed_successful_sim_run)


        # Stop all threads---------------------------------------------------------------------------------------------

        # action to cancel any worker threads related to simulation:
        self.actionStop_Phase.triggered.connect(self.cancel_worker_threads)

    def phase_and_property_tracker(self):

        """
        Keeps track of p, cells, init and sim that have been loaded or run in the GUI

        """

        self.valid_seed_present = False
        self.valid_init_present = False
        self.valid_sim_present = False

#-----------------------------------------------------------------------------------------------------------------------
    def change_page(self, ii):

        tname = ii.text(0)

        indy = self.tree_dict.get(tname, None)

        if indy is not None:

            self.stackedWidget.setCurrentIndex(indy)

        # self.stackedWidget.setCurrentIndex(ii)


    def new_page(self, ii):

        pass

        # tname = ii.text(0)
        #
        # stro = tname + "_HappyCat!"
        #
        # qti = QTreeWidgetItem(25)
        # qti.setText(25, stro)
        #
        # self.treeWidget.addTopLevelItem(qti)

# loading pre-run seed, init and sims----------------------------------------------------------------------------------

    def load_config(self):
        """
        Allows user to select a config file from their system, populates options fields, looks for already-run
        seed, init and/or sim and creates plots if they exist.

        """

        self.config_name = QFileDialog.getOpenFileName(self, 'Open file', pathtree.get_home_dirname())[0]

        # if a file is selected:
        if self.config_name:  # FIXME we need validations that the loaded objects are true to (BETSE config yaml) type!

            self.config_Fname = pathnames.get_basename(self.config_name)

            # set the save name of the config file to the selected filename
            self.lineEdit_configFname.setText(str(self.config_Fname))

            self.write_message_to_box("Loading selected config file.")
            self.write_message_to_box("                     ")

            self.p = Parameters(config_filename=self.config_name)

            # prepopulate the options forms with settings from this config:
            self.write_message_to_box("Populating Options Panels with selected config file information.")
            self.write_message_to_box("                     ")

            self.prepopulate()

            self.path_to_seed = pathnames.join(self.p.init_pickle_dirname, self.p.world_filename)
            self.path_to_init = pathnames.join(self.p.init_pickle_dirname, self.p.init_filename)
            self.path_to_sim = pathnames.join(self.p.sim_path, self.p.sim_filename)

            self.seedRun.set_up(self.path_to_seed, self.p)

            # Now that valid config has been loaded, unlock the seed controls:
            self.unlock_seed_controls()
            self.unlock_play_button()

            if files.is_file(self.path_to_seed):

                self.write_message_to_box("Found an existing seed file: loading and plotting.")
                self.write_message_to_box("                     ")

                self.seed_fname = self.path_to_seed
                self.load_seed()
                self.valid_seed_present = True

                # lock the seed and param controls and progress bar to 100% as we have a valid seed present:
                self.rb_lockSeed.setChecked(True)
                self.manage_seed_lock()
                self.progressBar_seed.setValue(100)

                # Let the user run an init from the seed by unlocking controls:
                self.groupBox_initControls.setEnabled(True)

                # Set the progress bar to "full" to indicate this is a completely run init:
                self.progressBar_init.setValue(100)

            if files.is_file(self.path_to_init):
                self.write_message_to_box("Found an existing init file: loading and plotting.")
                self.write_message_to_box("                     ")
                self.init_fname = self.path_to_init
                self.load_init()
                self.valid_init_present = True

                # Let the user run a sim from the init by unlocking controls:
                self.groupBox_simControls.setEnabled(True)

                # Set the progress bar to "full" to indicate this is a completely run init:
                self.progressBar_sim.setValue(100)

            if files.is_file(self.path_to_sim):
                self.write_message_to_box("Found an existing sim file: loading and plotting.")
                self.write_message_to_box("                     ")
                self.sim_fname = self.path_to_sim
                self.load_sim()
                self.valid_sim_present = True

                # Let the user run an init or sim by unlocking controls:
                self.groupBox_initControls.setEnabled(True)
                self.groupBox_simControls.setEnabled(True)

    def load_seed(self):
        """
        Allows user to select a BETSE world file from their system; plots the default seed and populates
         settings in GUI options panels.

        """

        if self.seed_fname:

            self.cells, self.p = fh.loadWorld(self.seed_fname)

            # populate the options fields of the BETSE Gui with settings from this seed:
            self.prepopulate()

            # reset the colormap in case it's changed:
            # self.p.background_cm = matplotlibs.get_colormap(self.p.config['results options']['background colormap'])
            # self.p.default_cm = matplotlibs.get_colormap(self.p.config['results options']['default colormap'])

            # Create a dummy simulation simulator:
            self.sim = Simulator(self.p)

            self.sim.baseInit_all(self.cells, self.p)
            self.sim.dyna = TissueHandler(self.sim, self.cells, self.p)
            self.sim.dyna.tissueProfiles(self.sim, self.cells, self.p)

            # run through the plotting sequence:
            self.plot_all_seed(write_to_comboBox=True)

    def load_init(self):

        """
        Allows user to select a BETSE init file from their system; plots the default seed and init, and populates
        settings in GUI options panels.

        """

        if self.init_fname:

            self.init, _, self.p = fh.loadSim(self.init_fname)

            # populate the options fields of the BETSE Gui with settings from this seed:
            self.prepopulate()

            # reset the colormap in case it's changed:
            # self.p.background_cm = matplotlibs.get_colormap(self.p.config['results options']['background colormap'])
            # self.p.default_cm = matplotlibs.get_colormap(self.p.config['results options']['default colormap'])

            # for init:
            self.plot_all_init(write_to_comboBox=True)

# options panel field population --------------------------------------------------------------------------------------

    def load_sim(self):

        """
        Allows user to select a BETSE sim file from their system; plots the default seed and init, and populates
        settings in GUI options panels.

        """

        if self.sim_fname:

            self.sim, _, self.p = fh.loadSim(self.sim_fname)

            # populate the options fields of the BETSE Gui with settings from this seed:
            self.prepopulate()

            # reset the colormap in case it's changed:
            # self.p.background_cm = matplotlibs.get_colormap(self.p.config['results options']['background colormap'])
            # self.p.default_cm = matplotlibs.get_colormap(self.p.config['results options']['default colormap'])

            # for init:
            self.plot_all_sim(write_to_comboBox=True)

# defining new default BETSE config and associated project directories; saving GUI-modified configs---------------------

    # Config specials:

    def new_config(self):

        """
        Allows the user to select a directory to define a new default BETSE config file, geo directory
        and extra_config directory, and loads the new config file into the GUI.

        """

        config_dir_name = str(QFileDialog.getExistingDirectory(self, 'Select Directory', pathtree.get_home_dirname()))


        if config_dir_name:

            # get the name of the file that will be created at in the selected directory from the line edit box:
            self.config_Fname = self.lineEdit_configFname.text()

            self.config_name = pathnames.join(config_dir_name, self.config_Fname)

            self.write_message_to_box("Selected the directory " + config_dir_name)
            self.write_message_to_box("                         ")

            confdefault.save(self.config_name)

            self.write_message_to_box("                     ")

            self.p = Parameters(config_filename=self.config_name)

            # prepopulate the options forms with settings from this config:
            self.write_message_to_box("Populating Options Panels with selected config file information.")
            self.write_message_to_box("                     ")

            self.prepopulate()

            self.path_to_seed = pathnames.join(self.p.init_pickle_dirname, self.p.world_filename)
            self.path_to_init = pathnames.join(self.p.init_pickle_dirname, self.p.init_filename)
            self.path_to_sim = pathnames.join(self.p.sim_path, self.p.sim_filename)

            # Set up the threads with necessary information:
            self.seedRun.set_up(self.path_to_seed, self.p)

            # Now that valid init has been loaded, unlock the seed controls:
            self.unlock_seed_controls()
            self.unlock_play_button()

    def save_config(self):
        """
        Allows the user to select a directory and specify filename to save GUI-altered config
        settings.

        """

        self.write_message_to_box("Saving config files are not yet ready for action!")

# options panel field population --------------------------------------------------------------------------------------

    def prepopulate(self):

        """
        Prepopulates available fields of the GUI with config file data.

        """

        # Make the BETSE-specific cache directories if they're not found.
        betse_init_dir = os.path.expanduser(self.p.init_pickle_dirname)
        os.makedirs(betse_init_dir, exist_ok=True)

        betse_sim_dir = os.path.expanduser(self.p.sim_path)
        os.makedirs(betse_sim_dir, exist_ok=True)

        betse_results_init_dir = os.path.expanduser(self.p.init_results)
        os.makedirs(betse_results_init_dir, exist_ok=True)

        betse_results_sim_dir = os.path.expanduser(self.p.sim_results)
        os.makedirs(betse_results_sim_dir, exist_ok=True)

        # Define data paths for saving an initialization and simulation run: -----------------------------------------
        self.savedWorld = os.path.join(betse_init_dir, self.p.world_filename)
        self.savedInit = os.path.join(betse_init_dir, self.p.init_filename)
        self.savedSim = os.path.join(betse_sim_dir, self.p.sim_filename)

        self.lineEdit_seedfile.setText(self.savedWorld)
        self.lineEdit_initfile.setText(self.savedInit)
        self.lineEdit_simfile.setText(self.savedSim)
        self.lineEdit_initresults.setText(self.p.init_results)
        self.lineEdit_simresults.setText(self.p.sim_results)

        # Define data paths for init and sim time settings:-------------------------------------------------------
        self.lineEdit_initTimeStep.setText(str(self.p.config['init time settings']['time step']))
        self.lineEdit_initTotalTime.setText(str(self.p.config['init time settings']['total time']))
        self.lineEdit_initSampling.setText(str(self.p.config['init time settings']['sampling rate']))

        self.lineEdit_simTimeStep.setText(str(self.p.config['sim time settings']['time step']))
        self.lineEdit_simTotalTime.setText(str(self.p.config['sim time settings']['total time']))
        self.lineEdit_simSampling.setText(str(self.p.config['sim time settings']['sampling rate']))


        # Fill in General Options:--------------------------------------------------------------------------------

        self.spinBox_gridSize.setValue(int(self.p.grid_size))

        self.rb_simECM.setChecked(bool(self.p.sim_ECM))

        if self.p.ion_profile == 'basic':

            indo = self.comboBox_ionProfile.findText('Basic')

        elif self.p.ion_profile == 'basic_Ca':

            indo = self.comboBox_ionProfile.findText('Basic Ca')

        elif self.p.ion_profile == 'animal':

            indo = self.comboBox_ionProfile.findText('Animal')

        elif self.p.ion_profile == 'customized':

            indo = self.comboBox_ionProfile.findText('Custom')

        else:
            indo = 0

        self.comboBox_ionProfile.setCurrentIndex(indo)

        #-----Seed (World) Options-----------------------------------------------------------------------
        self.lineEdit_worldSize.setText(str(self.p.wsx))
        self.lineEdit_cellR.setText(str(self.p.rc))

        if self.p.lattice_type == 'hex':
            ii = self.comboBox_latticeType.findText('Hexagonal')

        elif self.p.lattice_type == 'rect':

            ii = self.comboBox_latticeType.findText('Rectangular')

        else:
            ii = 0

        self.comboBox_latticeType.setCurrentIndex(ii)

        self.dsb_latticeDisorder.setValue(float(self.p.nl))


        #-----Tissue Profiles ----------------------------------------------------------------------
        useprof = bool(self.p.config['tissue profile definition']['profiles enabled'])

        self.rb_useProfiles.setChecked(useprof)


        self.clippingBitmapFilename =  os.path.join(self.p.config_dirname,
                                            self.p.config['tissue profile definition']['clipping']['bitmap']['file'])

        self.lineEdit_ClippingBitmap.setText(self.clippingBitmapFilename)


        #-----Dynamic Channels----------------------------------------------------------------------------

        #-----Interventions-------------------------------------------------------------------------------

        #-----Junctions-----------------------------------------------------------------------------------

        self.lineEdit_GJsa.setText(str(self.p.gj_surface))

        self.rb_vsGJ.setChecked(bool(self.p.gj_flux_sensitive))

        self.lineEdit_VthreshGJ.setText(str(self.p.gj_vthresh))

        self.dsb_GJmin.setValue(float(self.p.gj_min))

        self.lineEdit_TJscale.setText(str(self.p.D_tj))

        self.lineEdit_adherens.setText(str(self.p.D_adh))


        #------Network------------------------------------------------------------------------------------

        if self.p.grn_enabled:

            self.rb_useNetwork.setChecked(True)
            self.comboBox_netType.setCurrentIndex(0)
            self.lineEdit_NetConfig.setText(str(self.p.grn_config_filename))

            # FIXME need to inhibit network optimizer from running, same for plots

        elif self.p.metabolism_enabled:

            self.rb_useNetwork.setChecked(False)
            self.comboBox_netType.setCurrentIndex(1)
            self.lineEdit_NetConfig.setText(str(self.p.metabo_config_filename))

            # FIXME need to inhibit network optimizer from running, same for plots


        # self.rb_plotNetwork
        #
        # self.rb_runOptimizer



        #------Additional Physics------------------------------------------------------------------------

        self.rb_eosmoPC.setChecked(bool(self.p.sim_eosmosis))

        self.rb_flow.setChecked(bool(self.p.fluid_flow))

        self.rb_deform.setChecked(bool(self.p.deformation))

        self.rb_osmosis.setChecked(bool(self.p.deform_osmo))

        self.rb_dynNoise.setChecked(bool(self.p.dynamic_noise))

        # self.p.dynamic_noise_level

        self.dsb_staticNoise.setValue(float(self.p.channel_noise_level))


        #------Tools and Functions-----------------------------------------------------------------------

        self.rb_Goldman.setChecked(bool(self.p.GHK_calc))


        #------Advanced Settings-------------------------------------------------------------------------

        self.lineEdit_NaKATPaseMax.setText(str(self.p.alpha_NaK))

        self.lineEdit_CaATPaseMax.setText(str(self.p.alpha_Ca))

        self.dsb_gaussian.setValue(float(self.p.smooth_level))

        self.rb_smoothConcs.setChecked(bool(self.p.smooth_concs))

        self.rb_subsVmem.setChecked(bool(self.p.substances_affect_charge))

        self.dsb_timeAccel.setValue(float(self.p.gj_acceleration))

        #------Results------------------------------------------------------------------------------------

        # self.rb_autosavePlots
        #
        # self.rb_enableAni
        #
        # self.rb_showCells
        #
        # self.rb_enumerateCells
        #
        # self.rb_IOverlay
        #
        # self.sb_plotCell

        # Seed Control Panel options----------------------------------------------------------------------
        self.lineEdit_seedColormap.setText(self.p.config['results options']['background colormap'])

        # Init Control Panel options
        self.lineEdit_initColormap.setText(self.p.config['results options']['default colormap'])

        # Sim Control Panel options
        self.lineEdit_simColormap.setText(self.p.config['results options']['default colormap'])

# helper functions to manipulate plots on the viewer window------------------------------------------------------------

    def addPlotSeed(self, fig):
        """
        Adds a plot to the "Seed" viewing window of the BETSE GUI

        Parameters
        ------------
        fig: matplotlib figure object

        """
        self.canvas_seed = FigureCanvas(fig)
        self.mplVLayout_seed.addWidget(self.canvas_seed)
        self.canvas_seed.draw()
        self.toolbar_seed = NavigationToolbar(self.canvas_seed, self.mplWindow_seed, coordinates=True)
        self.mplVLayout_seed.addWidget(self.toolbar_seed)

    def removePlotSeed(self,):
        """
        Removes a plot from the "Seed" viewing window of the BETSE GUI.

        """

        self.mplVLayout_seed.removeWidget(self.canvas_seed)
        self.canvas_seed.close()
        self.mplVLayout_seed.removeWidget(self.toolbar_seed)
        self.toolbar_seed.close()

    def changePlotSeed(self):
        """
        Changes a figure in the "Seed" viewing window of the BETSE GUI, given a switch to a new item in the plot
        combo box.

        Parameters
        -----------
        item: signal from a mouse-click event on a QT GUI item with a text label.

        """

        item = self.comboBox_seedPlots.currentText()
        self.removePlotSeed()
        self.addPlotSeed(self.fig_dict_seed[item])

    def addPlotInit(self, fig):
        """
        Adds a plot to the "Init" viewing window of the BETSE GUI

        Parameters
        ------------
        fig: matplotlib figure object

        """
        self.canvas_init = FigureCanvas(fig)
        self.mplVLayout_init.addWidget(self.canvas_init)
        self.canvas_init.draw()
        self.toolbar_init = NavigationToolbar(self.canvas_init, self.mplWindow_init, coordinates=True)
        self.mplVLayout_init.addWidget(self.toolbar_init)

    def removePlotInit(self,):
        """
        Removes a plot from the "Init" viewing window of the BETSE GUI.

        """

        self.mplVLayout_init.removeWidget(self.canvas_init)
        self.canvas_init.close()
        self.mplVLayout_init.removeWidget(self.toolbar_init)
        self.toolbar_init.close()

    def changePlotInit(self):
        """
        Changes a figure in the "Init" viewing window of the BETSE GUI, given a click on an item.

        Parameters
        -----------
        item: signal from a mouse-click event on a QT GUI item with a text label.

        """
        item = self.comboBox_initPlots.currentText()
        self.removePlotInit()
        self.addPlotInit(self.fig_dict_init[item])

    def addPlotSim(self, fig):
        """
        Adds a plot to the "Sim" viewing window of the BETSE GUI

        Parameters
        ------------
        fig: matplotlib figure object

        """
        self.canvas_sim = FigureCanvas(fig)
        self.mplVLayout_sim.addWidget(self.canvas_sim)
        self.canvas_sim.draw()
        self.toolbar_sim = NavigationToolbar(self.canvas_sim, self.mplWindow_sim, coordinates=True)
        self.mplVLayout_sim.addWidget(self.toolbar_sim)

    def removePlotSim(self,):
        """
        Removes a plot from the "Sim" viewing window of the BETSE GUI.

        """

        self.mplVLayout_sim.removeWidget(self.canvas_sim)
        self.canvas_sim.close()
        self.mplVLayout_sim.removeWidget(self.toolbar_sim)
        self.toolbar_sim.close()

    def changePlotSim(self):
        """
        Changes a figure in the "Sim" viewing window of the BETSE GUI, given a click on an item.

        Parameters
        -----------
        item: signal from a mouse-click event on a QT GUI item with a text label.

        """
        item = self.comboBox_simPlots.currentText()
        self.removePlotSim()
        self.addPlotSim(self.fig_dict_sim[item])

# creating plots for the seed, init and sim viewer window--------------------------------------------------------------

    def plot_all_seed(self, write_to_comboBox = False):

        """
        Adds default plots to the Seed Viewer window.

        Parameters
        ------------

        write_to_comboBox:   are plot names added to the comboBox (used on first init only)

        """

        if self.p.autosave:
            images_path = self.p.init_results
            image_cache_dir = os.path.expanduser(images_path)
            os.makedirs(image_cache_dir, exist_ok=True)
            savedImg = os.path.join(image_cache_dir, 'fig_')


        if write_to_comboBox is True:

            # re-initialize the seed dictionary:
            self.fig_dict_seed = OrderedDict({})

            # clear the combo box
            self.comboBox_seedPlots.clear()


            if self.canvas_seed is None:

                # make a default plot to add to the canvas:
                fig_blank = Figure()
                fig_blank.add_subplot(111)
                self.addPlotSeed(fig_blank)

        if self.p.plot_cell_cluster is True:
            fig_cluster, ax_cluster, cb_cluster = pu.clusterPlot(
                self.p, self.sim.dyna, self.cells, clrmap=self.p.background_cm)

            if self.p.autosave is True:

                savename = savedImg + 'cluster_mosaic' + '.png'
                # print("Saving to: ", savename)
                fig_cluster.savefig(savename, format='png', transparent=True)


            # add the plot to the seed plot dictionary:
            self.fig_dict_seed['Cluster Plot'] = fig_cluster


            if write_to_comboBox is True:

                self.comboBox_seedPlots.addItem('Cluster Plot')

        if self.p.plot_cluster_mask is True:

            fig_envD = Figure()
            canvas_envD = FigureCanvas(fig_envD)
            ax_envD = fig_envD.add_subplot(111)

            if self.p.sim_ECM is True:
                envMesh = ax_envD.imshow(
                    np.log10(self.sim.D_env_weight.reshape(self.cells.X.shape)),
                    origin='lower',
                    extent=[self.p.um * self.cells.xmin, self.p.um * self.cells.xmax, self.p.um * self.cells.ymin,
                            self.p.um * self.cells.ymax],
                    cmap=self.p.background_cm,
                )
                fig_envD.colorbar(envMesh)

                cell_edges_flat = self.p.um * self.cells.mem_edges_flat
                coll = LineCollection(cell_edges_flat, colors='k')
                coll.set_alpha(1.0)
                ax_envD.add_collection(coll)
                ax_envD.set_aspect('equal')

                fig_envD.suptitle('Log of Env Diffusion Weight Matrix')

            else:
                ax_envD.text(self.cells.clust_xy[0], self.cells.clust_xy[1], "No Env Diffusion Data Available")

            # add the figure to the seed figure dictionary:

            self.fig_dict_seed['Environmental Diffusion'] = fig_envD


            if write_to_comboBox is True:

                self.comboBox_seedPlots.addItem('Environmental Diffusion')

            # if self.p.autosave is True:  # FIXME how to handle auto-save + message to user
                savename = savedImg + 'env_diffusion_weights' + '.png'
                # print(savename)
                canvas_envD.print_figure(savename, format = 'png', transparent = True)

            #     fig_envD.savefig(savename, format='png', transparent=True)

        # Plot gap junction network----------------------------------------------------------

        if self.p.plot_cell_connectivity is True:

            fig_gj = Figure()
            canvas_gj = FigureCanvas(fig_gj)
            ax_gj = fig_gj.add_subplot(111)

            if self.p.showCells is True:
                base_points = np.multiply(self.cells.cell_verts, self.p.um)
                col_cells = PolyCollection(base_points, facecolors='k', edgecolors='none')
                col_cells.set_alpha(0.3)
                ax_gj.add_collection(col_cells)

            con_segs = self.cells.nn_edges
            connects = self.p.um * np.asarray(con_segs)
            collection = LineCollection(connects, linewidths=1.0, color='b')
            ax_gj.add_collection(collection)
            ax_gj.set_aspect('equal')
            ax_gj.axis([self.cells.xmin * self.p.um, self.cells.xmax * self.p.um, self.cells.ymin * self.p.um,
                        self.cells.ymax * self.p.um])

            ax_gj.set_xlabel('Spatial x [um]')
            ax_gj.set_ylabel('Spatial y [um')
            fig_gj.suptitle('Cell Connectivity Network')

            self.fig_dict_seed['Gap Junction Network'] = fig_gj

            if write_to_comboBox is True:

                self.comboBox_seedPlots.addItem('Gap Junction Network')

            if self.p.autosave is True:
                savename = savedImg + 'gj_connectivity_network' + '.png'

                canvas_gj.print_figure(savename, format='png', transparent=True)
                # fig_gj.savefig(savename, format='png', transparent=True)

        self.groupBox_seedPlots.setEnabled(True)

    def plot_all_init(self, write_to_comboBox = False):


        if self.p.autosave:
            images_path = self.p.init_results
            image_cache_dir = os.path.expanduser(images_path)
            os.makedirs(image_cache_dir, exist_ok=True)
            # savedImg = os.path.join(image_cache_dir, 'fig_')

        if write_to_comboBox is True:

            # re-initialize the init dictionary:
            self.fig_dict_init = OrderedDict({})

            # clear the combo box
            self.comboBox_initPlots.clear()

            if self.canvas_init is None:

                # make a default plot to add to the canvas:
                fig_blank = Figure()
                fig_blank.add_subplot(111)
                self.addPlotInit(fig_blank)

        # ----default plot of Vmem for init-----------------------  # make time index a GUI variable!

        figVm, axVm, cbVm = pu.plotPrettyPolyData(1000*self.init.vm_time[-1],
                                               self.init, self.cells, self.p,
                                               clrAutoscale=self.p.autoscale_Vmem,
                                               clrMin=self.p.Vmem_min_clr,
                                               clrMax=self.p.Vmem_max_clr,
                                               number_cells=self.p.enumerate_cells,
                                               clrmap=self.p.default_cm,
                                               current_overlay=False,
                                               plotIecm=self.p.IecmPlot,
                                               )

        figVm.suptitle('Transmembrane Voltage (Vmem)', fontweight='bold')
        axVm.set_xlabel('Spatial distance [um]')
        axVm.set_ylabel('Spatial distance [um]')
        cbVm.set_label('Voltage mV')

        # add the plot to the seed plot dictionary:
        self.fig_dict_init['Vmem'] = figVm

        if write_to_comboBox is True:
            self.comboBox_initPlots.addItem('Vmem')

        self.groupBox_initPlotControls.setEnabled(True)


    def plot_all_sim(self, write_to_comboBox = False):

        if self.p.autosave:
            images_path = self.p.sim_results
            image_cache_dir = os.path.expanduser(images_path)
            os.makedirs(image_cache_dir, exist_ok=True)
            # savedImg = os.path.join(image_cache_dir, 'fig_')

        if write_to_comboBox is True:

            # re-initialize the init dictionary:
            self.fig_dict_sim = OrderedDict({})

            # clear the combo box
            self.comboBox_simPlots.clear()

            if self.canvas_sim is None:

                # make a default plot to add to the canvas:
                fig_blank = Figure()
                fig_blank.add_subplot(111)
                self.addPlotSim(fig_blank)

        # ----default plot of Vmem for init-----------------------  # make time index a GUI variable!

        figVm, axVm, cbVm = pu.plotPrettyPolyData(1000*self.sim.vm_time[-1],
                                               self.sim, self.cells, self.p,
                                               clrAutoscale=self.p.autoscale_Vmem,
                                               clrMin=self.p.Vmem_min_clr,
                                               clrMax=self.p.Vmem_max_clr,
                                               number_cells=self.p.enumerate_cells,
                                               clrmap=self.p.default_cm,
                                               current_overlay=False,
                                               plotIecm=self.p.IecmPlot,
                                               )

        figVm.suptitle('Transmembrane Voltage (Vmem)', fontweight='bold')
        axVm.set_xlabel('Spatial distance [um]')
        axVm.set_ylabel('Spatial distance [um]')
        cbVm.set_label('Voltage mV')

        # add the plot to the seed plot dictionary:
        self.fig_dict_sim['Vmem'] = figVm

        if write_to_comboBox is True:
            self.comboBox_simPlots.addItem('Vmem')

        self.groupBox_simPlotControls.setEnabled(True)

# dynamically changing plots in the seed, init and sim viewer window---------------------------------------------------

    def change_seed_plot_settings(self):

        # reset the colormap in case it's changed:
        # self.p.background_cm = matplotlibs.get_colormap(self.lineEdit_seedColormap.text())
        # self.p.default_cm = matplotlibs.get_colormap(self.lineEdit_seedColormap.text())

        self.plot_all_seed(write_to_comboBox=False)

    def change_init_plot_settings(self):

        # reset the colormap in case it's changed:
        # self.p.background_cm = matplotlibs.get_colormap(self.lineEdit_initColormap.text())
        # self.p.default_cm = matplotlibs.get_colormap(self.lineEdit_initColormap.text())

        self.plot_all_init(write_to_comboBox=False)

    def change_sim_plot_settings(self):

        # reset the colormap in case it's changed:
        # self.p.background_cm = matplotlibs.get_colormap(self.lineEdit_simColormap.text())
        # self.p.default_cm = matplotlibs.get_colormap(self.lineEdit_simColormap.text())

        self.plot_all_sim(write_to_comboBox=False)

# Utility functions for selecting specific files and other user-selections ---------------------------------------------

    def select_clippingBitmap(self):

        """
        Allows user to select a file from their system; returns filename

        """
        self.clippingBitmapFilename = QFileDialog.getOpenFileName(self, 'Open file')[0]

        if self.clippingBitmapFilename:

            self.lineEdit_ClippingBitmap.clear()

            self.lineEdit_ClippingBitmap.setText(self.clippingBitmapFilename)

    def toggle_initAutoscale(self):
        """
        Greys/un-greys the little "min/max" boxes of init plot controls to let user
        define an autoscale or specify plot values directly.

        """

        as_bool = self.radioButton_initAutoscale.isChecked()

        not_as_bool = not as_bool
        self.frame_initScaleMinMax.setEnabled(not_as_bool)

    def toggle_simAutoscale(self):

        """
        Greys/un-greys the little "min/max" boxes of sim plot controls to let user
        define an autoscale or specify plot values directly.

        """

        as_bool = self.radioButton_simAutoscale.isChecked()

        not_as_bool = not as_bool
        self.frame_simScaleMinMax.setEnabled(not_as_bool)

    def select_networkConfig(self):

        self.networkConfigFilename = QFileDialog.getOpenFileName(self, 'Open file')[0]

        if self.networkConfigFilename:

            self.lineEdit_NetConfig.clear()

            self.lineEdit_NetConfig.setText(self.networkConfigFilename)

#---GUI Log Messages----------------------------------------------------------------------------------------------------

    def write_message_to_box(self, msg):

        self.messageBox.appendPlainText(msg)

#---Utility methods managing seed/init/sim threads, progress updates, and workflow routing------------------------------

    # Seeds:

    def set_seed_progress(self, val):

        self.progressBar_seed.setValue(val)

    def completed_successful_seed_run(self):

        self.unlock_init_controls()
        self.unlock_play_button()

        # assume their is now a valid sim, and manage seed and sim locks:
        self.rb_lockSeed.setChecked(True)
        self.manage_seed_lock()
        self.lock_sim_controls()
        self.progressBar_seed.setValue(100)


    # Inits:
    def set_init_progress(self, val):

        self.progressBar_init.setValue(val)

    def completed_successful_init_run(self):

        # assume their is now a valid init, and manage seed and sim locks:
        self.rb_lockSeed.setChecked(True)
        self.manage_seed_lock()
        self.unlock_sim_controls()
        self.progressBar_init.setValue(100)

    # Sims:
    def set_sim_progress(self, val):

        self.progressBar_sim.setValue(val)

    def completed_successful_sim_run(self):

        # assume their is now a valid sim, and manage seed and sim locks:
        self.rb_lockSeed.setChecked(True)
        self.manage_seed_lock()
        self.unlock_sim_controls()
        self.unlock_init_controls()
        self.progressBar_sim.setValue(100)

#---Utility methods for locking controls to assist in workflow routing and thread safety--------------------------------

    # Seeds:

    def lock_play_button(self):

        self.actionRun_Sim.setEnabled(False)

    def unlock_play_button(self):

        self.actionRun_Sim.setEnabled(True)

    def manage_seed_lock(self):

        boo = self.rb_lockSeed.isChecked()

        not_boo = not boo

        self.widget_seedControls.setEnabled(not_boo)
        self.groupBox_generalOptions.setEnabled(not_boo)
        self.groupBox_clusterOptions.setEnabled(not_boo)

    def lock_seed_start(self):

        self.pushButton_startSeed.setEnabled(False)
        self.lock_play_button()

    def unlock_seed_start(self):

        self.pushButton_startSeed.setEnabled(True)
        self.unlock_play_button()

    def lock_seed_controls(self):

        self.actionRun_Seed.setEnabled(False)
        self.widget_seedControls.setEnabled(False)

    def unlock_seed_controls(self):

        self.actionRun_Seed.setEnabled(True)
        self.widget_seedControls.setEnabled(True)
        self.pushButton_startSeed.setEnabled(True)

    # Inits:

    def lock_init_start(self):

        self.pushButton_startInit.setEnabled(False)

    def unlock_init_start(self):

        self.pushButton_startInit.setEnabled(True)

    def lock_init_controls(self):

        self.groupBox_initControls.setEnabled(False)

    def unlock_init_controls(self):

        self.groupBox_initControls.setEnabled(True)

    # Sims:

    def lock_sim_start(self):

        self.pushButton_startSim.setEnabled(False)

    def unlock_sim_start(self):

        self.pushButton_startSim.setEnabled(True)

    def lock_sim_controls(self):

        self.groupBox_simControls.setEnabled(False)
        self.actionRun_Sim.setEnabled(False)

    def unlock_sim_controls(self):

        self.groupBox_simControls.setEnabled(True)
        self.actionRun_Sim.setEnabled(True)

#---Utility methods to handle worker threads from the main toolbar------------------------------------------------------

    def cancel_worker_threads(self):
        """
        This method terminates any betse-simulation-specific
        working threads (e.g. all running seeds, inits, sims, etc)

        """

        if self.seedRun._is_running:
            self.seedRun.stop()

        if self.initRun._is_running:
            self.initRun.stop()

        if self.simRun._is_running:
            self.simRun.stop()

#---Accessory classes---------------------------------------------------------------------------------------------------

# class QLogger(logging.Handler):
#     """
#
#     Class used to define a consol-like
#     region of the BETSE GUI, which will report
#     messages from the terminal.
#
#     """
#
#     def __init__(self, messageBox):
#         super().__init__()
#         self.console_widget = messageBox
#         self.console_widget.setReadOnly(True)
#
#     def emit(self, record):
#         """
#         This represents a signal collected from the
#         consol log.
#
#         """
#         msg = self.format(record)
#         self.console_widget.appendPlainText(msg)
#
#     def write(self, message):
#         """
#         This writes a string message to the muGUI console.
#
#         """
#         self.console_widget.appendPlainText(message)

# ....................{ THREADS                            }....................
# FIXME the following classes should all derive from the same base class.

class SeedThread(QThread):
    """
    This class defines a thread that emits log messages as signals using PySide
    signals and slots formalism.

    This thread may be started and stopped.

    While the seed thread is running, controls to run a sim or init are greyed
    out.
    """

    # signal to connect to GUI Consol box
    emit_message = pysideSignal(str)

    # signal to connect to progress bar
    emit_progress = pysideSignal(int)

    # seed start control lock/unlock signals
    emit_controlLock_startSeed = pysideSignal()
    emit_controlUnLock_startSeed = pysideSignal()

    # init and sim start control lock/unlock signals
    emit_controlLock_init = pysideSignal()
    emit_controlLock_sim = pysideSignal()
    emit_controlUnLock_init = pysideSignal()
    emit_controlUnLock_sim = pysideSignal()

    emit_controlUnlock_play = pysideSignal()

    # signal successful completion of the task:
    mission_completed = pysideSignal()

    def __init__(self):

        QThread.__init__(self)
        self.phase_mutex = QMutex()

        # control thread activity with this parameter:
        self._is_running = False

    def set_up(self, path_to_seed, p):

        self.path_to_seed = path_to_seed
        self.p = p

    def run(self):

        self._is_running = True

        # emit signals to lock init and sim control button boxes:
        self.emit_controlLock_startSeed.emit()
        self.emit_controlLock_init.emit()
        self.emit_controlLock_sim.emit()

        #-----------------------------------------------------

        jj =0

        for i in range(10):

            jj = jj + 1
            if not self._is_running:
                break

            with QMutexLocker(self.phase_mutex):

                # emit message to the main program:
                self.emit_message.emit("Seed " + str(i))

                time.sleep(1.0)
                prog = int((i/10)*100)

                # emit progress signal
                self.emit_progress.emit(prog)


        if jj == 10:  # suggest files.is_file(self.path_to_sim) as a good check for phase completion.

            self.mission_completed.emit()

            self.emit_message.emit("                     ")

            self.emit_message.emit("Cell Cluster creation finished successfully!")

        else:

            self.emit_message.emit("The Seed run was canceled prematurely.")
            self.emit_progress.emit(0)

        # emit signals to unlock init and sim control button boxes:
        self.emit_controlUnLock_startSeed.emit()
        self.emit_controlUnlock_play.emit()


    def stop(self):
        self._is_running = False


class InitThread(QThread):
    """
    This class defines a thread that emits log messages as signals using PySide
    signals and slots formalism.

    This thread may be started and stopped.
    """

    # signal to connect to GUI Consol box
    emit_message = pysideSignal(str)

    # signal to connect to progress bar
    emit_progress = pysideSignal(int)

    # seed start control lock/unlock signals
    emit_controlLock_startInit = pysideSignal()
    emit_controlUnLock_startInit = pysideSignal()

    # init and sim start control lock/unlock signals
    emit_controlLock_seed = pysideSignal()
    emit_controlLock_sim = pysideSignal()
    emit_controlUnLock_seed = pysideSignal()
    emit_controlUnLock_sim = pysideSignal()

    # signal successful completion of the task:
    mission_completed = pysideSignal()

    def __init__(self):

        QThread.__init__(self)
        self.phase_mutex = QMutex()
        self._is_running = False

    def set_up(self, path_to_init, p):

        self.path_to_init = path_to_init
        self.p = p

    def run(self):

        self._is_running = True

        # emit signals to lock init and sim control button boxes:
        self.emit_controlLock_startInit.emit()
        self.emit_controlLock_seed.emit()
        self.emit_controlLock_sim.emit()

        # ------Thread Loop Logic ----------------------

        jj = 0

        for i in range(10):

            jj = jj + 1
            if not self._is_running:
                break

            with QMutexLocker(self.phase_mutex):

                # emit message to the main program:
                self.emit_message.emit("Init " + str(i))

                time.sleep(1.0)
                prog = int((i / 10) * 100)

                # emit progress signal
                self.emit_progress.emit(prog)

        if jj == 10:  # suggest files.is_file(self.path_to_init) as a good check for phase completion.

            self.mission_completed.emit()

            self.emit_message.emit("                     ")

            self.emit_message.emit("Initialization finished successfully!")

        else:

            self.emit_message.emit("The Init run was canceled prematurely.")
            self.emit_progress.emit(0)

        # emit signals to unlock init and sim control button boxes:
        self.emit_controlUnLock_startInit.emit()
        self.emit_controlUnLock_seed.emit()
        self.emit_controlUnLock_sim.emit()

    def stop(self):
        self._is_running = False


class SimThread(QThread):
    """
    This class defines a thread that emits log messages as signals using PySide
    signals and slots formalism.

    This thread may be started and stopped.
    """

    # signal to connect to GUI Consol box
    emit_message = pysideSignal(str)

    # signal to connect to progress bar
    emit_progress = pysideSignal(int)

    # seed start control lock/unlock signals
    emit_controlLock_startSim = pysideSignal()
    emit_controlUnLock_startSim = pysideSignal()

    # init and sim start control lock/unlock signals
    emit_controlLock_init = pysideSignal()
    emit_controlLock_seed = pysideSignal()
    emit_controlUnLock_init = pysideSignal()
    emit_controlUnLock_seed = pysideSignal()

    # signal successful completion of the task:
    mission_completed = pysideSignal()

    def __init__(self):

        QThread.__init__(self)
        self.phase_mutex = QMutex()
        self._is_running = False

    def run(self):

        self._is_running = True

        # emit signals to lock init and sim control button boxes:
        self.emit_controlLock_startSim.emit()
        self.emit_controlLock_init.emit()
        self.emit_controlLock_seed.emit()

        # ------Thread Loop Logic ----------------------

        jj = 0

        for i in range(10):

            jj = jj + 1
            if not self._is_running:
                break

            with QMutexLocker(self.phase_mutex):

                # emit message to the main program:
                self.emit_message.emit("Sim " + str(i))

                time.sleep(1.0)
                prog = int((i / 10) * 100)

                # emit progress signal
                self.emit_progress.emit(prog)

        if jj == 10:  # suggest files.is_file(self.path_to_init) as a good check for phase completion.

            self.mission_completed.emit()
            self.emit_message.emit("                     ")
            self.emit_message.emit("Simulation finished successfully!")

        else:

            self.emit_message.emit("The Sim run was canceled prematurely.")
            self.emit_progress.emit(0)

        # emit signals to unlock init and sim control button boxes:
        self.emit_controlUnLock_startSim.emit()
        self.emit_controlUnLock_init.emit()
        self.emit_controlUnLock_seed.emit()

    def stop(self):
        self._is_running = False

# ....................{ MAIN                               }....................
#FIXME: Shift the following logic into the "betsee.cli.guicli" submodule.
if __name__ == '__main__':

    app = QApplication(sys.argv)
    main = Main()

    main.show()

    sys.exit(app.exec_())
