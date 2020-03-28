import logging
import chunk as ch

log = logging.getLogger(__name__)

PNG_MAGIC_NUMBER = b'\x89PNG\r\n\x1a\n'

class PngParser:
    def __init__(self, file_name):
        log.debug('Openning file')
        self.file = open(file_name, 'rb')
        self.chunks = []

        log.debug('Checking signature')
        if self.file.read(len(PNG_MAGIC_NUMBER)) != PNG_MAGIC_NUMBER:
            raise Exception(f'{self.file.name} is not a PNG!')
        log.debug('Start Reading Chunks')
        self.read_chunks()

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

            if chunk.type_ == b"IEND":
                break

    def print_chunks(self):
        for i, chunk in enumerate(self.chunks, 1):
            print(f"\033[1mCHUNK #{i}\033[0m")
            # if chunk.type_ == b"IDAT":
            #     continue
            print(chunk)
