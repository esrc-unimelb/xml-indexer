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
from indexer.EADProcessor import EADProcessor

log = logging.getLogger('INDEXER')

class Indexer:
    def __init__(self, site, config):
        # get the default configuration
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(config)

        self.site = site

        # assemble the path to the config file defining how to handle OHRM data
        #  this doesn't mean it exists or that we'll use it
        configuration = cfg.get('GENERAL', 'ohrm_configs') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'ohrm_configs')) else None
        if configuration is not None:
            ohrm_data_configuration_file = os.path.join(configuration, site)
        else:
            log.error("'ohrm_configs' not defined in section in section GENERAL")
            sys.exit()

        # assemble the path to the config file defining how to handle HDMS data
        #  this doesn't mean it exists or that we'll use it
        configuration = cfg.get('GENERAL', 'hdms_configs') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'hdms_configs')) else None
        if configuration is not None:
            hdms_data_configuration_file = os.path.join(configuration, site)
        else:
            log.error("'hdms_configs' not defined in section in section GENERAL")
            sys.exit()

        # assemble the path to the site cache
        site_cache = cfg.get('GENERAL', 'cache_path') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'cache_path')) else None
        if site_cache is not None:
            self.site_cache = os.path.join(site_cache, site)
        else:
            log.error("'cache_path' not defined in section in section GENERAL")
            sys.exit()

        self.default_transforms = cfg.get('GENERAL', 'transforms') if (cfg.has_section('GENERAL') and cfg.has_option('GENERAL', 'transforms')) else None
        log.debug("OHRM Data Configuration: %s" % ohrm_data_configuration_file)
        log.debug("HDMS Data Configuration: %s" % hdms_data_configuration_file)
        log.debug("Cache path: %s" % self.site_cache)

        # read in the ohrm specific configuration 
        try:
            cfg.read(ohrm_data_configuration_file)
            self.ohrm_cfg = cfg
        except:
            self.ohrm_cfg = None

        # read in the hdms specific configuration 
        try:
            cfg.read(hdms_data_configuration_file)
            self.hdms_cfg = cfg
        except:
            self.hdms_cfg = None


    def crawl(self):
        ### CRAWL THE SOURCE FOLDER
        files_list = []

        with Timer() as t:
            c = Crawler(self.ohrm_cfg)
            (files_list, existence_range) = c.run()

        self.existence_range = existence_range

        return files_list

    def transform(self, content, document=None, doctype=None):
        ### TRANSFORM THE CONTENT MARKED FOR INGESTION INTO SOLR
        output_folder = os.path.join(self.site_cache, 'ohrm')
        transforms = self.ohrm_cfg.get('transform', 'transforms') if (self.ohrm_cfg.has_section('transform') and self.ohrm_cfg.has_option('transform', 'transforms')) else None
        solr_service = self.ohrm_cfg.get('post', 'index') if (self.ohrm_cfg.has_section('post') and self.ohrm_cfg.has_option('post', 'index')) else None

        metadata = {
            'site_code': self.site,
            'site_name': self.ohrm_cfg.get('meta', 'site_name') if (self.ohrm_cfg.has_section('meta') and self.ohrm_cfg.has_option('meta', 'site_name')) else None,
            'site_url': self.ohrm_cfg.get('meta', 'site_url') if (self.ohrm_cfg.has_section('meta') and self.ohrm_cfg.has_option('meta', 'site_url')) else None
        }

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
            t = Transformer(content, metadata, output_folder, transforms, self.existence_range)
            if document is not None:
                t.process_document((document, doctype), debug=True)
            else:
                t.run()

    def process_hdms_data(self):
        ### EXTRACT THE FINDING AID ITEMS
        ead_datafile = self.hdms_cfg.get('hdms', 'input') if (self.hdms_cfg.has_section('hdms') and self.hdms_cfg.has_option('hdms', 'input')) else None
        images = self.hdms_cfg.get('hdms', 'images') if (self.hdms_cfg.has_section('hdms') and self.hdms_cfg.has_option('hdms', 'images')) else None
        source = self.hdms_cfg.get('hdms', 'source') if (self.hdms_cfg.has_section('hdms') and self.hdms_cfg.has_option('hdms', 'source')) else None
        output_folder = os.path.join(self.site_cache, 'hdms')

        metadata = {
            'site_code': self.site,
            'site_name': self.hdms_cfg.get('meta', 'site_name') if (self.hdms_cfg.has_section('meta') and self.hdms_cfg.has_option('meta', 'site_name')) else None,
            'site_url': self.hdms_cfg.get('meta', 'site_url') if (self.hdms_cfg.has_section('meta') and self.hdms_cfg.has_option('meta', 'site_url')) else None,
            'source': self.hdms_cfg.get('hdms', 'source') if (self.hdms_cfg.has_section('hdms') and self.hdms_cfg.has_option('hdms', 'source')) else None
        }
        if ead_datafile is not None:
            ead = EADProcessor(ead_datafile, self.default_transforms, source, images, output_folder)
            ead.run(metadata)

    def post(self, solr_service, clean_first):
        ### POST THE SOLR DOCUMENTS TO THE INDEX
        #input_folder = os.path.join(self.site_cache, 'post')
        input_folder = self.site_cache
        if solr_service is None:
            solr_service = self.ohrm_cfg.get('post', 'index') if (self.ohrm_cfg.has_section('post') and self.ohrm_cfg.has_option('post', 'index')) else None
            if solr_service == None:
                solr_service = self.hdms_cfg.get('hdms', 'index') if (self.ohrm_cfg.has_section('hdms') and self.ohrm_cfg.has_option('hdms', 'index')) else None

        log.debug("Content folder to be posted : %s" % input_folder)
        log.debug("Solr service: %s" % solr_service)

        with Timer() as t:
            p = Poster(input_folder, solr_service, self.site)
            p.run(clean_first)


