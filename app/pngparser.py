import logging
import zlib
from chunk import CHUNKTYPES, Chunk, IHDR, IDAT, PLTE, temporary_data_change

log = logging.getLogger(__name__)

PNG_MAGIC_NUMBER = b'\x89PNG\r\n\x1a\n'

class PngParser:
    def __init__(self, file_name, print_mode=False):
        log.debug('Openning file')
        self.file = open(file_name, 'rb')

        self.chunks = []
        self.chunks_count = {}

        log.debug('Checking signature')
        if self.file.read(len(PNG_MAGIC_NUMBER)) != PNG_MAGIC_NUMBER:
            raise Exception(f'{self.file.name} is not a PNG!')

        log.debug('Reading Chunks')
        self.read_chunks()

        log.debug('Asserting PNG data')
        self.assert_png()

        if print_mode:
            log.debug('Proccessing IDAT')
            self.reconstructed_idat_data = []

            self.process_idat_data()

            if self.chunks_count.get(b'PLTE'):
                log.debug('Applaying pallette')
                self.apply_pallette()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, value, traceback):
        if ex_type:
            print(f'Error {ex_type}: {value}\n{traceback}')
        log.debug('Closing file')
        self.file.close()

    def read_from_file(self, amount_of_bytes_to_read):
        return self.file.read(amount_of_bytes_to_read)

    def read_chunks(self):
        while True:
            length = self.read_from_file(Chunk.LENGTH_FIELD_LEN)
            if not length:
                break
            type_ = self.read_from_file(Chunk.TYPE_FIELD_LEN)
            data = self.read_from_file(int.from_bytes(length, 'big'))
            crc = self.read_from_file(Chunk.CRC_FIELD_LEN)

            chunk_class_type = CHUNKTYPES.get(type_, Chunk)
            chunk = chunk_class_type(length, type_, data, crc)

            self.chunks.append(chunk)
            self.chunks_count[type_] = self.chunks_count.get(type_, 0) + 1

    def process_idat_data(self):
        color_type_to_bytes_per_pixel_ratio = {
            0: 1,
            2: 3,
            3: 1,
            4: 2,
            6: 4
        }

        def paeth_predictor(a, b, c):
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                Pr = a
            elif pb <= pc:
                Pr = b
            else:
                Pr = c
            return Pr

        def recon_a(r, c):
            return self.reconstructed_idat_data[r * stride + c - self.bytesPerPixel] if c >= self.bytesPerPixel else 0

        def recon_b(r, c):
            return self.reconstructed_idat_data[(r-1) * stride + c] if r > 0 else 0

        def recon_c(r, c):
            return self.reconstructed_idat_data[(r-1) * stride + c - self.bytesPerPixel] if r > 0 and c >= self.bytesPerPixel else 0

        IDAT_data = b''.join(chunk.data for chunk in self.get_all_chunks_by_type(b'IDAT'))
        IDAT_data = zlib.decompress(IDAT_data)

        self.bytesPerPixel = color_type_to_bytes_per_pixel_ratio.get(self.get_chunk_by_type(b'IHDR').color_type)
        width = self.get_chunk_by_type(b'IHDR').width
        height = self.get_chunk_by_type(b'IHDR').height
        expected_IDAT_data_len = height * (1 + width * self.bytesPerPixel)

        assert expected_IDAT_data_len == len(IDAT_data), "Image's decompressed IDAT data is not as expected. Corrupted image"
        stride = width * self.bytesPerPixel

        i = 0
        for r in range(height): # for each scanline
            filter_type = IDAT_data[i] # first byte of scanline is filter type
            i += 1
            for c in range(stride): # for each byte in scanline
                filt_x = IDAT_data[i]
                i += 1
                if filter_type == 0: # None
                    recon_x = filt_x
                elif filter_type == 1: # Sub
                    recon_x = filt_x + recon_a(r, c)
                elif filter_type == 2: # Up
                    recon_x = filt_x + recon_b(r, c)
                elif filter_type == 3: # Average
                    recon_x = filt_x + (recon_a(r, c) + recon_b(r, c)) // 2
                elif filter_type == 4: # Paeth
                    recon_x = filt_x + paeth_predictor(recon_a(r, c), recon_b(r, c), recon_c(r, c))
                else:
                    raise Exception('unknown filter type: ' + str(filter_type))
                self.reconstructed_idat_data.append(recon_x & 0xff) # truncation to byte

    def assert_png(self):
        ihdr_chunk = self.get_chunk_by_type(b'IHDR')
        first_idat_occurence = min(idx for idx, val in enumerate(self.chunks) if isinstance(val, IDAT))

        def assert_ihdr():
            log.debug('Assert IHDR')
            color_type_to_bit_depth_restriction = {
                0: [1, 2, 4, 8, 16],
                2: [8, 16],
                3: [1, 2, 4, 8],
                4: [8, 16],
                6: [8, 16]
            }
            assert self.chunks_count.get(b'IHDR') == 1, f"Incorrect number of IHDR chunks: {self.chunks_count.get(b'IHDR')}"
            assert isinstance(self.chunks[0], IHDR), "IHDR must be the first chunk"
            assert ihdr_chunk.width > 0, "Image width must be > 0"
            assert ihdr_chunk.height > 0, "Image height must be > 0"
            assert ihdr_chunk.bit_depth in [1, 2, 4, 8, 16], f"Wrong bit_depth: {ihdr_chunk.bit_depth}. It must be one of: 1, 2, 4, 8 ,16"
            assert ihdr_chunk.color_type in [0, 2, 3, 4, 6], f"Wrong color_type: {ihdr_chunk.color_type}. It must be one of: 0, 2, 3, 4 ,16"
            assert ihdr_chunk.bit_depth in color_type_to_bit_depth_restriction.get(ihdr_chunk.color_type), (f"Wrong color_type to bit_depth combination: {ihdr_chunk.color_type} : {ihdr_chunk.bit_depth}"
                                                                                                f"\nIt must be one of: {color_type_to_bit_depth_restriction}"
                                                                                                )
            assert ihdr_chunk.compression_method == 0, f"Unsupported compression_method: {ihdr_chunk.compression_method}. Only 0 is supported."
            assert ihdr_chunk.filter_method == 0, f"Unsupported filter_method: {ihdr_chunk.filter_method}. Only 0 is supported."
            # We do not support Adam7 interlace
            assert ihdr_chunk.interlace_method == 0, f"Unsupported interlace_method: {ihdr_chunk.interlace_method}. Only 0 is supported."

        def assert_idat():
            log.debug('Assert IDAT')
            assert self.chunks_count.get(b'IDAT'), f"Incorrect number of IDAT chunks: {self.chunks_count.get(b'IDAT')}"

            last_idat_occurence = max(idx for idx, val in enumerate(self.chunks) if isinstance(val, IDAT))
            only_idat_interval = self.chunks[first_idat_occurence : last_idat_occurence + 1]

            assert all(isinstance(obj, IDAT) for obj in only_idat_interval), "IDAT chunks must be consecutive!"

        def assert_plte():
            plte_chunks_number = self.chunks_count.get(b'PLTE')
            if not plte_chunks_number:
                return

            log.debug('Assert PLTE')
            if ihdr_chunk.color_type != 3:
                assert ihdr_chunk.color_type == 2 or ihdr_chunk.color_type == 6, f"PLTE chunk must not appear for color type {ihdr_chunk.color_type}!"

            plte_chunk = self.get_chunk_by_type(b'PLTE')
            plte_index = self.chunks.index(plte_chunk)

            assert plte_chunks_number == 1, f"Incorrect number of PLTE chunks: {plte_chunks_number}!"
            assert first_idat_occurence > plte_index, "PLTE must be placed before IDAT!"
            assert len(plte_chunk.get_parsed_data()) <= 2 ** ihdr_chunk.bit_depth, "Number of pallette entries shall not exceed 2^bit_depth!"
            assert int.from_bytes(plte_chunk.length, 'big') % 3 == 0, "PLTE chunk length is not divisible by 3!"

        def assert_iend():
            log.debug('Assert IEND')
            assert self.chunks_count.get(b'IEND') == 1, f"Incorrect number of IEND chunks: {self.chunks_count.get(b'IEND')}"
            assert self.chunks[-1].type_ == b'IEND', "IEND must be the last chunk"
            assert len(self.get_chunk_by_type(b'IEND').data) == 0, "IEND chunk must be empty"

        def assert_time():
            time_chunks_number = self.chunks_count.get(b'tIME')
            if not time_chunks_number:
                return

            log.debug('Assert tIME')
            assert time_chunks_number == 1, f"Incorrect number of tIME chunks: {time_chunks_number}"

        assert_ihdr()
        assert_idat()
        assert_plte()
        assert_iend()
        assert_time()

    def get_chunk_by_type(self, type_):
        try:
            return [chunk for chunk in self.chunks if chunk.type_ == type_][0]
        except IndexError:
            return None

    def get_all_chunks_by_type(self, type_):
        return [chunk for chunk in self.chunks if chunk.type_ == type_]

    def apply_pallette(self):
        pallette = self.get_chunk_by_type(b'PLTE').get_parsed_data()
        self.reconstructed_idat_data = [pixel for indexed_pixel in self.reconstructed_idat_data for pixel in pallette[indexed_pixel]]

        # apply_pallette replaced indexed pixels in reconstructed_idat_data with corresponding RGB pixels, thus number of bytes per pixel has increased from 1 to 3
        self.bytesPerPixel = 3

    def print_chunks(self, skip_idat_data, skip_plte_data):
        for i, chunk in enumerate(self.chunks, 1):
            print(f"\033[1mCHUNK #{i}\033[0m")
            if isinstance(chunk, IDAT) and skip_idat_data:
                with temporary_data_change(chunk, ''):
                    print(chunk)
                    continue
            elif isinstance(chunk, PLTE) and skip_plte_data:
                with temporary_data_change(chunk, ''):
                    print(chunk)
                    continue
            print(chunk)
        print("\033[4mChunks summary\033[0m:")
        for key, value in self.chunks_count.items():
            print (key.decode('utf-8'), ':', value)
