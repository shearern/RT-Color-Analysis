from threading import RLock
import time
from PIL import Image, ImageDraw

from PySide.QtCore import QThread, QObject, Signal, QTimer, Slot

class HistogramThread(QThread):
    '''Generate histograms from screenshots'''

    # Based on:
    # http://tophattaylor.blogspot.com/2009/05/python-rgb-histogram.html

    updated = Signal()
    
    def __init__(self, input_queue, width, height, parent=None):
        super(HistogramThread, self).__init__(parent)

        self.input_queue = input_queue

        # Settings
        self.__settings_lock = RLock()
        self.__width = width
        self.__height = height

        # Outputs
        self.__output_lock = RLock()
        self.__histogram_image = None
        self.__sec_taken = None

        # Timing
        self.__started = None


    # Constants
    multiplerValue = 1.5        # The multiplier value basically increases
                                # the histogram height so that love values
                                # are easier to see, this in effect chops off
                                # the top of the histogram.
    showFstopLines = True       # True/False to hide outline
    fStopLines = 5

    # Colours to be used
    backgroundColor = (51,51,51)    # Background color
    lineColor = (102,102,102)       # Line color of fStop Markers
    red = (255,60,60)               # Color for the red lines
    green = (51,204,51)             # Color for the green lines
    blue = (0,102,255)              # Color for the blue lines


    def run(self):
        while True:
            size, next_screenshot = self.input_queue.get()
            next_screenshot = Image.frombytes('RGB', size, next_screenshot, 'raw')

            # Start timing
            self.__started = time.time()

            # Calculate histogram
            hist = next_screenshot.histogram()

            # -- Draw new histogram -------------------------------------------------

            # Get width and heigh
            with self.__settings_lock:
                hist_width = self.__width
                hist_height = self.__height


            histMax = max(hist)                                         # comon color
            xScale = float(hist_width)/len(hist)                        # xScaling
            yScale = float((hist_height)*self.multiplerValue)/histMax   # yScaling
            im = Image.new("RGBA", (hist_width, hist_height), self.backgroundColor)
            draw = ImageDraw.Draw(im)

            # Draw Outline is required
            if self.showFstopLines:
                xmarker = hist_width/self.fStopLines
                x =0
                for i in range(1,self.fStopLines+1):
                    draw.line((x, 0, x, hist_height), fill=self.lineColor)
                    x+=xmarker
                draw.line((hist_width-1, 0, hist_height-1, 200), fill=self.lineColor)
                draw.line((0, 0, 0, hist_height), fill=self.lineColor)


            # Draw the RGB histogram lines
            x=0; c=0;
            for i in hist:
                if int(i)==0: pass
                else:
                    color = self.red
                    if c>255: color = self.green
                    if c>511: color = self.blue
                    draw.line((x, hist_height, x, hist_height-(i*yScale)), fill=color)
                if x>255: x=0
                else: x+=1
                c+=1

            # Output results
            with self.__output_lock:
                self.__histogram_image = im
                self.__sec_taken = time.time() - self.__started

            self.updated.emit()


    @property
    def sec_taken(self):
        with self.__output_lock:
            return self.__sec_taken


    @property
    def histogram_image(self):
        with self.__output_lock:
            return self.__histogram_image