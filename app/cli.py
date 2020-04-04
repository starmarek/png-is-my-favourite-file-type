import logging
import traceback
from pngparser import PngParser

try:
    import fire
    import matplotlib.pyplot as plt
    import numpy as np
except ModuleNotFoundError:
    traceback.print_exc()
    print("\033[1;33mBefore you will debug, please delete 'venv' dir from project root and try again.\033[0m")
    exit(1)

log = logging.getLogger()

class CLI:
    """Provides access to package functionality

    cli.py module is using CLI class as an entrypoint.
    CLI's initializer setup all needed functionality such as logging settings or defining path to PNG file.
    CLI's methods represent core functionality of package and are called 'commands'.

    TIP:
    Help page may suggest that you should use: cli.py <flags> 
    Dont't worry it's wrapped in png_run.sh. Use:
    ./png_run.sh COMMAND <FLAGS>

    COMMANDS:
     - metadata
     - print

    For more, please read README.

    Args:
        file_name (str, optional): Optional. Defaults to png_files/dice.png. Path to your png file. 
        verbose (bool, optional):  Optional. Defaults to False. Print additional logs which should help in application debugging proccess
    """

    def __init__(self, file_name="png_files/dice.png", verbose=False):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_name = file_name
        self.verbose = verbose

        if self.verbose:
            log.setLevel(logging.DEBUG)

        self.png = PngParser(self.file_name)

    def __del__(self):
        plt.show()

    def metadata(self, idat=False, plte=False):
        # print metadta
        log.debug("Printing metadata")
        self.png.print_chunks(idat, plte)

    def print(self, no_gamma=False):
        # print PNG from reconstructed IDAT data
        log.debug("Printing file")
        self.png.enable_print_mode(no_gamma)
        width = self.png.get_chunk_by_type(b'IHDR').width
        height = self.png.get_chunk_by_type(b'IHDR').height
        if self.png.bytesPerPixel == 1:
            # greyscale
            plt.imshow(np.array(png.reconstructed_idat_data).reshape((height, width)), cmap='gray', vmin=0, vmax=255)
        elif self.png.bytesPerPixel == 2:
            # greyscale with alpha channel
            self.png.reconstructed_idat_data = np.array(self.png.reconstructed_idat_data).reshape((height, width, self.png.bytesPerPixel))
            grayscale = self.png.reconstructed_idat_data[:, :, 0]
            alpha = self.png.reconstructed_idat_data[:, :, 1]
            rgb_img = np.dstack((grayscale, grayscale, grayscale, alpha))
            plt.imshow(rgb_img)
        else:
            # truecolor, truecolor with alpha channel, pallette
            plt.imshow(np.array(self.png.reconstructed_idat_data).reshape((height, width, self.png.bytesPerPixel)))

    def spectrum(self):
        # print spectrum diagram via FFT
        pass

    def clean(self, output_file='new.png'):
        # remove unnecessary data from PNG
        self.png.create_clean_png(output_file)

    def fullservice(self, output_file='new.png', no_gamma=False, idat=False, plte=False):
        # every step from above + comparison
        plt.subplot(121)
        self.metadata(idat, plte)
        self.print(no_gamma)
        self.clean(output_file)

        print('=' * 100)

        plt.subplot(122)
        new_png = CLI(output_file)
        new_png.metadata(idat, plte)
        new_png.print(no_gamma)

if __name__ == '__main__':
    fire.Fire(CLI)
    # TODO:
    # - Improve debug logs
    # - Improve docstrings
    # - Spectrum diagram
    # - Improve readme
