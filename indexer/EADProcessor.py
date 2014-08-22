
import os.path
import logging
import sys
from lxml import etree

from clean.empty import elements
from helpers import *

log = logging.getLogger('EAD PROCESSOR')

class EADProcessor:
    def __init__(self, datafile, transforms, source, output_folder):
        # the HDMS datafile
        self.datafile = datafile

        # the source URL for contructing the id
        self.source = source

        # where to stash the output
        self.output_folder = output_folder
        if not os.path.isdir(self.output_folder):
            os.makedirs(self.output_folder)

        # the transform to load and use
        transform = None
        if os.path.exists(os.path.join(transforms, 'ead.xsl')):
            transform = os.path.join(transforms, 'ead.xsl')

        if transform is not None:
            xsl = etree.parse(transform)
            xsl.xinclude()
            self.xsl = etree.XSLT(xsl)

    def run(self, metadata):
        if not os.path.exists(self.datafile):
            log.error("Couldn't find file: %s" % self.datafile)
            return

        try:
            tree = etree.parse(self.datafile)
        except etree.XMLSyntaxError:
            log.error("Invalid XML file: %s" % self.datafile)

        for series in tree.xpath('//c01'):
            series_id = series.attrib['id']
            #print etree.tostring(series, pretty_print=True)
            #creator = series_id.xpath('/c01/did/origination[@label="Provenance"]/ref/persname')
            #print etree.tostring(series, pretty_print=True)

            for item in series.xpath('c02'):
                item_id = item.attrib['id']
                doc = self.xsl(item)

                eid = etree.Element('field', name='id')
                eid.text = "%s/%s#%s" % (self.source, series_id, item_id)

                # add the site metadata into the record
                site_code = etree.Element('field', name='site_code')
                site_code.text = metadata['site_code']

                site_name = etree.Element('field', name='site_name')
                site_name.text = metadata['site_name']

                site_url = etree.Element('field', name='site_url')
                site_url.text = metadata['site_url']

                data_type = etree.Element('field', name='data_type')
                data_type.text = 'HDMS'

                d = doc.xpath('/add/doc')[0]
                d.append(eid)
                d.append(site_code)
                d.append(site_url)
                d.append(site_name)
                d.append(data_type)

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
                        
                try:
                    uniqueid = eid.text.split('://')[1].replace('#', '-')
                    output_file = os.path.join(self.output_folder, uniqueid.replace('/', '-'))
                    log.debug("Writing output to: %s" % output_file)
                    with open(output_file, 'w') as f:
                        f.write(etree.tostring(doc, pretty_print=True))
                except:
                    log.error("Couldn't save the output from: %s" % doc[0])
                    print etree.tostring(doc, pretty_print=True)
