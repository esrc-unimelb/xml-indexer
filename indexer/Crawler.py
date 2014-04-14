
import re
import logging
log = logging.getLogger()

class Crawler:

    def __init__(self, input_folder, output_folder, excludes):
        # what to index
        self.input_folder = input_folder

        # where to store the output
        self.output_folder = output_folder

        # what to exclude
        self.exclude = excludes

        log.info('Crawler initialised')

    def run(self):
        pass
        