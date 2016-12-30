from PIL import Image

class ThreadSafeImage(object):
    '''
    Object for passing images between threads

    PIL images don't seem to like to be passed between threads.  This object stores
    the image data.
    '''


    def __init__(self, im):
        '''
        :param im: PIL image to store
        '''
        self.__size = im.size
        self.__im_data =  im.convert('RGB').tobytes('raw', 'RGB')


    @property
    def pil(self):
        '''Get PIL image back out'''
        im = Image.frombytes('RGB', self.__size, self.__im_data, 'raw')
        return im