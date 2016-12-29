from queue import Queue

from PySide.QtCore import *
from PySide.QtGui import *

from .RTCA_MainWindow_UI import Ui_RTCA_MainWindow_UI
from ..ScreenshotThread import ScreenshotThread

class RTCA_MainWindow(QMainWindow, Ui_RTCA_MainWindow_UI):

    def __init__(self, parent=None):
        super(RTCA_MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

        # Init Vars

        # Worker Threads
        q = Queue(maxsize=1) # For passing screenshots to histogram processor
        self.screenshot_thread = ScreenshotThread(q)
        self.screenshot_thread.start()

        # Connect signals/slots
        self.screenshot_thread.new_screenshot.connect(self.new_screenshot_ready)

        #self.play_btn.clicked.connect(self.play_pause)
        #self.pushButton_5.clicked.connect(self.jump)

        # Begin
        #QTimer.singleShot(200, self.choose_source_files)



    def new_screenshot_ready(self):
        '''Slot for when new screenshot ready'''
        self.screenshot_time_lbl.setText('%0.1f sec' % (self.screenshot_thread.sec_taken))