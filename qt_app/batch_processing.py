import os
import sys
import glob
import numpy as np
import openpyxl as xlsx

from flimdata import flimdata
from fitting import fitter


class BatchProcessing:
    def __init__(self, workbook_path=None, directory='./'):
        # Working directory for batch processing
        # PTU files in user-defined directory and
        # subdirectories will be included.
        # CAVE: In order to be compatible with
        # PyQt5's file selector, we have to use
        # absolute paths!
        self.directory = directory
        self.workbook = None
        self.ptus_in_working_directory = self.get_ptus_from_working_directory()
        # Current PTU file based on position on list of files in working directory
        self.current_ptu = 0
        self.current_file_path = None
        self.current_flim_object = None
        self.current_channel = 0

        # Useful info at start row, above that only description
        self.start_row = 6
        self.current_row = self.start_row
        # Number of rows a measurement section uses
        self.measurement_section_row_dimension = 6
        self.measurement_section_column_dimension = 21

        # Colors and styles
        # User input
        self.user_input_color = xlsx.styles.colors.Color(rgb='FFFFFF00')
        self.user_input_fill = xlsx.styles.fills.PatternFill(
            patternType='solid',
            fgColor=self.user_input_color
        )
        self.user_annotation_color = xlsx.styles.colors.Color(rgb='bebebe')
        self.user_annotation_fill = xlsx.styles.fills.PatternFill(
            patternType='solid',
            fgColor=self.user_annotation_color
        )
        self.output_color = xlsx.styles.colors.Color(rgb='aad08e')
        self.output_fill = xlsx.styles.fills.PatternFill(
            patternType='solid',
            fgColor=self.output_color
        )

        self.headings = [
            'Directory',
            'Filename',
            'Channel',
            'Fluorophore',
            'User Grade',
            'Excitation [nm]',
            'Emission [nm]',
            'ROI',
            'Monoexp. Fit',
            '', '', '', '', '',
            'Biexp. Fit', '', '', '', '', '', '', ''
        ]
        self.headings2 = [
            '', '', '', '', '', '', '', '',
            'Offset',
            'Amp',
            'Tau',
            'IRF Shift',
            'IRF Sigma',
            'Red. Chi.',
            'Offset',
            'Amp1',
            'Tau1',
            'Amp2',
            'Tau2',
            'IRF Shift',
            'IRF Sigma',
            'Red. Chi.'
        ]

        if(workbook_path is None):
            print('Creating new Batch Workbook...\n')
            self.workbook = xlsx.Workbook()
            self.sheet = self.workbook.active
            self.create_workbook()
            self.write_ptu_paths_to_workbook()
            self.save_workbook()
        else:
            self.read_workbook(workbook_path)

    # Excel file IO  and formating functions

    def create_workbook(self):
        '''
        Creates new excel file for batch processing
        of PicoQuant PTU files. It will be automatically
        populated with relative file paths with all
        ptu-files found in the subdirectories.
        Formatting follows template agreed upon on 06/2020.
        '''
        # Creating new Excel workbook and worksheet
        # batch_sheet = self.workbook.active

        # Add title and color description
        self.sheet.cell(1, 1).value = "FLIM Data Fitting"
        self.sheet.cell(1, 1).font = xlsx.styles.Font(
            name='Calibri',
            size=24,
            bold=True
        )
        self.sheet.cell(
            2, 2).value = 'Information supplied by the user and used by the program to retrieve the data'
        self.sheet.cell(2, 1).fill = self.user_input_fill

        self.sheet.cell(
            3, 2).value = 'additional Information supplied by the user, but not used by the program'
        self.sheet.cell(3, 1).fill = self.user_annotation_fill

        self.sheet.cell(
            4, 2).value = 'output from AGBP FLIM Fitter'
        self.sheet.cell(4, 1).fill = self.output_fill

        # Setting column size for proper displaying of parameters
        self.sheet.column_dimensions['A'].width = 25
        self.sheet.column_dimensions['B'].width = 25
        self.sheet.column_dimensions['C'].width = 7
        self.sheet.column_dimensions['D'].width = 13
        self.sheet.column_dimensions['E'].width = 13
        self.sheet.column_dimensions['F'].width = 13
        self.sheet.column_dimensions['G'].width = 13

        # Adding one measurement section per ptu file
        # in directory and subdirectories
        self.add_header()

    def add_header(self, row_offset=0):
        '''
        Create a measurement file section for a ptu file to be processed
         and add it to end of batch file table.
        ---
        '''
        for i in range(1, self.measurement_section_column_dimension):
            current_cell_upper = self.workbook.active.cell(
                row=self.start_row + row_offset,
                column=i
            )
            current_cell_lower = self.workbook.active.cell(
                row=self.start_row + row_offset + 1,
                column=i
            )

            current_cell_upper.value = self.headings[i - 1]
            if(i < 4):
                current_cell_upper.fill = self.user_input_fill
            elif(i < 6):
                current_cell_upper.fill = self.user_annotation_fill
            else:
                current_cell_upper.fill = self.output_fill

            current_cell_lower.value = self.headings2[i - 1]
            if(i < 4):
                current_cell_lower.fill = self.user_input_fill
            elif(i < 6):
                current_cell_lower.fill = self.user_annotation_fill
            else:
                current_cell_lower.fill = self.output_fill

        self.current_row += 2

    # PTU file gathering and processing

    def get_ptus_from_working_directory(self):
        ptu_file_list = glob.glob(self.directory + "/**/*.ptu", recursive=True)
        return(ptu_file_list)

    def check_for_new_files(self):
        '''
        If workbook has already files in it, check if there're new
        files in the working directory of the loaded workbook.
        Append the new files to the list and start processing
        from the first new file.
        '''

        pass

    def check_for_unprocessed_files(self):
        '''
        Check for files that have not been processed in a
        given, loaded workbook.
        '''

        pass

    def change_current_file_path(self):
        self.current_file_path = os.path.join(
            self.sheet.cell(
                row=self.current_row,
                column=1
            ).value,
            self.sheet.cell(
                row=self.current_row,
                column=2
            ).value
        )

        print(os.path.basename(self.current_file_path))

    def load_ptu_file(self, spatial_binning=3, temporal_binning=0):

        self.change_current_file_path()

        self.current_flim_object = flimdata(
            self.current_file_path,
            self.current_channel,
            spatial_binning,
            temporal_binning,
            fast_load=True
        )

        print(self.current_flim_object.FLIMInfo)

        print("Channels: ",
              self.current_flim_object.FLIMInfo['availableChannels']
              )

    def change_channel(self, channel: int):
        self.channel = channel

    def go_to_next_file(self):

        self.current_row += 1

        # Start from first file if last file is exceeded
        if(self.current_row > len(self.ptus_in_working_directory) + 2):
            self.current_row = self.start_row + 2

        self.load_ptu_file()

    def go_to_previous_file(self):

        self.current_row -= 1

        # Start from last file if first file is exceeded
        if(self.current_row < (self.start_row + 2)):
            self.current_row = len(self.ptus_in_working_directory)

        self.load_ptu_file()

    def fit_current_ROI(self, roi_position=None):
        '''
        Perform fit of currently loaded PTU file (self.current_flim_object)
        using the user-set ROI from mainWindowInterface.
        '''
        pass

    # Write data to workbook

    def write_ptu_paths_to_workbook(self, roi_position=None):
        # Loop through files in working directory
        # and write directory and file name in
        # first and second column of the current row.
        for i in range(0, len(self.ptus_in_working_directory)):
            # Writing relative path to file
            self.sheet.cell(
                row=self.current_row,
                column=1
            ).value = os.path.dirname(self.ptus_in_working_directory[i])

            # Writing filename
            self.sheet.cell(
                row=self.current_row,
                column=2
            ).value = os.path.basename(self.ptus_in_working_directory[i])

            self.current_row += 1

        # Resetting row number to first position of file list
        self.current_row = self.start_row + 2

    def read_workbook(self, file_path):
        '''
        Read Excel workbook from user-set file path.
        '''
        self.workbook = xlsx.load_workbook(file_path)

    def save_workbook(self):
        '''
        Write Excel workbook to user-set directory.
        '''
        self.workbook.save(filename=(self.directory + '/ptu_batch.xlsx'))


# For debugging – Only runs, if batch_processing.py was called from command line
if(__name__ == '__main__'):
    path = '/Users/tomkache/Documents/Studium/PhD/2019/Data Analysis/PhasorFLIM/notebooks/data'
    batch = BatchProcessing(directory=path)
    batch.write_ptu_paths_to_workbook()
    batch.load_ptu_file()
    batch.save_workbook()
