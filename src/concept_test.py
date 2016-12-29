import os
import sys
import csv
import pyscreenshot as ImageGrab
from PIL import Image, ImageDraw

from PySide.QtCore import *
from PySide.QtGui import *


if __name__ == "__main__":

    if not os.path.exists('test_output'):
        os.mkdir('test_output')

    # Capture fullscreen
    im = ImageGrab.grab()
    path = os.path.join("test_output", 'fullscreen.png')
    print "Writing", path
    im.save(path)

    # Capture screen section
    im = ImageGrab.grab(bbox=(10,10,510,510)) # X1,Y1,X2,Y2
    path = os.path.join("test_output", 'section.png')
    print "Writing", path
    im.save(path)

    # Generate Histogram

    # http://effbot.org/imagingbook/image.htm
    # Returns a histogram for the image. The histogram is returned as a list of pixel counts, one for each pixel value
    # in the source image. If the image has more than one band, the histograms for all bands are concatenated (for
    # example, the histogram for an "RGB" image contains 768 values).

    print "Generating histogram"
    hist = im.histogram()

    # Save Histogram Data
    path = os.path.join("test_output", 'histogram.csv')
    with open(path, 'wb') as fh:
        writer = csv.writer(fh)
        writer.writerow(("Value", "R", "G", "B"))
        for i in range(256):
            writer.writerow((i, hist[i], hist[256+i], hist[256*2+i]))


    # Draw Histogram
    #
    # http://tophattaylor.blogspot.com/2009/05/python-rgb-histogram.html
    #
    # RGB Hitogram
    # This script will create a histogram image based on the RGB content of
    # an image. It uses PIL to do most of the donkey work but then we just
    # draw a pretty graph out of it.
    #
    # May 2009,  Scott McDonough, www.scottmcdonough.co.uk
    #

    histHeight = 300            # Height of the histogram
    histWidth = 500             # Width of the histogram
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

    ##################################################################################

    histMax = max(hist)                                     # comon color
    xScale = float(histWidth)/len(hist)                     # xScaling
    yScale = float((histHeight)*multiplerValue)/histMax     # yScaling

    im = Image.new("RGBA", (histWidth, histHeight), backgroundColor)
    draw = ImageDraw.Draw(im)

    # Draw Outline is required
    if showFstopLines:
        xmarker = histWidth/fStopLines
        x =0
        for i in range(1,fStopLines+1):
            draw.line((x, 0, x, histHeight), fill=lineColor)
            x+=xmarker
        draw.line((histWidth-1, 0, histWidth-1, 200), fill=lineColor)
        draw.line((0, 0, 0, histHeight), fill=lineColor)


    # Draw the RGB histogram lines
    x=0; c=0;
    for i in hist:
        if int(i)==0: pass
        else:
            color = red
            if c>255: color = green
            if c>511: color = blue
            draw.line((x, histHeight, x, histHeight-(i*yScale)), fill=color)
        if x>255: x=0
        else: x+=1
        c+=1

    # Now save and show the histogram
    path = os.path.join('test_output', 'histogram.png')
    print "Writing", path
    im.save(path, 'PNG')


    # Show Histogram in Qt App

    class Window(QWidget):
        def __init__(self, im, parent=None):
            QWidget.__init__(self, parent)

            self.im_data = im.tobytes('raw', 'RGBA')
            self.qt_image = QImage(self.im_data, im.size[0], im.size[1], QImage.Format_ARGB32)
            self.pix = QPixmap.fromImage(self.qt_image)

            self.setGeometry(100, 100, im.size[0], im.size[1])
            self.setWindowTitle('Window')


            self.lbl = QLabel(self)
            self.lbl.setPixmap(self.pix)
            self.lbl.show()


    app = QApplication(sys.argv)
    window = Window(im)
    window.show()
    sys.exit(app.exec_())

    print "Finished"