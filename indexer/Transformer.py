
import sys
import logging
import os.path
import shutil
from lxml import etree, html
from clean.empty import elements
from clean.date import date_cleanser
from clean.markup import markup_cleanser
import requests
from datetime import datetime, timedelta

log = logging.getLogger('TRANSFORMER')

class Transformer:

    def __init__(self, files_list, site, output_folder, transforms, existence_range):
        # what to process
        self.files_list = files_list

        # the site code
        self.site = site

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
        try:
            df = datetime.strptime(existence_range[0], '%Y-%m-%d') - timedelta(weeks=52)
            self.date_lower_bound = str(df).split(' ')[0]
        except TypeError:
            self.date_lower_bound = None
        try:
            dt = datetime.strptime(existence_range[1], '%Y-%m-%d') + timedelta(weeks=52)
            self.date_upper_bound = str(dt).split(' ')[0]
        except TypeError:
            self.date_upper_bound = None

        log.info('Transformer initialised')

    def run(self):
        """Process each document in the input files_list"""

        # wipe the output folder
        shutil.rmtree(self.output_folder)
        if not os.path.isdir(self.output_folder):
            os.makedirs(self.output_folder)

        for f in self.files_list:
            self.process_document(f)

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
        self._clean_dates(d)

        try:
            # clean the fields with markup
            self._clean_markup(d)
        except ValueError:
            log.error("I think there's something wrong with the transformed result of: %s" % doc[0])

        # strip empty elements - dates in particular cause
        #  solr to barf horribly...
        elements().strip_empty_elements(d)

        # add in the metadata the indexer users
        tmp = d.xpath('/add/doc')[0]

        # add the solr unique id field 
        site_code = etree.Element('field', name='site_code')
        site_code.text = self.site
        tmp.append(site_code)

        # add in the faux start and end date as required
        #  but only if the record has a date from or to defined - for those
        #  records where it'snot defined; we skip this step so we don't
        #  get dodgy results
        if d.xpath('/add/doc/field[@name="date_from"]') or d.xpath('/add/doc/field[@name="date_to"]'):
            if self.date_lower_bound is not None:
                df = etree.Element('field', name='exist_from')
                if d.xpath('/add/doc/field[@name="date_from"]'):
                    df.text = d.xpath('/add/doc/field[@name="date_from"]')[0].text
                else:
                    df.text = "%sT00:00:00Z" % self.date_lower_bound
                tmp.append(df)

            if self.date_upper_bound is not None:
                dt = etree.Element('field', name='exist_to')
                if d.xpath('/add/doc/field[@name="date_to"]'):
                    dt.text = d.xpath('/add/doc/field[@name="date_to"]')[0].text
                else:
                    dt.text = "%sT00:00:00Z" % self.date_upper_bound
                tmp.append(dt)

        # now we want to save the document to self.output_folder
        #
        # To ensure we never get a name clash, use the value of id as the filename,
        #  suitably transformed to something sensible 
        uniqueid = d.xpath("/add/doc/field[@name='id']")
        if not uniqueid:
            log.error("Couldn't get unique id for %s so I can't save it" % doc[0])
            return

        add = etree.Element('add')
        add.append(tmp)

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

    def _clean_dates(self, doc):
        """Date data needs to be in Solr date format

        The format for this date field is of the form 1995-12-31T23:59:59Z,

        @params:
        doc: the XML document
        """
        date_elements = [ e for e in doc.iter() if e.get('name') in self.date_fields ]
        for e in date_elements:
            # have we found an empty or missing date field ?
            if e.text is None:
                continue

            #dc = date_cleanser(self.date_fields)
            dc = date_cleanser()
            datevalue = dc.clean(e.text)
            e.text = datevalue

    def _clean_markup(self, doc):
        """We don't want markup in the content being indexed

        @params:
        doc: the XML document
        """
        markup_elements = [ e for e in doc.iter() if e.get('name') in self.markup_fields ]
        for e in markup_elements:
            # have we found an empty or missing date field ?
            if e.text is None:
                continue

            e.text = markup_cleanser().clean(e.text)



