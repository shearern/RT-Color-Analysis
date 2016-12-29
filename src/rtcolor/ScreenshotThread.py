from threading import RLock
import pyscreenshot as ImageGrab
import time

from PySide.QtCore import QThread, QObject, Signal, QTimer, Slot

class ScreenshotThread(QThread):
    '''Thread to take screenshots'''

    new_screenshot = Signal()
    
    
    def __init__(self, output_queue, parent=None):
        super(ScreenshotThread, self).__init__(parent)

        self.output_queue = output_queue

        # Settings
        self.__settings_lock = RLock()
        self.__x_pos = None
        self.__width = None
        self.__y_pos = None
        self.__height = None
        self.__min_wait = None

        # Outputs
        self.__output_lock = RLock()
        self.__cur_screen = None
        self.__sec_taken = None

        # Timing
        self.__started = None


    @property
    def x_pos(self):
        return self.__x_pos
    @x_pos.setter
    def x_pos(self, value):
        with self.__settings_lock:
            self.__x_pos = int(value)
        
        
    @property
    def width(self):
        return self.__width
    @width.setter
    def width(self, value):
        with self.__settings_lock:
            self.__width = int(value)


    @property
    def y_pos(self):
        return self.__y_pos
    @y_pos.setter
    def y_pos(self, value):
        with self.__settings_lock:
            self.__y_pos = int(value)


    @property
    def height(self):
        return self.__height
    @height.setter
    def height(self, value):
        with self.__settings_lock:
            self.__height = int(value)


    @property
    def max_freq(self):
        return self.__min_wait
    @max_freq.setter
    def max_freq(self, value):
        with self.__settings_lock:
            self.__min_wait = int(value)        

    def run(self):

        while True:

            # Mark start for timing
            self.__started = time.time()

            # Capture screenshot
            with self.__settings_lock:
                fullscreen = False
                if self.__x_pos is None:
                    fullscreen = True
                elif self.__width is not None:
                    fullscreen = True
                elif self.__y_pos is not None:
                    fullscreen = True
                elif self.__height is not None:
                    fullscreen = True

                # Grab a section
                if fullscreen:
                    next_screen = ImageGrab.grab()
                else:
                    next_screen = ImageGrab.grab(bbox=(
                        self.__x_pos,
                        self.__y_pos,
                        self.__x_pos + self.__width - 1,
                        self.__y_pos + self.__height - 1,
                    ))
                    
            # Update output
            with self.__output_lock:
                self.__sec_taken = time.time() - self.__started
                self.__cur_screen = next_screen

            # Queue Output
            self.output_queue.put(next_screen)
            self.new_screenshot.emit()

            # Wait at least the given number of seconds
            wait_for = None
            with self.__settings_lock:
                if self.__min_wait is not None:
                    if time.time() - self.__started < self.__min_wait:
                        wait_for = self.__min_wait - (time.time() - self.__started)
            if wait_for is not None:
                time.sleep(wait_for)


    @property
    def sec_taken(self):
        with self.__output_lock:
            return self.__sec_taken


    @property
    def last_screenshot(self):
        with self.__output_lock:
            return self.__cur_screen

