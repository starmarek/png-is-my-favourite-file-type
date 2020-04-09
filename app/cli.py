import logging
import traceback
from pngparser import PngParser

try:
    import cv2
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
        """ Print FFT of an image (shows magnitude and phase)
            Compare original image and inverted fft of original image (checks transformation)
        """
        img=cv2.imread(self.file_name,0)
        fourier = np.fft.fft2(img) 
        fourier_shifted = np.fft.fftshift(fourier) 
    
        fourier_mag = np.asarray(20*np.log10(np.abs(fourier_shifted)) ,dtype=np.uint8) 
        fourier_phase = np.asarray(np.angle(fourier_shifted),dtype=np.uint8)

        f1 = plt.figure(1) # show source image and FFT 
        plt.subplot(131),plt.imshow(img, cmap = 'gray') 
        
        plt.title('Input Image'), plt.xticks([]), plt.yticks([])
        
        plt.subplot(132),plt.imshow(fourier_mag, cmap = 'gray')
        plt.title('FFT Magnitude'), plt.xticks([]), plt.yticks([])
        
        plt.subplot(133),plt.imshow(fourier_phase, cmap = 'gray')
        plt.title('FFT Phase'), plt.xticks([]), plt.yticks([])

        f2 = plt.figure(2) #comapare source image and inverted fft 
        fourier_inverted=np.fft.ifft2(fourier)

        plt.subplot(121),plt.imshow(img, cmap = 'gray') 
        plt.title('Input Image'), plt.xticks([]), plt.yticks([])
        plt.subplot(122),plt.imshow( np.asarray(fourier_inverted, dtype=np.uint8), cmap = 'gray')
        plt.title('Inverted Image'), plt.xticks([]), plt.yticks([])



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

        f3 = plt.figure(3)
        plt.subplot(121)
        plt.title("Before cleanup", fontweight='bold', fontsize=20)
        self.metadata(idat, plte)
        self.print(no_gamma)
        self.clean(output_file)
        self.spectrum()
        print('=' * 100)
        f3 = plt.figure(3)
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
