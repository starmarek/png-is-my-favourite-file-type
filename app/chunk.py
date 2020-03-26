import struct as st
import logging

log = logging.getLogger(__name__)

class Chunk:
    LENGTH = 4
    TYPE = 4
    DATA: int
    CRC = 4
    def __init__(self, file_handler):
        log.debug('Start parsing chunk')
        self.parse(file_handler)

    def __str__(self):
        return (f"Length: {self.length}\nType: {self.type_}\n"
                    f"Data: {self.data}\nCRC: {self.crc}\n")

    @property
    def _length(self):
        return self.length

    @_length.setter
    def _length(self, value):
        self.length = int.from_bytes(value, 'big')
        Chunk.DATA = self.length

    def parse(self, file_handler):
        self._length = file_handler.read(Chunk.LENGTH)
        self.type_ = file_handler.read(Chunk.TYPE)
        self.data = file_handler.read(Chunk.DATA)
        self.crc = file_handler.read(Chunk.CRC)


class IHDR(Chunk):
    def __init__(self, file_handler):
        super().__init__(file_handler)

        values = st.unpack('>iibbbbb', self.data)
        self.width = values[0]
        self.height = values[1]
        self.bit_depth = values[2]
        self.color_type = values[3]
        self.compression_method = values[4]
        self.filter_method = values[5]
        self.interlace_method = values[6]

    def __str__(self):
        tmp = self.data
        self.data = (f"Width: {self.width} | Height: {self.height} | BitDepth: {self.bit_depth} | ColorType: {self.color_type} | "
                        f"CompressionMethod: {self.compression_method} | FilterMethod: {self.filter_method} | InterlaceMethod {self.interlace_method}")
        try:
            return super().__str__()
        finally:
            self.data = tmp

CHUNKTYPES = {
    b"IHDR": IHDR
}
