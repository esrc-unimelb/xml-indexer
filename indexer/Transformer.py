
import sys
import os.path
import shutil
from lxml import etree, html
import requests
from datetime import datetime, timedelta

from clean.empty import elements
from helpers import *

import logging
log = logging.getLogger(__name__)

class Transformer:

    def __init__(self, files_list, metadata, output_folder, transforms, existence_range):
        # what to process
        self.files_list = files_list

        # the site code
        self.metadata = metadata

        # where to stash the output
        self.output_folder = output_folder
        if not os.path.isdir(self.output_folder):
            os.makedirs(self.output_folder)

        # how to process it
        self.transforms = transforms

        # the names of the fields which could have a date
        self.date_fields = [ 'date_from', 'date_to' ]

        # the names of the fields which could have markup
        self.markup_fields = [ 'abstract', 'text', 'locality' ]

        # the existence range of the dataset
        #try:
        #    df = datetime.strptime(existence_range[0], '%Y-%m-%d') - timedelta(weeks=52)
        #    self.date_lower_bound = str(df).split(' ')[0]
        #except TypeError:
        #    self.date_lower_bound = None
        #try:
        #    dt = datetime.strptime(existence_range[1], '%Y-%m-%d') + timedelta(weeks=52)
        #    self.date_upper_bound = str(dt).split(' ')[0]
        #except TypeError:
        #    self.date_upper_bound = None
        self.date_upper_bound = str(datetime.now()).split(' ')[0]

        log.info('Transformer initialised')

    def run(self):
        """Process each document in the input files_list"""

        # wipe the output folder
        shutil.rmtree(self.output_folder)
        if not os.path.isdir(self.output_folder):
            os.makedirs(self.output_folder)

        for f in self.files_list:
            self.process_document(f)

    def add_field(self, doc, field_name, field_value):
        tmp = doc.xpath('/add/doc')[0]

        # add the record and item metadata
        b = etree.Element('field', name=field_name)
        b.text = field_value.decode('utf-8')
        tmp.append(b)

        add = etree.Element('add')
        add.append(tmp)
        return add

    def process_document(self, doc, debug=False):
        """The code to actually process the document

        @params:
        - doc: the path to a document to try and transform
        - debug: false (default): if set to true - transformed
            doc gets written to STDOUT for viewing
        """
        # figure out its type
        if doc[1] == 'xml':
            try:
                tree = etree.parse(doc[0])
            except IOError:
                log.error("Couldn't load %s. Skipping it.." % doc[0])
                return
            except etree.XMLSyntaxError:
                log.error("Bad data file: %s. Skipping it.." % doc[0])
                return
        else:
            try:
                tree = html.parse(doc[0])
            except IOError:
                log.error("Couldn't load %s. Skipping it." % doc[0])
                return

        transform = self._get_transform(tree)
        log.debug("Transforming %s with %s" % (doc[0], transform))
        try:
            xsl = etree.parse(transform)
            xsl.xinclude()
            xsl = etree.XSLT(xsl)
        except IOError:
            log.error("No such transform: %s; skipping document: %s" % (transform, doc[0]))
            return
        except etree.XSLTParseError:
            log.error("Check the stylesheet; I can't parse it! %s" % transform)
            return 

        # transform it!
        d = xsl(tree)

        # clean the date entries for solr
        clean_dates(d)

        try:
            # clean the fields with markup
            clean_markup(d)
        except ValueError:
            log.error("I think there's something wrong with the transformed result of: %s" % doc[0])

        # strip empty elements - dates in particular cause
        #  solr to barf horribly...
        elements().strip_empty_elements(d)

        # add in the metadata the indexer users
        d = d.xpath('/add/doc')[0]

        # add the site metadata into the record
        d = self.add_field(d, 'site_code', self.metadata['site_code'])
        d = self.add_field(d, 'site_name', self.metadata['site_name'])
        d = self.add_field(d, 'site_url', self.metadata['site_url'])
        d = self.add_field(d, 'data_type', 'OHRM')

        # add in the faux start and end date as required
        #  but only if the record has a date from or to defined - for those
        #  records where it'snot defined; we skip this step so we don't
        #  get dodgy results
        if d.xpath('/add/doc/field[@name="date_from"]') or d.xpath('/add/doc/field[@name="date_to"]'):
            if d.xpath('/add/doc/field[@name="date_from"]'):
                d = self.add_field(d, 'exist_from', d.xpath('/add/doc/field[@name="date_from"]')[0].text)

            if d.xpath('/add/doc/field[@name="date_to"]'):
                d = self.add_field(d, 'exist_to', d.xpath('/add/doc/field[@name="date_to"]')[0].text)

            # add the existance to date if from date and no to date
            if d.xpath('/add/doc/field[@name="exist_from"]') and not d.xpath('/add/doc/field[@name="exist_to"]'):
                d = self.add_field(d, 'exist_to', d.xpath('/add/doc/field[@name="exist_from"]')[0].text)

            # add the existance from date if no from date and a to date
            if not d.xpath('/add/doc/field[@name="exist_from"]') and d.xpath('/add/doc/field[@name="exist_to"]'):
                d = self.add_field(d, 'exist_from', d.xpath('/add/doc/field[@name="exist_to"]')[0].text)

        # now we want to save the document to self.output_folder
        #
        # To ensure we never get a name clash, use the value of id as the filename,
        #  suitably transformed to something sensible 
        uniqueid = d.xpath("/add/doc/field[@name='id']")
        if not uniqueid:
            log.error("Couldn't get unique id for %s so I can't save it" % doc[0])
            return

        add = etree.Element('add')
        add.append(d)

        # when testing against a single document, this is the line that spits
        #  the result to stdout for viewing
        if debug:
            print etree.tostring(add, pretty_print=True)

        try:
            uniqueid = uniqueid[0].text.split('://')[1]
            output_file = os.path.join(self.output_folder, uniqueid.replace('/', '-'))
            log.debug("Writing output to: %s" % output_file)
            with open(output_file, 'w') as f:
                f.write(etree.tostring(add, pretty_print=True))
        except:
            log.error("Couldn't save the output from: %s" % doc[0]) 

    def _get_transform(self, tree):
        # we're we given an XML tree or a HTML tree
        root = tree.getroot()

        if root.tag == 'html':
            if tree.xpath('//body[@id="entity"]'):
                t = 'entity.xsl'

            elif tree.xpath('//body[@id="pub"]'):
                t = 'pub.xsl'

            elif tree.xpath('//body[@id="arc"]'):
                t = 'arc.xsl'

            elif tree.xpath('//body[@id="dobject"]'):
                t = 'dobject.xsl'

            else:
                # it's some other kind of html document so just slurp the body
                log.debug("Uh oh - using body transform as the type couldn't be determined more specifically.")
                t = 'body.xsl'

        else:
            t = 'eac.xsl'

        for transform_path in self.transforms:
            transform = os.path.join(transform_path, t)
            if os.path.exists(transform):
                return transform
