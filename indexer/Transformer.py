
import sys
import logging
import os.path
from lxml import etree, html
log = logging.getLogger('TRANSFORMER')

class Transformer:

    def __init__(self, files_list, output_folder, transforms):
        # what to process
        self.files_list = files_list

        # where to stash the output
        self.output_folder = output_folder
        if not os.path.isdir(self.output_folder):
            os.makedirs(self.output_folder)

        # how to process it
        self.transforms = transforms

        log.info('Transformer initialised')

    def run(self):
        for f in self.files_list:
            self.process_document(f)

    def process_document(self, doc, debug=False):
        # figure out its type
        if doc[1] == 'xml':
            try:
                tree = etree.parse(doc[0])
            except IOError:
                log.error("Couldn't load %s. Skipping it.." % doc[0])
                return
            transform = os.path.join(self.transforms, 'eac.xsl')
        else:
            try:
                tree = html.parse(doc[0])
            except IOError:
                log.error("Couldn't load %s. Skipping it." % doc[0])
                return
            transform = os.path.join(self.transforms, self._get_transform(tree))

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

        # when testing against a single document, this is the line that spits
        #  the result to stdout for viewing
        if debug:
            print etree.tostring(d, pretty_print=True)

        # now we want to save the document to self.output_folder
        #
        # To ensure we never get a name clash, use the value of id as the filename,
        #  suitably transformed to something sensible 
        uniqueid = d.xpath("/add/doc/field[@name='id']")
        if not uniqueid:
            log.error("Couldn't get unique id for %s so I can't save it" % doc[0])
            return

        uniqueid = uniqueid[0].text.split('://')[1]
        output_file = os.path.join(self.output_folder, uniqueid.replace('/', '-'))
        log.debug("Writing output to: %s" % output_file)
        with open(output_file, 'w') as f:
            f.write(etree.tostring(d, pretty_print=True))


    def _get_transform(self, tree):
        if tree.xpath('//body[@id="entity"]'):
            return 'entity.xsl'

        if tree.xpath('//body[@id="pub"]'):
            return 'pub.xsl'

        if tree.xpath('//body[@id="arc"]'):
            return 'arc.xsl'

        if tree.xpath('//body[@id="dobject"]'):
            return 'dobject.xsl'

        # it's some other kind of html document so just slurp the body
        return 'body.xsl'
        
        # load a suitable transform
        # transform it 
        # store the result
