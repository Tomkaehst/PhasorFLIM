# Importing PyQt5 Modules
from PyQt5.QtWidgets import QApplication

# Importing GUI scripts and modules
from gui.mainWindowInterface import Ui_mainWindowInterface

if(__name__ == '__main__'):
    app = QApplication([])
    app.setApplicationName('FLIM Analyser')

    window = Ui_mainWindowInterface()

    print('Executing Q5 App...')
    app.exec_()