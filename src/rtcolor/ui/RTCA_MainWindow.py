import ctypes

import vlc
ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ctypes.py_object]

from PySide.QtCore import *
from PySide.QtGui import *

from .RTCA_MainWindow_UI import Ui_RTCA_MainWindow_UI

class RTCA_MainWindow(QMainWindow, Ui_RTCA_MainWindow_UI):

    def __init__(self, parent=None):
        super(RTCA_MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

        # Init Vars

        # Connect signals/slots
        #self.play_btn.clicked.connect(self.play_pause)
        #self.pushButton_5.clicked.connect(self.jump)

        # Begin
        #QTimer.singleShot(200, self.choose_source_files)

