
import os.path
import logging
import sys
from lxml import etree

from clean.empty import elements
from helpers import *

log = logging.getLogger('EAD PROCESSOR')

class EADProcessor:
    def __init__(self, datafile, transforms, source, images, output_folder):
        # the HDMS datafile
        self.datafile = datafile

        # the source URL for contructing the id
        self.source = source

        # the path to the images - optional
        self.images = images

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

                sid = etree.Element('field', name='series_id')
                sid.text = series_id

                iid = etree.Element('field', name='item_id')
                iid.text = item_id

                d = doc.xpath('/add/doc')[0]
                d.append(eid)
                d.append(site_code)
                d.append(site_url)
                d.append(site_name)
                d.append(data_type)
                d.append(sid)
                d.append(iid)

                # process any item images - if there any
                if self.images is not None:
                    # stash the image path
                    image_path = etree.Element('field', name='source')
                    image_path.text = metadata['source']
                    d.append(image_path)

                    # generate the list of small images
                    try:
                        images = [ f for f in os.listdir(os.path.join(self.images, item_id, 'small')) ]
                        for f in sorted(images):
                            image = etree.Element('field', name='small_images')
                            image.text = f
                            d.append(image)
                    except OSError:
                        pass

                    # generate the list of large images
                    try:
                        images = [ f for f in os.listdir(os.path.join(self.images, item_id, 'large')) ]
                        for f in sorted(images):
                            image = etree.Element('field', name='large_images')
                            image.text = f
                            d.append(image)
                    except OSError:
                        pass

                # clean the date entries for solr
                clean_dates(d)

                try:
                    # clean the fields with markup
                    clean_markup(d)
                except ValueError:
                    log.error("I think there's something wrong with the transformed result of: %s" % item_id)

                # strip empty elements - dates in particular cause
                #  solr to barf horribly...
                elements().strip_empty_elements(d)

                # add in the faux start and end date as required
                #  but only if the record has a date from or to defined - for those
                #  records where it'snot defined; we skip this step so we don't
                #  get dodgy results
                if d.xpath('/add/doc/field[@name="date_from"]') or d.xpath('/add/doc/field[@name="date_to"]'):
                    df = etree.Element('field', name='exist_from')
                    if d.xpath('/add/doc/field[@name="date_from"]'):
                        df.text = d.xpath('/add/doc/field[@name="date_from"]')[0].text
                        d.append(df)

                    dt = etree.Element('field', name='exist_to')
                    if d.xpath('/add/doc/field[@name="date_to"]'):
                        dt.text = d.xpath('/add/doc/field[@name="date_to"]')[0].text
                    else:
                        dt.text = "%sT00:00:00Z" % self.date_upper_bound
                    d.append(dt)
                            
                try:
                    uniqueid = eid.text.split('://')[1].replace('#', '-')
                    output_file = os.path.join(self.output_folder, uniqueid.replace('/', '-'))
                    log.debug("Writing output to: %s" % output_file)
                    with open(output_file, 'w') as f:
                        f.write(etree.tostring(doc, pretty_print=True))
                except:
                    log.error("Couldn't save the output from: %s" % doc[0])
                    print etree.tostring(doc, pretty_print=True)
