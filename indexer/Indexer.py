#!/usr/local/scholarly-python2/bin/python

import sys
import argparse
import logging
import ConfigParser
import os.path
from indexer.Timer import Timer
from indexer.Crawler import Crawler
from indexer.Transformer import Transformer
from indexer.Poster import Poster

log = logging.getLogger('INDEXER')

class Indexer:
    def __init__(self, site, config):
        # get the default configuration
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(config)

        self.site = site
        configuration = cfg.get('GENERAL', 'configs') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'configs')) else None
        if configuration is not None:
            site_configuration = os.path.join(configuration, site)
        else:
            log.error("'configs' not defined in section in section GENERAL")
            sys.exit()

        site_cache = cfg.get('GENERAL', 'cache_path') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'cache_path')) else None
        if site_cache is not None:
            self.site_cache = os.path.join(site_cache, site)
        else:
            log.error("'cache_path' not defined in section in section GENERAL")
            sys.exit()

        self.default_transforms = cfg.get('GENERAL', 'transforms') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'transforms')) else None
        log.debug("Configuration: %s" % site_configuration)
        log.debug("Cache path: %s" % self.site_cache)

        # then try to load the site specific config
        if not os.path.exists(site_configuration):
            log.error("Can't access %s" % site_configuration)
            sys.exit()

        # read in the site specific configuration and kick off the run
        cfg.read(site_configuration)
        self.cfg = cfg

    def crawl(self):
        ### CRAWL THE SOURCE FOLDER
        files_list = []

        with Timer() as t:
            c = Crawler(self.cfg)
            (files_list, existence_range) = c.run()

        self.existence_range = existence_range

        return files_list

    def transform(self, content, document=None, doctype=None):
        ### TRANSFORM THE CONTENT MARKED FOR INGESTION INTO SOLR
        output_folder = os.path.join(self.site_cache, 'post')
        transforms = self.cfg.get('transform', 'transforms') if (self.cfg.has_section('transform') and self.cfg.has_option('transform', 'transforms')) else None
        solr_service = self.cfg.get('post', 'index') if (self.cfg.has_section('post') and self.cfg.has_option('post', 'index')) else Noned

        if not transforms:
            transforms = self.default_transforms
        else:
            transforms = [ transforms, self.default_transforms ]

        log.debug("Output folder for transforms: %s" % output_folder)
        log.debug("Transform search path: %s" % transforms)

        try:
            if not self.existence_range:
                pass
        except:
            self.existence_range = [ None, None ]

        with Timer() as t:
            t = Transformer(content, self.site, output_folder, transforms, self.existence_range)
            if document is not None:
                t.process_document((document, doctype), debug=True)
            else:
                t.run()

    def post(self):
        ### POST THE SOLR DOCUMENTS TO THE INDEX
        input_folder = os.path.join(self.site_cache, 'post')
        solr_service = self.cfg.get('post', 'index') if (self.cfg.has_section('post') and self.cfg.has_option('post', 'index')) else None

        log.debug("Content folder to be posted : %s" % input_folder)
        log.debug("Solr service: %s" % solr_service)

        with Timer() as t:
            p = Poster(input_folder, solr_service, self.site)
            p.run()


