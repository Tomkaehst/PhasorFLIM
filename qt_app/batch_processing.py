import path
import os
import sys
import glob
import openpyxl as xlsx


class BatchProcessing:
    def __init__(self, workbook_path=None, directory='./'):
        # Working directory for batch processing
        # PTU files in user-defined directory and
        # subdirectories will be included.
        self.directory = directory
        self.workbook = None
        self.ptus_in_working_directory = self.get_ptus_from_working_directory()

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
            self.create_workbook()
            self.write_ptu_infos_to_workbook()
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
        self.workbook = xlsx.Workbook()
        batch_sheet = self.workbook.active

        # Add title and color description
        batch_sheet.cell(1, 1).value = "FLIM Data Fitting"
        batch_sheet.cell(1, 1).font = xlsx.styles.Font(
            name='Calibri',
            size=24,
            bold=True
        )
        batch_sheet.cell(
            2, 2).value = 'Information supplied by the user and used by the program to retrieve the data'
        batch_sheet.cell(2, 1).fill = self.user_input_fill

        batch_sheet.cell(
            3, 2).value = 'additional Information supplied by the user, but not used by the program'
        batch_sheet.cell(3, 1).fill = self.user_annotation_fill

        batch_sheet.cell(
            4, 2).value = 'output from AGBP FLIM Fitter'
        batch_sheet.cell(4, 1).fill = self.output_fill

        # Setting column size for proper displaying of parameters
        batch_sheet.column_dimensions['A'].width = 25
        batch_sheet.column_dimensions['B'].width = 25
        batch_sheet.column_dimensions['C'].width = 7
        batch_sheet.column_dimensions['D'].width = 13
        batch_sheet.column_dimensions['E'].width = 13
        batch_sheet.column_dimensions['F'].width = 13
        batch_sheet.column_dimensions['G'].width = 13

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

    def read_workbook(self, filepath):
        self.workbook = xlsx.load_workbook(filepath)

    def save_workbook(self, filepat=None):
        self.workbook.save(filename=(self.directory + '/ptu_batch.xlsx'))

    # PTU file gathering and processing

    def get_ptus_from_working_directory(self):
        ptu_file_list = glob.glob(self.directory + "/**/*.ptu", recursive=True)
        return(ptu_file_list)

    def write_ptu_infos_to_workbook(self):
        for i in range(0, len(self.ptus_in_working_directory)):
            sheet = self.workbook.active
            # Writing relative path to file
            sheet.cell(
                row=self.current_row,
                column=1
            ).value = self.ptus_in_working_directory[i]

            # Writing filename
            sheet.cell(
                row=self.current_row,
                column=2
            ).value = os.path.basename(self.ptus_in_working_directory[i])

            self.current_row += 1


#batch = BatchProcessing(directory='../notebooks/data/')
# batch.write_ptu_infos_to_workbook()
# batch.save_workbook()
