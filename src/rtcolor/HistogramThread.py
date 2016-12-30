from threading import RLock
import time
from PIL import Image, ImageDraw

from PySide.QtCore import QThread, QObject, Signal, QTimer, Slot

from .ThreadSafeImage import ThreadSafeImage

class Histogram(object):

    def __init__(self, data):
        self.data = data
        self.data_image = None

        self.redraw_histogram()

    # Constants
    default_width = 3 * 256
    default_height = 256

    background_color = (51,51,51)       # Background color
    marker_color     = (102,102,102)    # Line color of fStop Markers
    red = (255,60,60)                   # Color for the red lines
    green = (51,204,51)                 # Color for the green lines
    blue = (0,102,255)                  # Color for the blue lines

    y_scale = 10

    @property
    def rgb_counts(self):
        '''
        Yields data bins in histogram as tuple

        :return: (color_value 00-FF, R count, G count, B count)
        '''
        if len(self.data) != 3*256:
            raise Exception("Histogram data has %d items.  Expected %d" % (len(data), 3*256))

        for i in range(256):
            yield (i, self.data[i], self.data[i+256], self.data[i+256+256])


    @property
    def rgb_pcts(self):
        '''
        Yield data bins in histogram as tuple converted to percent

        :return: (color_value 00-FF, R%, G%, B%)
        '''

        # Find total number of pixels to compare against
        sums = {'r': 0, 'g': 0, 'b': 0}
        for bin, r, g, b in self.rgb_counts:
            sums['r'] += r
            sums['g'] += g
            sums['b'] += b
        upper_limit = max(sums.values()) # All three should be the same I think?

        # Return values as percentages
        for bin, r, g, b in self.rgb_counts:
            yield (bin, float(r)/upper_limit, float(g)/upper_limit, float(b)/upper_limit)

    def redraw_histogram(self, width=None, height=None):
        '''
        Draw histogram image.

        Current theory:
         - Draw RGB as interleaved bars
           (ref: https://en.wikipedia.org/wiki/Color_histogram#/media/File:Odd-eyed_cat_histogram.png)
         - Draw histogram as an ideally fitted image
             width:     3 * 256
             height:    256
         - Map frequency to Y as (% of pixels) * 256
        '''
        if width is None:
            width = self.default_width
        if height is None:
            height = self.default_height

        im = Image.new("RGBA", (width, height), self.background_color)
        draw = ImageDraw.Draw(im)

        # Draw the RGB histogram lines
        x = -1
        for bin, r, g, b in self.rgb_pcts:
            # R
            x += 1
            draw.line((x, height, x, height-(self.y_scale*r*height)), fill=self.red)

            # G
            x += 1
            draw.line((x, height, x, height-(self.y_scale*g*height)), fill=self.green)

            # B
            x += 1
            draw.line((x, height, x, height-(self.y_scale*b*height)), fill=self.blue)

        self.data_image = ThreadSafeImage(im)


class HistogramThread(QThread):
    '''Generate histograms from screenshots'''

    # Based on:
    # http://tophattaylor.blogspot.com/2009/05/python-rgb-histogram.html

    updated = Signal()
    
    def __init__(self, input_queue, parent=None):
        super(HistogramThread, self).__init__(parent)

        self.input_queue = input_queue

        # Settings
        self.__settings_lock = RLock()

        # Outputs
        self.__output_lock = RLock()
        self.__histogram = None
        self.__sec_taken = None

        # Timing
        self.__started = None


    def run(self):
        while True:
            next_screenshot = self.input_queue.get().pil

            # Start timing
            self.__started = time.time()

            # Calculate histogram
            hist = Histogram(data = next_screenshot.histogram())

            # Output results
            with self.__output_lock:
                self.__histogram = hist
                self.__sec_taken = time.time() - self.__started

            self.updated.emit()


    @property
    def sec_taken(self):
        with self.__output_lock:
            return self.__sec_taken


    @property
    def histogram(self):
        with self.__output_lock:
            return self.__histogram