import struct
import logging
from itertools import zip_longest
from contextlib import contextmanager
import calendar
from tabulate import tabulate

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
        try:
            if b'Xt' in self.type_:
                # bytes containing text data. We check if chunk type matches one of text-containing chunks -> iTXt tEXt zTXt
                data = self.data.decode('utf-8')
            else:
                # bytes containing hex data
                data = ' '.join(str(byte) for byte in self.data.hex(' ').split())
        except:
            # some other __str__ method has manipulated the self.data and we want to leave it as it is
            data = self.data

        return (f"Length: {int.from_bytes(self.length, 'big')}\nType: {self.type_.decode('utf-8')}\n"
                    f"Data: {data}\nCRC: {self.crc.hex(' ')}\n")

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
        decoded_pixels = iter([int(byte, 16) for byte in self.data.hex(' ').split()])
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

class tIME(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

        values = struct.unpack('>hbbbbb', self.data)
        self.year = values[0]
        self.month = values[1]
        self.day = values[2]
        self.hour = values[3]
        self.minute = values[4]
        self.second = values[5]

    def __str__(self):
        data = f"Last modification: {self.day} {calendar.month_abbr[self.month]}. {self.year} {self.hour}:{self.minute}:{self.second}"
        with temporary_data_change(self, data):
            return super().__str__()

class gAMA(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

        # PNG specification says, that stored gamma value is multiplied by 100000
        self.gamma = int.from_bytes(data, 'big') / 100000
        if self.gamma == 0:
            log.warning("Gamma shouldn't have value 0!")

    def __str__(self):
        with temporary_data_change(self, self.gamma):
            return super().__str__()

class cHRM(Chunk):
    def __init__(self, length, type_, data, crc):
        super().__init__(length, type_, data, crc)

        values = struct.unpack('>iiiiiiii', self.data)
        # PNG specification says, that stored values are multiplied by 100000
        self.WPx = values[0] / 100000
        self.WPy = values[1] / 100000
        self.WPz = 1 - self.WPx - self.WPy
        self.Rx = values[2] / 100000
        self.Ry = values[3] / 100000
        self.Rz = 1 - self.Rx - self.Ry
        self.Gx = values[4] / 100000
        self.Gy = values[5] / 100000
        self.Gz = 1 - self.Gx - self.Gy
        self.Bx = values[6] / 100000
        self.By = values[7] / 100000
        self.Bz = 1 - self.Bx - self.By

    def __str__(self):
        table = tabulate([['x', self.Rx, self.Gx, self.Bx, self.WPx],
                          ['y', self.Ry, self.Gy, self.By, self.WPy],
                          ['z', self.WPz, self.Gz, self.Bz, self.WPz]],
                          headers=['', 'Red', 'Green', 'Blue', 'WhitePoint'],
                          tablefmt='orgtbl'
                        )
        with temporary_data_change(self, f'\n{table}'):
            return super().__str__()

CHUNKTYPES = {
    b'IHDR': IHDR,
    b'PLTE': PLTE,
    b'IDAT': IDAT,
    b'IEND': IEND,
    b'tIME': tIME,
    b'gAMA': gAMA,
    b'cHRM': cHRM,
}
