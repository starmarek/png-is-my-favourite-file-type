import logging

log = logging.getLogger('pngparser.py')

PNG_MAGIC_NUMBER = b'\x89PNG\r\n\x1a\n'

class PngParser():
    def __init__(self, file):
        log.info('Starting to parse your file!')
        log.debug('Openning file')
        self.file = open(file, 'rb')

        log.debug('Checking signature')
        if self.file.read(len(PNG_MAGIC_NUMBER)) != PNG_MAGIC_NUMBER:
            raise Exception(f'{self.file.name} is not a PNG!')

        self.read_chunks()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, value, traceback):
        if ex_type:
            print(f'Error {ex_type}: {value}\n{traceback}')
        log.debug('Closing file')
        self.file.close()

    def read_chunks(self):
        print("Dummy chunks!")
