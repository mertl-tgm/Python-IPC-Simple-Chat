from Model import Model
import View
import sys

from PySide.QtGui import *


class Controller(object):

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.view = View.Ui_MainWindow()
        self.view.setupUi(self.window)

        self.model = Model()
        self.model.start()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
       super(MainWindow, self).__init__(parent)
       self.show()
