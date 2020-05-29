import logging
import zlib
from chunks import IDAT, PLTE, temporary_data_change
from pngparser import PngParser

log = logging.getLogger(__name__)

class Png:
    def __init__(self, file_name):
        log.debug('Openning file')
        try:
            self.file = open(file_name, 'rb')
        except IOError as e:
            raise e

        self.PNG_MAGIC_NUMBER = b'\x89PNG\r\n\x1a\n'
        self.chunks = []
        self.chunks_count = {}
        self.reconstructed_idat_data = []
        self.bytesPerPixel = 0

    def __del__(self):
        log.debug('Closing file')
        try:
            self.file.close()
        except AttributeError:
            pass
            
    
    def assert_existance(self, type_to_assert):
        return True if any(chunk.type_ == type_to_assert for chunk in self.chunks) else False

    def get_chunk_by_type(self, type_):
        try:
            return [chunk for chunk in self.chunks if chunk.type_ == type_][0]
        except IndexError:
            return None

    def get_all_chunks_by_type(self, type_):
        return [chunk for chunk in self.chunks if chunk.type_ == type_]

    def get_decompressed_idat_data(self):
        IDAT_data = b''.join(chunk.data for chunk in self.get_all_chunks_by_type(b'IDAT'))
        return zlib.decompress(IDAT_data)

    def print_chunks(self, get_idat_data, get_plte_data):
        """
        Args:
            get_idat_data(bool): If set to true, IDAT data is printed to console
            get_plte_data(bool): If set to true, PLTE data is printed to console
        """
        for i, chunk in enumerate(self.chunks, 1):
            print(f"\033[1mCHUNK #{i}\033[0m")
            # Default behavior is to enter if statements and replace data with empty strings
            # Data in those chunks is generally long and makes chunk summary less readable
            if isinstance(chunk, IDAT) and not get_idat_data:
                with temporary_data_change(chunk, ''):
                    print(chunk)
                    continue
            elif isinstance(chunk, PLTE) and not get_plte_data:
                with temporary_data_change(chunk, ''):
                    print(chunk)
                    continue
            print(chunk)
        print("\033[4mChunks summary\033[0m:")
        for key, value in self.chunks_count.items():
            print(key.decode('utf-8'), ':', value)

    def parse(self, no_gamma_mode):
        PngParser(self, no_gamma_mode)

    def create_clean_copy(self, new_file_name):
        """Creates brand new file with ONLY critical chunks in it
        """
        def get_ancilary_chunks():
            ancilary_chunks = [
                b'IHDR',
                b'IDAT',
                b'IEND'
            ]
            if self.get_chunk_by_type(b'IHDR').color_type == 3:
                ancilary_chunks.insert(1, b'PLTE')
            return ancilary_chunks

        ancilary_chunks = get_ancilary_chunks()
        file_handler = open(new_file_name, 'wb')
        file_handler.write(self.PNG_MAGIC_NUMBER)

        for chunk in self.chunks:
            if chunk.type_ in ancilary_chunks:
                file_handler.write(chunk.length)
                file_handler.write(chunk.type_)
                file_handler.write(chunk.data)
                file_handler.write(chunk.crc)

        file_handler.close()
