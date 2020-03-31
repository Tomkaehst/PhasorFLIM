import sys
import time
import traceback
import pyqtgraph as pg
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt


from gui.mainWindow import Ui_mainWindow
from flimdata import flimdata
from fitting import fitter




class Ui_mainWindowInterface(QMainWindow, Ui_mainWindow):

    def __init__(self, *args, **kwargs):

        # Inheriting Ui_mainWindow and initializung GUI
        print('Starting GUI...')
        super(Ui_mainWindowInterface, self).__init__(*args, **kwargs)
        print('Setting up Ui_mainWindow...')
        self.setupUi(self)

        # Initializing ROI objects
        self.ROI = None

        self.logHistory = []

        # Setting up flimdata class
        self.flim_object = None
        self.ptupath = None
        self.ptuFileHistory = []
        self.fit_object = None

        # Initialize threads
        self.thread_pool = QThreadPool()
        self.update_log('%d CPU threads used...'%(self.thread_pool.maxThreadCount()))


        # GUI Actions
        self.update_log('Setting up GUI actions...')

        # Close application
        self.actionQuit.triggered.connect(self.close)

        # Clear log
        self.pushButton_clearLog.pressed.connect(self.clearLog)

        # Load PTU file
        self.pushButton_selectFile.pressed.connect(self.select_file)
        self.pushButton_LoadPTU.pressed.connect(self.loadPTUFile)

        # Show intensity image
        self.pushButton_showIntensityImage.pressed.connect(
            self.show_intensity_image
        )

        # Show ROI-selected decay
        self.pushButton_showSelectedDecay.pressed.connect(
            self.show_selected_decay
        )
        
        # Perform fit of selected decay
        self.pushButton_fitSelection.pressed.connect(self.fit_selected_decay)

        # Fit entire image
        self.pushButton_fitImage.pressed.connect(self.fit_image)

        # lifetime image setup
        self.pushButton_updateLifetimeImage.pressed.connect(self.show_lifetime_image)

        # Show GUI
        self.show()
        self.update_log('Ready...')




    # GUI Management Functions
    def update_log(self, logMessage: str):
        """
        Displays string on text box. Used as log for performed actions and potential errors. logMessage string is appended to list of strings in flimdata object --> logHistory
        Arguments:
            logMessage {str} -- Log text to be displayed.

        """   
        self.logHistory.append(logMessage)
        self.logConsole.appendPlainText(self.logHistory[-1])


    def clearLog(self):
        self.logHistory = []
        self.logConsole.clear()


    def show_error(self, header: str, message: str):
        """
        Calls a Qt5 Message Box (critical) to attract users attention.
        Should be called from function, when a condition to run a certain action is not yet met, e.g. no file has been loaded etc. 
        
        Arguments:
            header {str} -- Window title of message box
            message {str} -- Message to be displayed in message box
        """        
        QMessageBox.critical(
            self,
            header,
            message
        )

    def set_progressbar_value(self, value):
        self.progressBar.setValue(value)



    def print_output(self, message):
        '''
        Generic function that prints any message to console.
        '''
        print(message)



    def show_optimized_parameters(self):
        """
        Displays fitted parameters from selected decay fit
        to list widget in fit tab.
        """
        if(self.fit_object.optimized_parameters):
            self.listWidget_fittedParameters.clear()
            for i in range(len(self.fit_object.optimized_parameters['x'])):
                item = QListWidgetItem('%s: %d'%(self.fit_object.parameter_names[i], self.fit_object.optimized_parameters['x'][i]))
                self.listWidget_fittedParameters.addItem(item)

            self.listWidget_fittedParameters.show()
        else:
            self.show_error('No Fit', 'No fit present!')


    # Analysis related functions

    def select_file(self):
        """
        Created file browser for file selection and passes path to self.ptupath.
        """
        if self.flim_object:
            self.show_error('Attention', 'Previously loaded data will be overwritten!')
            self.update_log('Overwriting previous file...')
            self.flim_object = None
            self.fit_object = None
            self.ROI = None
        
        self.ptupath = QFileDialog.getOpenFileName(filter='PTU Files (*.ptu)')[0]
        self.lineEdit_filepath.setText(self.ptupath)
        self.ptuFileHistory.append(self.ptupath)



    def loadPTUFile(self):
        """ 

        """
        spatial_binning = self.spinBox_spatialBinning.value()
        temporal_binning = self.spinBox_temporalBinning.value()
        channel = self.spinBox_channel.value()

        filepath = self.ptupath

        if filepath:
            try:
                self.flim_object = flimdata(
                    filepath,
                    channel,
                    spatial_binning,
                    temporal_binning
                )
            except:
                self.show_error('File Loading Error', 'File could not be loaded. Check file integrity!')
                return(-1)

            self.ptuFileHistory.append(filepath)
            self.update_log('Loaded' + filepath)
        else:
            self.update_log('No file selected.')
            self.show_error('Error', 'No file selected!')

    def loadPTUFile_thread(self):
        thread = Thread(self.loadPTUFile)
        thread.thread_signals.thread_result.connect(self.print_output)
        thread.thread_signals.thread_finished.connect(self.print_output)
        thread.thread_signals.thread_progress.connect(self.set_progressbar_value)

        self.thread_pool.start(thread)


    def show_intensity_image(self):
        '''
        Displays intensity image of PTU file, if a flim data object is present.
        Otherwise, error message will be shown to user.
        '''
        if(self.flim_object):
            intensity_image = pg.ImageItem(self.flim_object.intensity_image)
            self.graphicsView_intensityimage.addItem(intensity_image)
            self.graphicsView_intensityimage.setRange(
                QRect(0, 0, self.flim_object.intensity_image.shape[0], self.flim_object.intensity_image.shape[1])
            )
            self.tabWidget_view.setCurrentIndex(0)
        else:
            self.show_error('Loading Error', 'No FLIM data has been loaded yet!')
            

    def show_selected_decay(self):
        '''
        Allows user to plot fluorescence decay of selected image region.
        If no ROI is present, it will be projected onto intensity image.
        User then moves ROI to desired region. If ROI is present,
        the decay in the corresponding image region will be extracted
        and plotted.
        '''
        if(self.flim_object):
            if(self.ROI is None):
                self.ROI = pg.RectROI(
                    [self.flim_object.intensity_image.shape[0]/ 2, self.flim_object.intensity_image.shape[1]/ 2],
                    [20, 20]
                )
                self.graphicsView_intensityimage.addItem(self.ROI)
            else:
                coordinates = self.ROI.pos()
                size = self.ROI.size()
                
                self.flim_object.sum_up_selected_decay(
                    start_x = int(coordinates[0]),
                    stop_x = int(coordinates[0] + size[0]),
                    start_y = int(coordinates[1]),
                    stop_y = int(coordinates[1] + size[1])
                )

                #self.selectedDecay = np.sum(np.sum(
                #    self.flim_object.flimarray[int(coordinates[0]):int(coordinates[0] + size[0]), int(coordinates[1]):int(coordinates[1] + size[1]), :], axis = 0
                #), axis = 0)

                self.graphicsView_decay.clear()
                self.graphicsView_decay.plot(
                    x = self.flim_object.time_axis,
                    y = self.flim_object.selected_decay,
                    pen = pg.mkPen('w', width = 2)
                )
                self.tabWidget_view.setCurrentIndex(1)
            
        else:
            self.show_error('Selection not possible.', 'Please load a FLIM file first.')


    def fit_selected_decay(self):

        if(self.flim_object is None):
            self.show_error('Fitting not possible.', 'Please load a FLIM file first.')
            return(-1)

        #self.show_error('Starting fitting procedure...', 'Starting the fitting procedure. This might take a while. Application is unresponsive during fitting...')

        self.fit_object = fitter(
            self.flim_object.time_axis,
            self.flim_object.selected_decay,
            self.comboBox_objectiveFunction.currentText()
        )

        fit = self.fit_object.fit_decay(decay = self.fit_object.data)
        
        # Plotting selected decay and the corresping fit
        self.graphicsView_decay.clear()
        self.graphicsView_decay.plot(
            x = self.flim_object.time_axis,
            y = self.flim_object.selected_decay,
            pen = pg.mkPen('w', width = 2)
        )
        self.graphicsView_decay.plot(
            x = self.flim_object.time_axis,
            y = fit,
            pen = pg.mkPen('r', width = 2)
        )

        if(self.fit_object.optimized_parameters['success'] == False):
            self.show_error('Warning', 'The optimizer did not report a successful fit. Please check it manually.')
        else:
            self.update_log('Fit successful! \n')
            self.show_optimized_parameters()


    def fit_image(self):
        self.fit_object = fitter(
            self.flim_object.time_axis,
            self.flim_object.flimarray
        )

        self.fit_object.fit_image(photon_threshold=self.spinBox_photonThreshold.value())
        self.show_lifetime_image()

    def show_lifetime_image(self):

        colored_image = pg.ImageItem()
        colored_image.setImage(
            self.fit_object.lifetime_image
        )
        
        color_positions = np.array([0.0, 0.33, 0.66, 1.0])
        color = np.array([[0, 0, 0, 255], [255, 0, 0, 255], [0, 255, 0, 255], [0, 0, 255, 255]], dtype=np.ubyte)
        colormap = pg.ColorMap(
            color_positions,
            color
        )
        lut = colormap.getLookupTable(0, 1, 256)
        colored_image.setLookupTable(lut)
        colored_image.setLevels([
            self.spinBox_lifetimeLower.value(),
            self.spinBox_lifetimeUpper.value()
        ])

        self.graphicsView_lifetimeimage.addItem(colored_image)
        self.graphicsView_lifetimeimage.setRange(
                QRect(
                    0,
                    0,
                    self.flim_object.intensity_image.shape[0],
                    self.flim_object.intensity_image.shape[1])
            )
        self.tabWidget_view.setCurrentIndex(2)












class Thread(QRunnable):

    def __init__(self, function, *args, **kwargs):
        super(Thread, self).__init__()

        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.thread_signals = ThreadSignals()

        self.kwargs['progress_callback'] = self.thread_signals.thread_progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.thread_signals.thread_error.emit((exctype, value, traceback.format_exc()))
        else:
            self.thread_signals.thread_result.emit(result)
        finally:
            self.thread_signals.thread_finished.emit()



class ThreadSignals(QObject):
    thread_finished = pyqtSignal()
    thread_error = pyqtSignal(tuple)
    thread_result = pyqtSignal(object)
    thread_progress = pyqtSignal(int)