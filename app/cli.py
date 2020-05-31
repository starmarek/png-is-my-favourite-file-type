import logging
import traceback
from pngparser import PngParser
from pngImage import Png
from rsa import RSA

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
        verbose (bool, optional):  Optional. Defaults to False. Print additional logs which should help in application debugging proccess.
        no_gamma (bool, optional): OPtional. Determines, whether gamma should be aplied (if exists).
    """

    def __init__(self, file_name="png_files/dice.png", verbose=False, no_gamma=False):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_name = file_name
        self.verbose = verbose
        self.no_gamma = no_gamma

        if self.verbose:
            log.setLevel(logging.DEBUG)

        self.png = Png(self.file_name)
        self.png.parse(no_gamma)

    def __del__(self):
        # Show image if it has been loaded to memory by plt.imshow()
        # This is the very last thing in the program execution
        plt.show()

    def metadata(self, idat=False, plte=False):
        """Print PNG's metadata in good-looking way
        """
        log.debug("Printing metadata")
        self.png.print_chunks(idat, plte)

    def print(self):
        """Print PNG from reconstructed IDAT data using matplotlib
        """
        log.debug("Printing file")
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
        self.png.create_clean_copy(output_file)

    def fullservice(self, output_file='new.png', idat=False, plte=False):
        """Launch all functionality of package in controlled and automated way

        It might be somehow called 'presentation mode'.

        1. print info about png
        2. create new png with only critical chunks in it
        3. also print info about this new png
        4. summarize chunks that were deleted during process
        5. show spectrum of original png
        6. print png's next to each other
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
        self.print()
        self.clean(output_file)
        self.spectrum()

        print('=' * 100)

        f3 = plt.figure(3)
        plt.subplot(122)
        plt.title("After cleanup", fontweight='bold', fontsize=20)
        new_png = Png(output_file)
        new_png.parse(self.no_gamma)
        original_png = self.png; self.png = new_png
        self.metadata(idat, plte)
        self.print()

        print('=' * 100)

        print_chunks_difference(original_png.chunks_count, self.png.chunks_count)

    def rsa(self, key_size=1024, encrypted_file_path="encrypted.png", decrypted_file_path="decrypted.png", mode="ECB"):
        assert self.png.get_chunk_by_type(b'IHDR').color_type != 3, "RSA module do not support pallette"
        rsa = RSA(key_size)

        if mode == "ECB":
            cipher, after_iend_data_embedded = rsa.ECB_encrypt(self.png.reconstructed_idat_data)
        elif mode == "CBC":
            cipher, after_iend_data_embedded = rsa.CBC_encrypt(self.png.reconstructed_idat_data)
        else:
            log.error("Unkown cipher method. Quitting...")
            exit(1)
        rsa.create_encrypted_png(cipher, self.png.bytesPerPixel, self.png.get_chunk_by_type(b'IHDR').width,
                                    self.png.get_chunk_by_type(b'IHDR').height, encrypted_file_path, after_iend_data_embedded)

        log.info("Parsing encrypted file")
        new_png = Png(encrypted_file_path)
        new_png.parse(True)

        if mode == "ECB":
            decrypted_data = rsa.ECB_decrypt(new_png.reconstructed_idat_data, new_png.after_iend_data)
        elif mode == "CBC":
            decrypted_data = rsa.CBC_decrypt(new_png.reconstructed_idat_data, new_png.after_iend_data)
        rsa.create_decrypted_png(decrypted_data, new_png.bytesPerPixel, new_png.get_chunk_by_type(b"IHDR").width,
                                    new_png.get_chunk_by_type(b"IHDR").height, decrypted_file_path)

if __name__ == '__main__':
    fire.Fire(CLI)
