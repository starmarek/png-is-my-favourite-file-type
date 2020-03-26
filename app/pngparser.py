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

    def get_chunk_type(self):
        current_position = self.file.tell()
        self.file.seek(current_position + ch.Chunk.LENGTH)
        chunk_type = self.file.read(ch.Chunk.TYPE)
        self.file.seek(current_position)
        return chunk_type

    def read_chunks(self):
        while True:
            chunk_class_type = ch.CHUNKTYPES.get(self.get_chunk_type())

            if chunk_class_type is None:
                chunk = ch.Chunk(self.file)
            else:
                chunk = chunk_class_type(self.file)
            self.chunks.append(chunk)

            if chunk.type_ == b"IEND":
                break

    def print_chunks(self):
        for i, chunk in enumerate(self.chunks, 1):
            print(f"\033[1mCHUNK #{i}\033[0m")
            print(chunk)
