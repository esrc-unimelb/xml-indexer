
import logging
log = logging.getLogger()

class Poster:

    def __init__(self, input_folder, solr_service):
        # what to send to solr
        self.input_folder = input_folder

        # where to send it
        self.solr_service = solr_service

        log.info('Poster initialised')
        
    def run(self):
        pass