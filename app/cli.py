import logging
import fire
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
        # printing metadta
        with PngParser(self.file_name) as png:
            png.print_chunks()

    def print(self):
        # print PNG
        pass

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
