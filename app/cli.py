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
            png.print_chunks(skip_idat_data)

    def print(self):
        # print PNG from reconstructed IHDR data
        with PngParser(self.file_name) as png:
            if png.bytesPerPixel == 1:
                plt.imshow(np.array(png.reconstructed_idat_data).reshape((png.height, png.width)), cmap='gray', vmin=0, vmax=255)
            else:
                plt.imshow(np.array(png.reconstructed_idat_data).reshape((png.height, png.width, png.bytesPerPixel)))
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
    # - Code refactor
    # - Implement IDAT class
    # - Improve debug logs
    # - Improve docstrings
