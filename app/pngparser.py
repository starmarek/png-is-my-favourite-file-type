import logging
import zlib
import chunk as ch

log = logging.getLogger(__name__)

PNG_MAGIC_NUMBER = b'\x89PNG\r\n\x1a\n'

class PngParser:
    def __init__(self, file_name):
        log.debug('Openning file')
        self.file = open(file_name, 'rb')
        self.chunks = []
        self.reconstructed_idat_data = []

        log.debug('Checking signature')
        if self.file.read(len(PNG_MAGIC_NUMBER)) != PNG_MAGIC_NUMBER:
            raise Exception(f'{self.file.name} is not a PNG!')
        log.debug('Start Reading Chunks')
        self.read_chunks()
        self.process_ihdr_data()
        self.process_idat_data()

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
            length = self.read_from_file(ch.Chunk.LENGTH_FIELD_LEN)
            type_ = self.read_from_file(ch.Chunk.TYPE_FIELD_LEN)
            data = self.read_from_file(int.from_bytes(length, 'big'))
            crc = self.read_from_file(ch.Chunk.CRC_FIELD_LEN)

            chunk_class_type = ch.CHUNKTYPES.get(type_, ch.Chunk)
            chunk = chunk_class_type(length, type_, data, crc)

            self.chunks.append(chunk)

            if chunk.type_ == b'IEND':
                break

    def process_ihdr_data(self):
        self.width = self.chunks[0].width
        self.height = self.chunks[0].height
        self.bit_depth = self.chunks[0].bit_depth
        self.color_type = self.chunks[0].color_type
        self.compression_method = self.chunks[0].compression_method
        self.filter_method = self.chunks[0].filter_method
        self.interlace_method = self.chunks[0].interlace_method

    def process_idat_data(self):
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
            return self.reconstructed_idat_data[r * stride + c - bytesPerPixel] if c >= bytesPerPixel else 0

        def recon_b(r, c):
            return self.reconstructed_idat_data[(r-1) * stride + c] if r > 0 else 0

        def recon_c(r, c):
            return self.reconstructed_idat_data[(r-1) * stride + c - bytesPerPixel] if r > 0 and c >= bytesPerPixel else 0

        IDAT_data = b''.join(chunk.data for chunk in self.chunks if chunk.type_ == b'IDAT')
        IDAT_data = zlib.decompress(IDAT_data)

        bytesPerPixel = 4
        stride = self.width * bytesPerPixel

        i = 0
        for r in range(self.height): # for each scanline
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

    def print_chunks(self, skip_idat_data):
        for i, chunk in enumerate(self.chunks, 1):
            print(f"\033[1mCHUNK #{i}\033[0m")
            if chunk.type_ == b"IDAT" and skip_idat_data:
                tmp = chunk.data; chunk.data = ''
                print(chunk)
                chunk.data = tmp; continue
            print(chunk)
