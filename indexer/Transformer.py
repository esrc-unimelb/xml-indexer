
import logging
log = logging.getLogger()

class Transformer:

    def __init__(self, input_folder, output_folder, transforms):
        # what to process
        self.input_folder = input_folder

        # where to stash the output
        self.output_folder = output_folder

        # how to process it
        self.transforms = transforms

        log.info('Transformer initialised')

    def run(self):
        pass
        