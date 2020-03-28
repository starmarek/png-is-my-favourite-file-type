import logging
import fire
import matplotlib.pyplot as plt
import numpy as np
from pngparser import PngParser

log = logging.getLogger()

class CLI:
    def __init__(self, file_name, verbose=False):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if verbose:
            log.setLevel(logging.DEBUG)
        self.file_name = file_name

    def metadata(self):
        # print metadta
        with PngParser(self.file_name) as png:
            png.print_chunks()

    def print(self):
        # print PNG from reconstructed IHDR data
        with PngParser(self.file_name) as png:
            plt.imshow(np.array(png.reconstructed_idat_data).reshape((png.height, png.width, 4)))
            plt.show()

    def spectrum(self):
        # print spectrum diagram via FFT
        pass

    def clean(self):
        # remove unnecessary data from PNG and print it
        pass

    def full_service(self):
        # every step from above
        pass

if __name__ == '__main__':
    fire.Fire(CLI)
    # TODO:
    # - Better method to get png metadata than saving it as an pngparser's attribute, e.g. getter
    # - Add precausions to starter script -> python>=3.8, tkinter to matplotlib: sudo apt install python3-tk
    # - Implement IDAT class
    # - Assertions
    # - Asking if user want to skip IDAT data print
    # - Improve debug logs