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
     - clean
     - fullservice

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
        # Show image if it has been loaded to memory by plt.imshow()
        # This is the very last thing in the program execution
        plt.show()

    def metadata(self, idat=False, plte=False):
        """Print PNG's metadata in good-looking way
        """
        log.debug("Printing metadata")
        self.png.print_chunks(idat, plte)

    def print(self, no_gamma=False):
        """Print PNG from reconstructed IDAT data using matplotlib
        """
        log.debug("Printing file")
        self.png.enable_print_mode(no_gamma)
        width = self.png.get_chunk_by_type(b'IHDR').width
        height = self.png.get_chunk_by_type(b'IHDR').height
        if self.png.bytesPerPixel == 1:
            # greyscale
            plt.imshow(np.array(self.png.reconstructed_idat_data).reshape((height, width)), cmap='gray', vmin=0, vmax=255)
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
        """Create brand new file with chunks that are TOTTALLY NECESSARY. Other chunks are discarded
        """
        self.png.create_clean_png(output_file)

    def fullservice(self, output_file='new.png', no_gamma=False, idat=False, plte=False):
        """Launch all functionality of package in controlled and automated way

        It might be somehow called 'presentation mode'.

        1. print info about png
        2. create new png with only critical chunks in it
        3. also print info about this new png
        4. summarize chunks that were deleted during process
        5. print png's next to each other
        """
        def print_chunks_difference(dict1, dict2):
            chunks_difference = set(dict1.items()) ^ set(dict2.items())
            print("\033[4mRemoved chunks\033[0m:")
            for dict_tuple in chunks_difference:
                print(dict_tuple[0].decode('utf-8'), ':', dict_tuple[1])

        plt.subplot(121)
        plt.title("Before cleanup", fontweight='bold', fontsize=20)
        self.metadata(idat, plte)
        self.print(no_gamma)
        self.clean(output_file)

        print('=' * 100)

        plt.subplot(122)
        plt.title("After cleanup", fontweight='bold', fontsize=20)
        new_entrypoint = CLI(output_file)
        new_entrypoint.metadata(idat, plte)
        new_entrypoint.print(no_gamma)

        print('=' * 100)

        print_chunks_difference(self.png.chunks_count, new_entrypoint.png.chunks_count)

if __name__ == '__main__':
    fire.Fire(CLI)
    # TODO:
    # - Spectrum diagram
