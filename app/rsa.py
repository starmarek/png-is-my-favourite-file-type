from keygenerator import KeyGenerator
from collections import deque
from pngImage import Png

try:
    import gmpy2 as g
    import png
except ModuleNotFoundError:
    traceback.print_exc()
    print("\033[1;33mBefore you will debug, please delete 'venv' dir from project root and try again.\033[0m")
    exit(1)

class RSA:
    def __init__(self, png, key_size):
        self.png = png
        assert png.get_chunk_by_type(b'IHDR').color_type != 3, "Our RSA do not support pallette"
        self.public_key, self.private_key = KeyGenerator(key_size).generateKeys()
        self.encrypted_png_path = "encrypted.png"
        
        # chunk should be a bit smaller than key length in order for RSA to work properly => math stuff
        self.amount_of_bytes_to_substract_from_chunk_size = 1
        self.encrypted_chunk_size_in_bytes = key_size // 8 - self.amount_of_bytes_to_substract_from_chunk_size

    def ECB_encrypt_decompressed_data(self):
        cipher_data = []

        for i in range(0, len(self.png.reconstructed_idat_data), self.encrypted_chunk_size_in_bytes):
            chunk_to_encrypt_hex = bytes(self.png.reconstructed_idat_data[i: i + self.encrypted_chunk_size_in_bytes])

            cipher_int = g.powmod(int.from_bytes(chunk_to_encrypt_hex, 'big'), self.public_key[0], self.public_key[1])

            cipher_hex = int(cipher_int).to_bytes(self.encrypted_chunk_size_in_bytes + self.amount_of_bytes_to_substract_from_chunk_size, 'big')

            for i in range(self.encrypted_chunk_size_in_bytes):
                cipher_data.append(cipher_hex[i])

        self.create_encrypted_png(cipher_data)

    def create_encrypted_png(self, cipher_data):
        idat_data, after_iend_data = self.extract_after_iend_pixels(cipher_data)
        bytes_row_width = self.png.get_chunk_by_type(b'IHDR').width * self.png.bytesPerPixel
        if self.png.bytesPerPixel == 1:
            png_writer = png.Writer(self.png.get_chunk_by_type(b'IHDR').width, self.png.get_chunk_by_type(b'IHDR').height, greyscale=True)
        elif self.png.bytesPerPixel == 2:
            png_writer = png.Writer(self.png.get_chunk_by_type(b'IHDR').width, self.png.get_chunk_by_type(b'IHDR').height, greyscale=True, alpha=True)
        elif self.png.bytesPerPixel == 3:
            png_writer = png.Writer(self.png.get_chunk_by_type(b'IHDR').width, self.png.get_chunk_by_type(b'IHDR').height, greyscale=False)
        elif self.png.bytesPerPixel == 4:
            png_writer = png.Writer(self.png.get_chunk_by_type(b'IHDR').width, self.png.get_chunk_by_type(b'IHDR').height, greyscale=False, alpha=True)            

        f = open(self.encrypted_png_path, 'wb')
        pixels_grouped_by_rows = [idat_data[i: i + bytes_row_width] for i in range(0, len(idat_data), bytes_row_width)]
        png_writer.write(f, pixels_grouped_by_rows)
        f.write(bytes(after_iend_data))
        f.close()

    def extract_after_iend_pixels(self, cipher_data):
        """
        The side effect of using the ECB mode with RSA is that IDAT length gets bigger.
        In order to NOT CHANGE THE METADATA, we are using hack.
        The hack is to put new pixels after IEND chunk, so image can be displayed properly AND
        further deciphering operation can be successfull.
        """
        cipher_data = deque(cipher_data)
        idat_data = []
        after_iend_data = []

        for i in range(len(self.png.reconstructed_idat_data)):
            idat_data.append(cipher_data.popleft())
        for i in range(len(cipher_data)):
            after_iend_data.append(cipher_data.popleft())
        
        return idat_data, after_iend_data
