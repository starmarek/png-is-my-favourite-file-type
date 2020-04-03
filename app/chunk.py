import struct
import logging
from itertools import zip_longest
from contextlib import contextmanager

log = logging.getLogger(__name__)

@contextmanager
def temporary_data_change(object_to_change, tmp_data):
    original_data = getattr(object_to_change, 'data')
    setattr(object_to_change, 'data', tmp_data)
    try:
        yield
    finally:
        setattr(object_to_change, 'data', original_data)

class Chunk:
    LENGTH_FIELD_LEN = 4
    TYPE_FIELD_LEN = 4
    CRC_FIELD_LEN = 4

    def __init__(self, length, type_, data, crc):
        log.debug(f"Creating {type_.decode('utf-8')} chunk")
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
        data = (f"Width: {self.width} | Height: {self.height} | BitDepth: {self.bit_depth} | ColorType: {self.color_type} | "
                            f"CompressionMethod: {self.compression_method} | FilterMethod: {self.filter_method} | InterlaceMethod {self.interlace_method}")
        with temporary_data_change(self, data):
            return super().__str__()

class PLTE(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

    def __str__(self):
        if self.data:
            data = self.get_parsed_data()
        else:
            data = self.data
        with temporary_data_change(self, data):
            return super().__str__()

    def get_parsed_data(self):
        decoded_pixels = iter([int(byte, 16) for byte in self.data. hex(' ').split()])
        return [pixel_tuple for pixel_tuple in zip_longest(*[decoded_pixels]*3)]

class IDAT(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

class IEND(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

    def __str__(self):
        with temporary_data_change(self, "\'\'"):
            return super().__str__()


CHUNKTYPES = {
    b'IHDR': IHDR,
    b'PLTE': PLTE,
    b'IDAT': IDAT,
    b'IEND': IEND
}
