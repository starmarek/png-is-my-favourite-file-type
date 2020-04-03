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

    def metadata(self, skip_idat_data=False):
        # print metadta
        with PngParser(self.file_name) as png:
            log.debug("Printing metadata")
            png.print_chunks(skip_idat_data)

    def print(self):
        # print PNG from reconstructed IHDR data
        with PngParser(self.file_name) as png:
            log.debug("Printing file")
            width = png.get_chunk_by_type(b'IHDR').width
            height = png.get_chunk_by_type(b'IHDR').height
            if png.bytesPerPixel == 1:
                # greyscale
                plt.imshow(np.array(png.reconstructed_idat_data).reshape((height, width)), cmap='gray', vmin=0, vmax=255)
                plt.show()
            elif png.bytesPerPixel == 2:
                # greyscale with alpha channel
                png.reconstructed_idat_data = np.array(png.reconstructed_idat_data).reshape((height, width, png.bytesPerPixel))
                grayscale = png.reconstructed_idat_data[:, :, 0]
                alpha = png.reconstructed_idat_data[:, :, 1]
                rgb_img = np.dstack((grayscale, grayscale, grayscale, alpha))
                plt.imshow(rgb_img)
                plt.show()
            else:
                # truecolor, truecolor with alpha channel, pallette
                plt.imshow(np.array(png.reconstructed_idat_data).reshape((height, width, png.bytesPerPixel)))
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
    # - Code refactor
    # - Improve debug logs
    # - Improve docstrings
    # - Cleaning file from rubbish and unnecessry
    # - Spectrum diagram
    # - Print summary of chunks number
    # - Add support for few other chunks
    # - Improve readme
    # - Improve chunks info print (colors)
    # - Asserts!
