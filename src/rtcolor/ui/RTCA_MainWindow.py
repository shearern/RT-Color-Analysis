import io

from Queue import Queue
from PIL import Image

from PySide.QtCore import *
from PySide.QtGui import *

from .RTCA_MainWindow_UI import Ui_RTCA_MainWindow_UI
from ..ScreenshotThread import ScreenshotThread
from ..HistogramThread import HistogramThread

def pil2pixmap(im, parent):

    image_data_buf = io.BytesIO()
    im.save(image_data_buf, 'PNG')
    image_data_buf.seek(0)

    qtimage = QImage(parent=parent)
    qtimage.loadFromData(image_data_buf.getvalue())
    return QPixmap.fromImage(qtimage, parent=parent)


class RTCA_MainWindow(QMainWindow, Ui_RTCA_MainWindow_UI):

    def __init__(self, parent=None):
        super(RTCA_MainWindow, self).__init__(parent=parent)
        self.setupUi(self)

        # Init Vars

        # Worker Threads
        q = Queue(maxsize=1) # For passing screenshots to histogram processor

        self.screenshot_thread = ScreenshotThread(q)
        self.screenshot_thread.start()

        self.histogram_thread = HistogramThread(input_queue = q)
        self.histogram_thread.start()

        # Connect signals/slots
        self.screenshot_thread.new_screenshot.connect(self.new_screenshot_ready)
        self.histogram_thread.updated.connect(self.new_histogram_ready)

        #self.play_btn.clicked.connect(self.play_pause)
        #self.pushButton_5.clicked.connect(self.jump)

        # Begin
        #QTimer.singleShot(200, self.choose_source_files)



    def new_screenshot_ready(self):
        '''Slot for when new screenshot ready'''

        # Display time taken to get screenshot
        self.screenshot_time_lbl.setText('%0.1f sec' % (self.screenshot_thread.sec_taken))

        # Scale preview to thumbnail
        thumb = self.screenshot_thread.last_screenshot.pil
        size = self.last_screenshot_lbl.width(), self.last_screenshot_lbl.height()
        thumb.thumbnail(size)

        # Convert image to QPixmap
        thumb_pixmap = pil2pixmap(thumb, self)

        self.last_screenshot_lbl.setPixmap(thumb_pixmap)


    def new_histogram_ready(self):
        '''Slot for when new histogram ready'''

        # Display time taken to generate
        self.histogram_time_lbl.setText('%0.1f sec' % (self.histogram_thread.sec_taken))

        # Convert image to QPixmap
        size = (self.analysis_image_lbl.width(), self.analysis_image_lbl.height() - 20)
        image = self.histogram_thread.histogram.draw_histogram(size[0], size[1], bin_width=4).pil
        pixmap = pil2pixmap(image, self)
        self.analysis_image_lbl.setPixmap(pixmap)
