from threading import RLock
import time
from math import floor, ceil
from PIL import Image, ImageDraw

from PySide.QtCore import QThread, QObject, Signal, QTimer, Slot
from pygments.lexers import data

from .ThreadSafeImage import ThreadSafeImage

def rebin_data(data, new_bin_count):
    '''
    Convert number of bins in the histogram

    :param data: Histogram bins
    :param new_bin_count: New number of bins to return
    '''
    bins = [0, ] * new_bin_count

    b_bin_width = float(len(data)) / new_bin_count
    def a_bins_overlapping_b(o_bi):
        '''Return indexes of bins in data overlapped by bin bi in new bins'''
        o_first = int(floor(o_bi * b_bin_width))
        o_last = int(ceil((o_bi+1) * b_bin_width))
        return range(max(0, o_first), min(o_last+1, len(data)))

    for bin_b in range(new_bin_count):
        for bin_a in a_bins_overlapping_b(bin_b):
            # Calc percent overlap
            bin_a_start = bin_a
            bin_a_end = bin_a + 1
            bin_b_start = bin_b * b_bin_width
            bin_b_end = (bin_b + 1) * b_bin_width

            if bin_b_start <= bin_a_start and bin_a_end <= bin_b_end:
                pct_a = 1
            elif bin_a_start <= bin_b_start and bin_b_end <= bin_a_end:
                pct_a = max(0, bin_b_end - bin_b_start)
            elif bin_a_start <= bin_b_start and bin_a_end <= bin_b_end:
                pct_a = max(0, bin_a_end - bin_b_start)
            elif bin_b_start <= bin_a_start and bin_b_end <= bin_a_end:
                pct_a = max(0, bin_b_end - bin_a_start)
            else:
                pct_a = 0 # Don't expect to get here

            # Calc contribution of origional bin to new bin
            bins[bin_b] += pct_a * data[bin_a]

    return bins



class Histogram(object):

    def __init__(self, data):
        self.data = data


    # Constants
    default_width = 3 * 256
    default_height = 256

    background_color = (51,51,51)       # Background color
    marker_color     = (102,102,102)    # Line color of fStop Markers

    y_scale = 10



    @property
    def rgb_counts(self):
        '''
        Yields data bins in histogram as tuple

        :return: (color_value 00-FF, R count, G count, B count)
        '''
        if len(self.data) != 3*256:
            raise Exception("Histogram data has %d items.  Expected %d" % (len(self.data), 3*256))

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


    def draw_histogram(self, width=None, height=None, bin_width = 1):
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

        # Number of bins we can get on this width
        bin_count = int(floor(width / bin_width))
        y_scale = 0.20

        # master image is one we'll return.
        # Will add each color as a seperate layer on top
        master = Image.new("RGBA", (width, height), self.background_color)

        layers = (
            ((255, 60, 60,256), (255, 60, 60,256),   0, 255),   # Red
            ((051,204, 51,256), ( 51,204, 51,256), 256, 511),   # Green
            ((  0,102,255,256), (  0,102,255,256), 512, 767),   # Blue
        )

        for line_color, fill_color, data_start, data_end in layers:

            data = self.data[data_start:data_end+1]
            ##before = sum(data)
            data = rebin_data(data, bin_count)
            ##after = sum(data)
            ##print "Sum before = %d, sum after = %d, difference = %d (%.02f%%)" % (before, after, after - before, (100 * (after - before)) / before)
            data_max = max(data)

            # Start layer for this color
            layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

            # -- Draw each bin --------------------------------------------------
            draw = ImageDraw.Draw(layer)
            for x, cnt in enumerate(data):

                start_x = x * bin_width
                end_x = (x + 1) * bin_width  - 1

                this_height = (cnt / data_max) * height
                this_y = height - this_height

                # Outline bin
                draw.line((start_x, height, start_x, this_y), fill=line_color) # Left border
                if end_x > start_x:
                    draw.line((start_x, this_y, end_x, this_y), fill=line_color) # Top
                    draw.line((end_x, height, end_x, this_y), fill=line_color) # Right border

                # Fill bin
                start_x -= 1
                end_x -= 1
                this_y += 1
                if start_x < end_x:
                    draw.rectangle((start_x, this_y, end_x, height), fill=fill_color)

            # Add layer to master
            master.paste(layer, (0, 0), layer)

        return ThreadSafeImage(master)


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