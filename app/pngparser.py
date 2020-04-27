import logging
import zlib
import math
from chunks import CHUNKTYPES, Chunk, IHDR, IDAT, PLTE, temporary_data_change

log = logging.getLogger(__name__)

class PngParser:
    """Parse PNG

    PNG is read, asserted, and its data is distributed among Chunk based objects.
    Next up, IDAT chunk is processed. If there is a PLTE chunk, pallette is also aplied.
    Finally gamma normalization is aplied if gAMA chunk is present.
    """
    def __init__(self, png, no_gamma_mode):
        self.png = png
        log.debug('Checking signature')
        if png.file.read(len(png.PNG_MAGIC_NUMBER)) != png.PNG_MAGIC_NUMBER:
            raise Exception(f'{png.file.name} is not a PNG!')

        self.read_chunks()
        self.assert_png()
        self.process_idat_data()
        if self.png.assert_existance(b'PLTE'):
            self.apply_pallette()
        if self.png.assert_existance(b'gAMA') and not no_gamma_mode:
            if self.png.get_chunk_by_type(b'gAMA').gamma == 0:
                log.warning("Skipping gamma normalization because gamma have value 0!")
            else:
                self.apply_gamma()

    def read_chunks(self):
        log.debug('Reading Chunks')
        while True:
            length = self.png.file.read(Chunk.LENGTH_FIELD_LEN)
            # If length is empty, we have reached and of the file
            if not length:
                break
            type_ = self.png.file.read(Chunk.TYPE_FIELD_LEN)
            data = self.png.file.read(int.from_bytes(length, 'big'))
            crc = self.png.file.read(Chunk.CRC_FIELD_LEN)

            # Initialize new chunk with class that CHUNKTYPES is pointing to. If new chunk
            # is not mentioned in CHUNKTYPES, Chunk base class is initialized.
            chunk_class_type = CHUNKTYPES.get(type_, Chunk)
            chunk = chunk_class_type(length, type_, data, crc)

            self.png.chunks.append(chunk)
            self.png.chunks_count[type_] = self.png.chunks_count.get(type_, 0) + 1

    def process_idat_data(self):
        """Decompress and defilter IDAT data

        This method is taken from this tutorial:
        https://pyokagan.name/blog/2019-10-14-png/
        Solid explanation is also available there.
        """
        log.debug('Proccessing IDAT')
        # Byte per pixel is a measure of chunks within the pixel. E.g. RGB (type 2) has three chunks -> (R, G, B)
        # RGBA (type 6) has four chunks -> (R, G, B, A).
        color_type_to_bytes_per_pixel_ratio = {
            0: 1,
            2: 3,
            3: 1,
            4: 2,
            6: 4
        }

        IDAT_data = b''.join(chunk.data for chunk in self.png.get_all_chunks_by_type(b'IDAT'))
        # DECOMPRESSING
        IDAT_data = zlib.decompress(IDAT_data)

        self.png.bytesPerPixel = color_type_to_bytes_per_pixel_ratio.get(self.png.get_chunk_by_type(b'IHDR').color_type)
        width = self.png.get_chunk_by_type(b'IHDR').width
        height = self.png.get_chunk_by_type(b'IHDR').height
        expected_IDAT_data_len = height * (1 + width * self.png.bytesPerPixel)

        assert expected_IDAT_data_len == len(IDAT_data), "Image's decompressed IDAT data is not as expected. Corrupted image"
        stride = width * self.png.bytesPerPixel

        # DEFINING DEFILTER FUNCTIONS
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
            return self.png.reconstructed_idat_data[r * stride + c - self.png.bytesPerPixel] if c >= self.png.bytesPerPixel else 0

        def recon_b(r, c):
            return self.png.reconstructed_idat_data[(r-1) * stride + c] if r > 0 else 0

        def recon_c(r, c):
            return self.png.reconstructed_idat_data[(r-1) * stride + c - self.png.bytesPerPixel] if r > 0 and c >= self.png.bytesPerPixel else 0

        # DEFILTER
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
                self.png.reconstructed_idat_data.append(recon_x & 0xff) # truncation to byte

    def assert_png(self):
        """ Asserts PNG data according to PNG specification

        Specification:
        http://www.libpng.org/pub/png/spec/1.2/PNG-Structure.html
        https://www.w3.org/TR/2003/REC-PNG-20031110/ (newer version)
        """
        log.debug('Asserting PNG data')
        ihdr_chunk = self.png.get_chunk_by_type(b'IHDR')
        first_idat_occurence = min(idx for idx, val in enumerate(self.png.chunks) if isinstance(val, IDAT))

        def assert_ihdr():
            log.debug('Assert IHDR')
            color_type_to_bit_depth_restriction = {
                0: [1, 2, 4, 8, 16],
                2: [8, 16],
                3: [1, 2, 4, 8],
                4: [8, 16],
                6: [8, 16]
            }
            assert self.png.chunks_count.get(b'IHDR') == 1, f"Incorrect number of IHDR chunks: {self.png.chunks_count.get(b'IHDR')}"
            assert isinstance(self.png.chunks[0], IHDR), "IHDR must be the first chunk"
            assert ihdr_chunk.width > 0, "Image width must be > 0"
            assert ihdr_chunk.height > 0, "Image height must be > 0"
            assert ihdr_chunk.bit_depth in [1, 2, 4, 8, 16], f"Wrong bit_depth: {ihdr_chunk.bit_depth}. It must be one of: 1, 2, 4, 8 ,16"
            assert ihdr_chunk.color_type in [0, 2, 3, 4, 6], f"Wrong color_type: {ihdr_chunk.color_type}. It must be one of: 0, 2, 3, 4 ,16"
            assert ihdr_chunk.bit_depth in color_type_to_bit_depth_restriction.get(ihdr_chunk.color_type), (
                                    f"Wrong color_type to bit_depth combination: {ihdr_chunk.color_type} : {ihdr_chunk.bit_depth}"
                                    f"\nIt must be one of: {color_type_to_bit_depth_restriction}"
                                    )
            assert ihdr_chunk.compression_method == 0, f"Unsupported compression_method: {ihdr_chunk.compression_method}. Only 0 is supported."
            assert ihdr_chunk.filter_method == 0, f"Unsupported filter_method: {ihdr_chunk.filter_method}. Only 0 is supported."
            # We do not support Adam7 interlace
            assert ihdr_chunk.interlace_method == 0, f"Unsupported interlace_method: {ihdr_chunk.interlace_method}. Only 0 is supported."

        def assert_idat():
            log.debug('Assert IDAT')
            assert self.png.chunks_count.get(b'IDAT'), f"Incorrect number of IDAT chunks: {self.png.chunks_count.get(b'IDAT')}"

            last_idat_occurence = max(idx for idx, val in enumerate(self.png.chunks) if isinstance(val, IDAT))
            only_idat_interval = self.png.chunks[first_idat_occurence : last_idat_occurence + 1]

            assert all(isinstance(obj, IDAT) for obj in only_idat_interval), "IDAT chunks must be consecutive!"

        def assert_plte():
            plte_chunks_number = self.png.chunks_count.get(b'PLTE')
            if not plte_chunks_number:
                return

            log.debug('Assert PLTE')
            if ihdr_chunk.color_type != 3:
                assert ihdr_chunk.color_type == 2 or ihdr_chunk.color_type == 6, f"PLTE chunk must not appear for color type {ihdr_chunk.color_type}!"

            plte_chunk = self.png.get_chunk_by_type(b'PLTE')
            plte_index = self.png.chunks.index(plte_chunk)

            assert plte_chunks_number == 1, f"Incorrect number of PLTE chunks: {plte_chunks_number}!"
            assert first_idat_occurence > plte_index, "PLTE must be placed before IDAT!"
            assert len(plte_chunk.get_parsed_data()) <= 2 ** ihdr_chunk.bit_depth, "Number of pallette entries shall not exceed 2^bit_depth!"
            assert int.from_bytes(plte_chunk.length, 'big') % 3 == 0, "PLTE chunk length is not divisible by 3!"

        def assert_iend():
            log.debug('Assert IEND')
            assert self.png.chunks_count.get(b'IEND') == 1, f"Incorrect number of IEND chunks: {self.png.chunks_count.get(b'IEND')}"
            assert self.png.chunks[-1].type_ == b'IEND', "IEND must be the last chunk"
            assert len(self.png.get_chunk_by_type(b'IEND').data) == 0, "IEND chunk must be empty"

        def assert_time():
            time_chunks_number = self.png.chunks_count.get(b'tIME')
            if not time_chunks_number:
                return

            log.debug('Assert tIME')
            assert time_chunks_number == 1, f"Incorrect number of tIME chunks: {time_chunks_number}"

        def assert_gama():
            gama_chunks_number = self.png.chunks_count.get(b'gAMA')
            if not gama_chunks_number:
                return

            log.debug('Assert gAMA')
            gama_chunk = self.png.get_chunk_by_type(b'gAMA')
            gama_index = self.png.chunks.index(gama_chunk)

            assert gama_chunks_number == 1, f"Incorrect number of gAMA chunks: {gama_chunks_number}"
            assert first_idat_occurence > gama_index, "gAMA must be placed before IDAT!"
            if self.png.assert_existance(b'PLTE'):
                assert self.png.chunks.index(self.get_chunk_by_type(b'PLTE')) > gama_index, "gAMA must be placed before PLTE!"

        def assert_chrm():
            chrm_chunks_number = self.png.chunks_count.get(b'cHRM')
            if not chrm_chunks_number:
                return

            log.debug('Assert cHRM')
            chrm_chunk = self.png.get_chunk_by_type(b'cHRM')
            chrm_index = self.png.chunks.index(chrm_chunk)

            assert chrm_chunks_number == 1, f"Incorrect number of cHRM chunks: {chrm_chunks_number}"
            assert first_idat_occurence > chrm_index, "cHRM must be placed before IDAT!"
            if self.png.assert_existance(b'PLTE'):
                assert self.png.chunks.index(self.png.get_chunk_by_type(b'PLTE')) > chrm_index, "cHRM must be placed before PLTE!"

        assert_ihdr()
        assert_chrm()
        assert_gama()
        assert_plte()
        assert_idat()
        assert_iend()
        assert_time()

    def apply_pallette(self):
        """Replace indexed pixels in parsed IDAT with according pallette RGB values
        """
        log.debug('Applaying pallette')
        pallette = self.png.get_chunk_by_type(b'PLTE').get_parsed_data()
        # In next step: take indexed_pixel (index of pallette entry) from parsed IDAT. Find pallette entry which has this list index, and replace them.
        # If still confused -> please google how indexed colors work
        self.png.reconstructed_idat_data = [pixel for indexed_pixel in self.png.reconstructed_idat_data for pixel in pallette[indexed_pixel]]

        # apply_pallette replaced indexed pixels in reconstructed_idat_data with corresponding RGB pixels, thus number of bytes per pixel has increased from 1 to 3
        self.png.bytesPerPixel = 3

    def apply_gamma(self):
        """Apply gamma normalization, to parsed IDAT pixels
        """
        log.debug('Applying gamma normalization')
        gamma = self.png.get_chunk_by_type(b'gAMA').gamma

        # This is basically the definition of bith depth.
        # 2^bit_depth - 1 -> 255 for 8-bit | 31 for 5-bit etc.
        max_colors_in_sample = 2 ** self.png.get_chunk_by_type(b'IHDR').bit_depth - 1
        invGamma = 1.0 / gamma

        # Steps to apply gamma:
        # 1. Normalize pixels from [0, max_colors_in_sample] to [0, 1.0]
        # 2. Aplly gamma via equation: output = input ^ (1 / gamma)
        # 3. Reverse normalize output to [0, max_colors_in_sample]
        # 4. Finally do: floor(output + 0.5)
        # https://www.w3.org/TR/2003/REC-PNG-20031110/#13Decoder-gamma-handling
        self.png.reconstructed_idat_data = [math.floor((((pixel / max_colors_in_sample) ** invGamma) * max_colors_in_sample) + 0.5) for pixel in self.png.reconstructed_idat_data]
