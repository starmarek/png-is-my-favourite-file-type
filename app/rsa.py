from keygenerator import KeyGenerator
from collections import deque
from pngImage import Png
import logging
import random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome import Random
from Cryptodome.PublicKey import RSA
import Cryptodome as crypto

log = logging.getLogger(__name__)

try:
    import png
except ModuleNotFoundError:
    traceback.print_exc()
    print("\033[1;33mBefore you will debug, please delete 'venv' dir from project root and try again.\033[0m")
    exit(1)

class _RSA:
    def __init__(self, key_size):
        log.info("Initializing RSA module")
        self.public_key, self.private_key = KeyGenerator(key_size).generateKeys()
        self.key_size = key_size

        # chunk that goes to encryption should be a bit smaller than key length in order for RSA to work properly => math stuff
        self.amount_of_bytes_to_substract_from_chunk_size = 1
        self.encrypted_chunk_size_in_bytes_substracted = key_size // 8 - self.amount_of_bytes_to_substract_from_chunk_size
        
        self.encrypted_chunk_size_in_bytes_substracted2 = key_size // 16 
        # on the other hand - chunk that has been already encrypted has the lenght of key itself
        self.encrypted_chunk_size_in_bytes = key_size // 8
        self.encrypted_chunk_size_in_bytes2 = key_size // 16

    def ECB_encrypt(self, data):
        log.info(f"Performing ECB RSA encryption using {self.key_size} bit public key")

        cipher_data = []
        after_iend_data_embedded = []
        self.original_data_len = len(data)

        for i in range(0, len(data), self.encrypted_chunk_size_in_bytes_substracted):
            chunk_to_encrypt_hex = bytes(data[i: i + self.encrypted_chunk_size_in_bytes_substracted])

            cipher_int = pow(int.from_bytes(chunk_to_encrypt_hex, 'big'), self.public_key[0], self.public_key[1])

            cipher_hex = cipher_int.to_bytes(self.encrypted_chunk_size_in_bytes, 'big')

            for i in range(self.encrypted_chunk_size_in_bytes_substracted):
                cipher_data.append(cipher_hex[i])
            after_iend_data_embedded.append(cipher_hex[-1])
        cipher_data.append(after_iend_data_embedded.pop())

        return cipher_data, after_iend_data_embedded

    def ECB_decrypt(self, data, after_iend_data):
        log.info(f"Performing ECB RSA decryption using {self.key_size} bit private key")

        data_to_decrypt = self.concentate_data_to_decrypt(data, deque(after_iend_data))
        decrypted_data = []

        for i in range(0, len(data_to_decrypt), self.encrypted_chunk_size_in_bytes):
            chunk_to_decrypt_hex = bytes(data_to_decrypt[i: i + self.encrypted_chunk_size_in_bytes])

            decrypted_int = pow(int.from_bytes(chunk_to_decrypt_hex, 'big'), self.private_key[0], self.private_key[1])

            # We don't know how long was the last original chunk (no matter what, chunks after encryption have fixd key-length size, so extra bytes could have been added), 
            # so below, before creating decrpyted_hex of fixed size we check if adding it to decrpted_data wouldn't exceed the original_data_len
            # If it does, we know that the length of last chunk was smaller and we can retrieve it's length
            if len(decrypted_data) + self.encrypted_chunk_size_in_bytes_substracted > self.original_data_len:
                # last original chunk
                decrypted_hex_len = self.original_data_len - len(decrypted_data)
            else:
                # standard encryption_RSA_chunk length
                decrypted_hex_len = self.encrypted_chunk_size_in_bytes_substracted

            decrypted_hex = decrypted_int.to_bytes(decrypted_hex_len, 'big')

            for byte in decrypted_hex:
                decrypted_data.append(byte)

        return decrypted_data

    def create_decrypted_png(self, decrpted_data, bytes_per_pixel, width, height, decrypted_png_path):
        log.info(f"Creating decrypted file '{decrypted_png_path}'")

        png_writer = self.get_png_writer(width, height, bytes_per_pixel)
        bytes_row_width = width * bytes_per_pixel
        pixels_grouped_by_rows = [decrpted_data[i: i + bytes_row_width] for i in range(0, len(decrpted_data), bytes_row_width)]

        f = open(decrypted_png_path, 'wb')
        png_writer.write(f, pixels_grouped_by_rows)
        f.close()

    def create_encrypted_png(self, cipher_data, bytes_per_pixel, width, height, encrypted_png_path, after_iend_data_embedded):
        log.info(f"Creating encrpyted file '{encrypted_png_path}'")

        idat_data, after_iend_data = self.extract_after_iend_pixels(cipher_data)
        png_writer = self.get_png_writer(width, height, bytes_per_pixel)
        bytes_row_width = width * bytes_per_pixel
        pixels_grouped_by_rows = [idat_data[i: i + bytes_row_width] for i in range(0, len(idat_data), bytes_row_width)]

        f = open(encrypted_png_path, 'wb')
        png_writer.write(f, pixels_grouped_by_rows)
        f.write(bytes(after_iend_data_embedded))
        f.write(bytes(after_iend_data))
        f.close()

    def get_png_writer(self, width, height, bytes_per_pixel):
        if bytes_per_pixel == 1:
            png_writer = png.Writer(width, height, greyscale=True)
        elif bytes_per_pixel == 2:
            png_writer = png.Writer(width, height, greyscale=True, alpha=True)
        elif bytes_per_pixel == 3:
            png_writer = png.Writer(width, height, greyscale=False)
        elif bytes_per_pixel == 4:
            png_writer = png.Writer(width, height, greyscale=False, alpha=True)

        return png_writer

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
        for i in range(self.original_data_len):
            idat_data.append(cipher_data.popleft())
        for i in range(len(cipher_data)):
            after_iend_data.append(cipher_data.popleft())
        
        return idat_data, after_iend_data

    def concentate_data_to_decrypt(self, data, after_iend_data: deque):
        data_to_decrypt = []

        for i in range(0, len(data), self.encrypted_chunk_size_in_bytes_substracted):
            data_to_decrypt.extend(data[i:i + self.encrypted_chunk_size_in_bytes_substracted])
            data_to_decrypt.append(after_iend_data.popleft())
        data_to_decrypt.extend(after_iend_data)

        return data_to_decrypt

    def CBC_encrypt(self, data):
        log.info(f"Performing CBC RSA encryption using {self.key_size} bit public key")

        cipher_data = []
        decrypted_data = []
        after_iend_data_embedded = []
        self.original_data_len = len(data)
        self.IV = random.getrandbits(self.key_size)
        prev = self.IV

        for i in range(0, len(data), self.encrypted_chunk_size_in_bytes_substracted):
            chunk_to_encrypt_hex = bytes(data[i: i + self.encrypted_chunk_size_in_bytes_substracted])

            prev = prev.to_bytes(self.encrypted_chunk_size_in_bytes, 'big')
            prev = int.from_bytes(prev[:len(chunk_to_encrypt_hex)], 'big')
            xor = int.from_bytes(chunk_to_encrypt_hex, 'big') ^ prev

            cipher_int = pow(xor, self.public_key[0], self.public_key[1])
            prev = cipher_int

            cipher_hex = cipher_int.to_bytes(self.encrypted_chunk_size_in_bytes, 'big')

            for i in range(self.encrypted_chunk_size_in_bytes_substracted):
                cipher_data.append(cipher_hex[i])
            after_iend_data_embedded.append(cipher_hex[-1])
        cipher_data.append(after_iend_data_embedded.pop())

        return cipher_data, after_iend_data_embedded

    def CBC_decrypt(self, data, after_iend_data):
        log.info(f"Performing CBC RSA decryption using {self.key_size} bit private key")

        data_to_decrypt = self.concentate_data_to_decrypt(data, deque(after_iend_data))
        decrypted_data = []
        prev = self.IV

        for i in range(0, len(data_to_decrypt), self.encrypted_chunk_size_in_bytes):
            chunk_to_decrypt_hex = bytes(data_to_decrypt[i: i + self.encrypted_chunk_size_in_bytes])

            decrypted_int = pow(int.from_bytes(chunk_to_decrypt_hex, 'big'), self.private_key[0], self.private_key[1])

            # We don't know how long was the last original chunk (no matter what, chunks after encryption have fixd key-length size, so extra bytes could have been added),
            # so below, before creating decrpyted_hex of fixed size we check if adding it to decrpted_data wouldn't exceed the original_data_len
            # If it does, we know that the length of last chunk was smaller and we can retrieve it's length
            if len(decrypted_data) + self.encrypted_chunk_size_in_bytes_substracted > self.original_data_len:
                # last original chunk
                decrypted_hex_len = self.original_data_len - len(decrypted_data)
            else:
                # standard encryption_RSA_chunk length
                decrypted_hex_len = self.encrypted_chunk_size_in_bytes_substracted

            prev = prev.to_bytes(self.encrypted_chunk_size_in_bytes, 'big')
            prev = int.from_bytes(prev[:decrypted_hex_len], 'big')
            xor = prev ^ decrypted_int
            prev = int.from_bytes(chunk_to_decrypt_hex, 'big')

            decrypted_hex = xor.to_bytes(decrypted_hex_len, 'big')

            for byte in decrypted_hex:
                decrypted_data.append(byte)

        return decrypted_data

    def Crypto_encrypt(self, data):
        log.info(f"Performing Crypto Package RSA encryption using {self.key_size} bit public key")

        cipher_data = []
        after_iend_data_embedded = []
        self.original_data_len = len(data)
        key = RSA.construct((self.public_key[1] , self.public_key[0]))
        cipher = PKCS1_OAEP.new(key)    

        for i in range(0, len(data), self.encrypted_chunk_size_in_bytes_substracted2):
            chunk_to_encrypt_hex = bytes(data[i: i + self.encrypted_chunk_size_in_bytes_substracted2])
            cipher_hex = cipher.encrypt(chunk_to_encrypt_hex)
            
            for i in range(self.encrypted_chunk_size_in_bytes_substracted2):
                cipher_data.append(cipher_hex[i])
            after_iend_data_embedded.append(cipher_hex[-1])
        cipher_data.append(after_iend_data_embedded.pop())

        return cipher_data, after_iend_data_embedded

