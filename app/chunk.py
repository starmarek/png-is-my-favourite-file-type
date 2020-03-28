import struct
import logging

log = logging.getLogger(__name__)

class Chunk:
    LENGTH_FIELD_LEN = 4
    TYPE_FIELD_LEN = 4
    CRC_FIELD_LEN = 4

    def __init__(self, length, type_, data, crc):
        log.debug(f'Creating {type_} chunk')
        self.length = length
        self.type_ = type_
        self.data = data
        self.crc = crc

    def __str__(self):
        return (f"Length: {int.from_bytes(self.length, 'big')}\nType: {self.type_.decode('utf-8')}\n"
                    f"Data: {self.data}\nCRC: {self.crc.hex(' ')}\n")

class IHDR(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

        values = struct.unpack('>iibbbbb', self.data)
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
