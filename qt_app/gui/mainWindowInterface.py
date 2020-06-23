import sys
import os
import time
import traceback
import csv
import pyqtgraph as pg
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib.pyplot as plt
from PIL import Image

from gui.mainWindow import Ui_mainWindow
from flimdata import flimdata
from irf import IRF
from fitting import fitter
from batch_processing import BatchProcessing
from settings import settings


#pg.setConfigOptions(antialias =  True)


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

        # Setting up external classes
        # FLIM Data and Processing
        self.flim_object = None
        # FLIM Data and Processing for IRF Measurements
        self.irf_object = None
        # Path to PTU
        self.ptupath = None
        # Path to PTU of IRF
        self.irfpath = None
        # History of PTUs in current session
        self.ptuFileHistory = []
        # FLIM Decay Fitting Class
        self.fit_object = None
        # Batch Processing of PTUs
        self.batch = None

        # Some storage here for simple fit curve and residuals
        self.fitted_curve = None
        self.residuals = None

        # Initialize threads
        self.thread_pool = QThreadPool()
        self.update_log('%d CPU cores detected...' %
                        (self.thread_pool.maxThreadCount()))

        # GUI Actions
        self.update_log('Setting up GUI actions...')

        # Close application
        self.actionQuit.triggered.connect(self.close)

        # Clear log
        self.pushButton_clearLog.pressed.connect(self.clearLog)

        # Load PTU file
        self.pushButton_selectFile.pressed.connect(self.select_file)
        self.pushButton_LoadPTU.pressed.connect(self.load_ptu_file)

        # IRF
        self.pushButton_loadIRF.pressed.connect(self.load_irf)
        self.pushButton_showIRF.pressed.connect(self.show_irf)
        self.pushButton_correctIRF.pressed.connect(self.correct_irf)
        self.pushButton_resetIRF.pressed.connect(self.reset_irf)

        # Show ROI-selected decay
        self.pushButton_showSelectedDecay.pressed.connect(
            self.show_selected_decay
        )

        # Perform fit of selected decay
        self.pushButton_fitSelection.pressed.connect(self.fit_selected_decay)

        # Fit entire image
        self.pushButton_fitImage.pressed.connect(self.fit_image)

        # lifetime image setup
        self.pushButton_updateLifetimeImage.pressed.connect(
            self.show_lifetime_image)

        # Initializing decay tab
        self.decay_layout = pg.GraphicsLayout()
        self.graphicsView_decay.setCentralItem(self.decay_layout)
        self.graphicsView_decay.show()
        self.decay_plot = self.decay_layout.addPlot(row=1, col=1)
        self.residual_plot = self.decay_layout.addPlot(row=2, col=1)

        # Batch processing functions
        self.pushButton_loadNewWorkbook.pressed.connect(
            self.new_batch_workbook)
        self.pushButton_BatchNextFile.pressed.connect(self.next_file_in_batch)
        self.pushButton_BatchPreviousFile.pressed.connect(
            self.previous_file_in_batch)

        # Output functions
        self.pushButton_saveFitResults.pressed.connect(
            self.write_parameters_to_disk)
        self.pushButton_savePlot.pressed.connect(self.save_plot_to_disk)
        self.pushButton_saveDecay.pressed.connect(self.save_decay_to_disk)
        self.pushButton_saveImage.pressed.connect(
            self.save_intensity_image_to_disk)

        # Show GUI
        self.show()
        self.update_log('Ready...')

        self.save_application_settings()

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
                item = QListWidgetItem('%s: %f' % (
                    self.fit_object.parameter_names[i], self.fit_object.optimized_parameters['x'][i]))
                self.listWidget_fittedParameters.addItem(item)

            # Calculate reduced chi-square
            item = QListWidgetItem('%s: %f' % (
                'Red. ChiSq.', self.fit_object.calculate_reduced_chi_square()))
            self.listWidget_fittedParameters.addItem(item)

            self.listWidget_fittedParameters.show()
        else:
            self.show_error('No Fit', 'No fit present!')

    def peak_at_header(self):
        if (self.ptupath):
            tmp = flimdata(
                file_path=self.ptupath,
                channel=0,
                spatial_binning=4,
                temporal_binning=5,
                fast_load=False
            )

            self.headerPeak.clear()

            for entry in tmp.FLIMInfo:
                self.headerPeak.appendPlainText(str(entry))
                self.headerPeak.appendPlainText(str(tmp.FLIMInfo[entry]))

            del tmp

        else:
            self.show_error('No File Selected',
                            'You have not selected a .ptu file yet!')

    def select_file(self):
        """
        Created file browser for file selection and passes path to self.ptupath.
        """
        if self.flim_object:
            self.show_error(
                'Attention', 'Previously loaded data will be overwritten!')
            self.update_log('Overwriting previous file...')
            self.flim_object = None
            self.fit_object = None

        self.ptupath = QFileDialog.getOpenFileName(
            filter='PTU Files (*.ptu)')[0]
        self.lineEdit_filepath.setText(self.ptupath)
        self.ptuFileHistory.append(self.ptupath)
        self.peak_at_header()

    def ajdust_cutoff_gui(self):
        '''
        Adjusting GUI elements to cut decay axis.
        Step size is set to decay bin width of data.
        Maximum is set to maximum time of decay and
        the automatic cutoff is set to 85 % of the
        maximum of the decay axis.
        '''
        # Adjusting step size of spin boxes
        step_size = int(round(self.flim_object.FLIMInfo['Resolution']*1E12))
        self.DoubleSpinBox_lowerCutoff.setSingleStep(step_size)
        self.DoubleSpinBox_higherCutoff.setSingleStep(step_size)

        # Setting maximum of spin boxes
        maximum = self.flim_object.time_axis[-1]
        self.DoubleSpinBox_lowerCutoff.setMaximum(maximum)
        self.DoubleSpinBox_higherCutoff.setMaximum(maximum)

        # Set current value of higher cutoff to 85 % of maximum
        standard_value = int((max(self.flim_object.time_axis))*0.85)
        print(standard_value)
        self.DoubleSpinBox_higherCutoff.setProperty(
            "value",
            standard_value
        )

    def load_ptu_file(self):
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
                    temporal_binning,
                    fast_load=True
                )

                # Changing max, min and step of upper and lower decay axis cutoffs
                self.ajdust_cutoff_gui()

                if (self.flim_object):
                    # Adding intensity image to first tab
                    # self.graphicsView_intensityimage.clear()
                    intensity_image = pg.ImageItem(
                        self.flim_object.intensity_image)
                    self.graphicsView_intensityimage.addItem(intensity_image)
                    self.graphicsView_intensityimage.setRange(
                        QRect(
                            0, 0, self.flim_object.intensity_image.shape[0], self.flim_object.intensity_image.shape[1])
                    )
                    # Switching view to first tab
                    self.tabWidget_view.setCurrentIndex(0)

                    # Delete previous ROI and create new
                    if (self.ROI):
                        self.graphicsView_intensityimage.removeItem(self.ROI)
                    self.ROI = pg.RectROI(
                        [self.flim_object.intensity_image.shape[0] / 2,
                            self.flim_object.intensity_image.shape[1] / 2],
                        [20, 20]
                    )
                    self.graphicsView_intensityimage.addItem(self.ROI)
                else:
                    self.show_error('Loading Error',
                                    'No FLIM data has been loaded yet!')

            except Exception as excep:
                print("Unexpected error:", excep)
                self.show_error(
                    'File Loading Error', 'File could not be loaded. Check file integrity!')
                return(-1)

            self.ptuFileHistory.append(filepath)
            self.update_log('Loaded' + filepath)
        else:
            self.update_log('No file selected.')
            self.show_error('Error', 'No file selected!')

    def load_ptu_file_thread(self):
        thread = Thread(self.load_ptu_file)
        thread.thread_signals.thread_result.connect(self.print_output)
        thread.thread_signals.thread_finished.connect(self.print_output)
        thread.thread_signals.thread_progress.connect(
            self.set_progressbar_value)

        self.thread_pool.start(thread)

    def load_irf(self):
        if (self.irf_object is not None):
            self.show_error('Attention', 'IRF will be overwritten!')

        self.irfpath = QFileDialog.getOpenFileName(
            filter='PTU Files (*.ptu)')[0]
        self.lineEdit_filePathIRF.setText(self.irfpath)

        self.irf_object = IRF(
            self.irfpath,
            channel=0
        )
        self.show_irf()

    def show_irf(self):
        if (self.irf_object is None):
            self.show_error('Attention', 'No IRF has been loaded!')
            return ()

        self.decay_plot.clear()
        self.residual_plot.clear()
        self.decay_plot.plot(
            x=self.irf_object.irf_time_axis,
            y=self.irf_object.irf,
            pen=pg.mkPen('w', width=2)
        )
        self.tabWidget_view.setCurrentIndex(1)

    def correct_irf(self):
        if (self.irf_object):
            self.irf_object.reset_irf()
            self.irf_object.set_background(
                self.spinBox_IRFBackground.value()
            )
            self.irf_object.cut_irf(
                self.spinBox_irfLeftCut.value(),
                self.spinBox_irfRightCut.value()
            )
            self.irf_object.standardize_irf()
            self.show_irf()
        else:
            self.show_error('Attention', 'No IRF has been loaded yet!')

    def reset_irf(self):
        if (self.irf_object):
            self.irf_object.reset_irf()
            self.show_irf()
        else:
            self.show_error('Attention', 'No IRF has been loaded yet!')

    def show_intensity_image(self, flim_object: flimdata = None):
        '''
        Displays intensity image of PTU file, if a flim data object is present.
        Otherwise, error message will be shown to user.
        '''

        if(flim_object is None):
            flim_object = self.flim_object

        if (flim_object):
            # self.graphicsView_intensityimage.clear()
            intensity_image = pg.ImageItem(flim_object.intensity_image)
            self.graphicsView_intensityimage.addItem(intensity_image)
            self.graphicsView_intensityimage.setRange(
                QRect(
                    0, 0, flim_object.intensity_image.shape[0], flim_object.intensity_image.shape[1])
            )
            self.tabWidget_view.setCurrentIndex(0)
        else:
            self.show_error('Loading Error',
                            'No FLIM data has been loaded yet!')

    def show_selected_decay(self):
        '''
        Allows user to plot fluorescence decay of selected image region.
        If no ROI is present, it will be projected onto intensity image.
        User then moves ROI to desired region. If ROI is present,
        the decay in the corresponding image region will be extracted
        and plotted.
        '''
        if(self.flim_object and self.ROI is not None):
            coordinates = self.ROI.pos()
            size = self.ROI.size()

            self.flim_object.sum_up_selected_decay(
                start_x=int(coordinates[0]),
                stop_x=int(coordinates[0] + size[0]),
                start_y=int(coordinates[1]),
                stop_y=int(coordinates[1] + size[1])
            )

            # self.selectedDecay = np.sum(np.sum(
            #    self.flim_object.flimarray[int(coordinates[0]):int(coordinates[0] + size[0]), int(coordinates[1]):int(coordinates[1] + size[1]), :], axis = 0
            # ), axis = 0)

            self.decay_plot.clear()
            self.residual_plot.clear()
            self.decay_plot.plot(
                x=self.flim_object.time_axis,
                y=self.flim_object.selected_decay,
                pen=pg.mkPen('w', width=2)
            )
            self.tabWidget_view.setCurrentIndex(1)

        else:
            self.show_error('Selection not possible.',
                            'Please load a FLIM file first.')

    def fit_selected_decay(self):

        if(self.flim_object is None):
            self.show_error('Fitting not possible.',
                            'Please load a FLIM file first.')
            return(-1)

        #self.show_error('Starting fitting procedure...', 'Starting the fitting procedure. This might take a while. Application is unresponsive during fitting...')

        self.fit_object = fitter(
            time_axis=self.flim_object.time_axis,
            data=self.flim_object.selected_decay,
            number_of_exponentials=self.spinBox_noExp.value(),
            objective_function=self.comboBox_objectiveFunction.currentText(),
            lower_time_cutoff=self.DoubleSpinBox_lowerCutoff.value(),
            upper_time_cutoff=self.DoubleSpinBox_higherCutoff.value()
        )

        if (self.irf_object and self.checkBox_measuredIRFFit.isChecked()):
            try:
                self.fitted_curve, self.residuals = self.fit_object.fit_decay(
                    decay=self.fit_object.data,
                    measured_irf=self.irf_object.irf
                )

            except:
                self.show_error('Attention', 'IRF fit has not been done yet!')
                return(0)
        else:
            self.fitted_curve, self.residuals = self.fit_object.fit_decay(
                decay=self.fit_object.data
            )

        # Plotting selected decay and the corresping fit
        self.decay_plot.clear()
        self.decay_plot.plot(
            x=self.fit_object.time_axis,
            y=self.fit_object.data,
            pen=pg.mkPen('w', width=2)
        )
        self.decay_plot.plot(
            x=self.fit_object.time_axis,
            y=self.fitted_curve,
            pen=pg.mkPen('r', width=2)
        )

        self.residual_plot.clear()
        self.residual_plot.plot(
            x=self.fit_object.time_axis,
            y=self.residuals,
            pen=pg.mkPen('w', width=2)
        )

        if(self.fit_object.optimized_parameters['success'] == False):
            self.show_error(
                'Warning', 'The optimizer did not report a successful fit. Please check it manually.')
        else:
            self.update_log('Fit successful! \n')
            self.show_optimized_parameters()

    def fit_image(self):
        self.fit_object = fitter(
            self.flim_object.time_axis,
            self.flim_object.flimarray
        )

        self.fit_object.fit_image(
            photon_threshold=self.spinBox_photonThreshold.value())
        # self.show_lifetime_image()

    def show_lifetime_image(self):

        colored_image = pg.ImageItem()
        colored_image.setImage(
            self.fit_object.lifetime_image
        )

        color_positions = np.array([0.0, 0.33, 0.66, 1.0])
        color = np.array([[0, 0, 0, 255], [255, 0, 0, 255], [
                         0, 255, 0, 255], [0, 0, 255, 255]], dtype=np.ubyte)
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

    # Batch processing functions

    def new_batch_workbook(self):
        self.batch_directory = QFileDialog.getExistingDirectory()

        print(self.batch_directory)

        # Creating new Batch object
        self.batch = BatchProcessing(directory=self.batch_directory)

        # Setting user-selected channel for processing
        self.batch.change_channel(
            self.spinBox_BatchChannel.value()
        )
        # Loading first file in batch
        self.batch.load_ptu_file()

        # Display current file name in batch menu
        self.label_BatchCurrentFile.setText(
            os.path.basename(self.batch.current_file_path)
        )

        # Display intensity image of first file in batch
        self.show_current_image_in_batch()

        self.update_log(
            str('Created new batch file at ' + self.batch_directory)
        )

    def next_file_in_batch(self):
        if(self.batch is not None):
            # Decrement Batch file index
            self.batch.go_to_next_file()

            # Check if user changed channel
            #! Use PyQt5 featured / concurrency to do this like a normal person!
            self.batch.change_channel(
                self.spinBox_BatchChannel.value()
            )
            self.batch.load_ptu_file()
            self.label_Batch_CurrentFile.setText(
                os.path.basename(self.batch.current_file_path)
            )
            self.show_current_image_in_batch()
        else:
            self.show_error(
                'No Batch',
                'No batch is currently active.'
            )

    def previous_file_in_batch(self):
        if(self.batch is not None):
            # Decrement Batch file index
            self.batch.go_to_previous_file()

            # Check if user changed channel
            #! Use PyQt5 featured / concurrency to do this like a normal person!
            self.batch.change_channel(
                self.spinBox_BatchChannel.value()
            )
            self.batch.load_ptu_file()
            self.label_Batch_CurrentFile.setText(
                os.path.basename(self.batch.current_file_path)
            )
            self.show_current_image_in_batch()
        else:
            self.show_error(
                'No Batch',
                'No batch is currently active.'
            )

    def show_current_image_in_batch(self):
        # Display intensity image of current file in batch
        self.show_intensity_image(
            self.batch.current_flim_object
        )

        # Add ROI to current file in batch
        if (self.ROI):
            self.graphicsView_intensityimage.removeItem(self.ROI)
            self.ROI = pg.RectROI(
                [self.batch.current_flim_object.intensity_image.shape[0] / 2,
                 self.batch.current_flim_object.intensity_image.shape[1] / 2],
                [10, 10]
            )
            self.graphicsView_intensityimage.addItem(self.ROI)

        else:
            self.ROI = pg.RectROI(
                [self.batch.current_flim_object.intensity_image.shape[0] / 2,
                 self.batch.current_flim_object.intensity_image.shape[1] / 2],
                [10, 10]
            )
            self.graphicsView_intensityimage.addItem(self.ROI)

        # Set view to intensity image
        self.tabWidget_view.setCurrentIndex(0)

    # Output functions

    def write_parameters_to_disk(self):
        '''
        Write fitted parameters to csv file together with header information.
        '''

        try:
            save_path = QFileDialog.getSaveFileName(
                self,
                'Save Fit Results...'
            )

            save_path = str(save_path[0] + '.csv')

            with open(save_path, 'w') as file:
                writer = csv.writer(file)

                for i in range(len(self.fit_object.optimized_parameters['x'])):
                    writer.writerow([
                        self.fit_object.parameter_names[i],
                        self.fit_object.optimized_parameters['x'][i]

                    ])

                writer.writerow([
                    "Red. Chi-Sq.",
                    self.fit_object.calculate_reduced_chi_square()
                ])

                writer.writerow(['---'])

                writer.writerow([
                    'Header'
                ])

                for header_element in self.flim_object.header_contents:
                    writer.writerow([
                        header_element,
                        self.flim_object.header_contents[header_element]
                    ])

        except:
            self.show_error('No Fit', 'No fitted parameters available!')

    def save_decay_to_disk(self):
        try:
            save_path = QFileDialog.getSaveFileName(
                self,
                'Save Decay...'
            )

            save_path = str(save_path[0] + '.csv')

            with open(save_path, 'w') as file:

                writer = csv.writer(file)

                writer.writerow([
                    'File:',
                    self.flim_object.FLIMInfo['Filename']
                ])

                writer.writerow([
                    'Time Axis [ps]',
                    'Decay Data [Counts]',
                    'Fitted Curve',
                    'Residuals'
                ])

                for i in range(len(self.fit_object.time_axis)):
                    writer.writerow([
                        self.fit_object.time_axis[i],
                        self.fit_object.data[i],
                        self.fitted_curve[i],
                        self.residuals[i]
                    ])

        except Exception as exp:
            print(exp)
            self.show_error('No fit', 'No fitted curve available!')

    def save_intensity_image_to_disk(self):
        try:
            save_path = QFileDialog.getSaveFileName(
                self,
                'Save Intensity Image...'
            )

            save_path = str(save_path[0] + '.png')

            image = Image.fromarray(self.flim_object.intensity_image)
            image.save(save_path)

        except Exception as e:
            print(e)
            self.show_error('Intensity Image coult not be saved.',
                            'No intensity image available.')

    def save_plot_to_disk(self):

        try:
            save_path = QFileDialog.getSaveFileName(
                self,
                'Save Plot...'
            )

            save_path = str(save_path[0] + '.png')

            fig, ax = plt.subplots(
                nrows=2,
                ncols=1,
                figsize=(self.spinBox_plotWidth.value(),
                         self.spinBox_plotHeight.value()),
                sharex=True
            )

            ax[0].plot(self.fit_object.time_axis, self.fit_object.data, 'b.')
            ax[0].plot(self.fit_object.time_axis, self.fitted_curve, 'r-')
            ax[0].set(
                ylabel='Counts',
                yscale='log'
            )

            ax[1].plot(self.fit_object.time_axis, self.residuals)
            ax[1].set(
                ylabel='Residiuals',
                xlabel='Time [ps]'
            )

            plt.savefig(
                save_path,
                dpi=350,
                format='png'
            )
            plt.close()
        except Exception as excep:
            print(excep)
            self.show_error('No Fit', 'No fitted curve available.')

    # Save application states

    def save_application_settings(self):
        application_state = settings(self)


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
            self.thread_signals.thread_error.emit(
                (exctype, value, traceback.format_exc()))
        else:
            self.thread_signals.thread_result.emit(result)
        finally:
            self.thread_signals.thread_finished.emit()


class ThreadSignals(QObject):
    thread_finished = pyqtSignal()
    thread_error = pyqtSignal(tuple)
    thread_result = pyqtSignal(object)
    thread_progress = pyqtSignal(int)
