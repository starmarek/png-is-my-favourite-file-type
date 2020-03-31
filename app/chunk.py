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

        self.assert_data()

    def __str__(self):
        tmp = self.data
        self.data = (f"Width: {self.width} | Height: {self.height} | BitDepth: {self.bit_depth} | ColorType: {self.color_type} | "
                        f"CompressionMethod: {self.compression_method} | FilterMethod: {self.filter_method} | InterlaceMethod {self.interlace_method}")
        try:
            return super().__str__()
        finally:
            self.data = tmp

    def assert_data(self):
        color_type_to_bit_depth_restriction = {
            0: [1, 2, 4, 8, 16],
            2: [8, 16],
            3: [1, 2, 4, 8],
            4: [8, 16],
            6: [8, 16]
        }

        assert self.width > 0, "Image width must be > 0"
        assert self.height > 0, "Image height must be > 0"
        assert self.bit_depth in [1, 2, 4, 8, 16], f"Wrong bit_depth: {self.bit_depth}. It must be one of: 1, 2, 4, 8 ,16"
        assert self.color_type in [0, 2, 3, 4, 6], f"Wrong color_type: {self.color_type}. It must be one of: 0, 2, 3, 4 ,16"
        assert self.bit_depth in color_type_to_bit_depth_restriction.get(self.color_type), (f"Wrong color_type to bit_depth combination: {self.color_type} : {self.bit_depth}"
                                                                                             f"\nIt must be one of: {color_type_to_bit_depth_restriction}"
                                                                                            )
        assert self.compression_method == 0, f"Unsupported compression_method: {self.compression_method}. Only 0 is supported."
        assert self.filter_method == 0, f"Unsupported filter_method: {self.filter_method}. Only 0 is supported."
        assert self.interlace_method == 0, f"Unsupported interlace_method: {self.interlace_method}. Only 0 is supported."

        # tepmorary
        assert self.color_type != 3, f"We dont support color type {self.color_type} for now!"

CHUNKTYPES = {
    b"IHDR": IHDR
}
