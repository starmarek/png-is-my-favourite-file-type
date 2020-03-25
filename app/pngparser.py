import logging
from chunk import Chunk

log = logging.getLogger(__name__)

PNG_MAGIC_NUMBER = b'\x89PNG\r\n\x1a\n'

class PngParser():
    def __init__(self, file):
        log.debug('Openning file')
        self.file = open(file, 'rb')
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

    def read_chunks(self):
        while True:
            chunk = Chunk(self.file)
            self.chunks.append(chunk)

            if chunk.type_ == "IEND":
                break

    def print_chunks(self):
        for i, chunk in enumerate(self.chunks, 1):
            print(f"\033[1mCHUNK #{i}\033[0m")
            print(chunk)
