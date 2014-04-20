
import os
import re
import logging
import magic
import urlparse
from lxml import html, etree
log = logging.getLogger('CRAWLER')

class Crawler:

    def __init__(self, input_folder, excludes, source):
        # what to index
        self.input_folder = input_folder

        # what to exclude
        #self.excludes = excludes.split(',')
        self.excludes = [ re.compile(e.strip()) for e in excludes.split(',') ] if excludes is not None else None

        # whether the source should be re-mapped for file loads
        self.source = source

        log.info('Crawler initialised')

    def run(self):
        log.info("Crawling %s" % self.input_folder)

        # walk the content folder, generating list of 
        #  available content => self.input_folder
        files_list = []
        for (dirpath, dirnames, filenames) in os.walk(self.input_folder):
            for f in filenames:
                file_handle = os.path.join(dirpath, f)

                # clean out anything from new that matches an exclude
                ditch_file = False
                for e in self.excludes:
                    if e.search(file_handle) is not None:
                        ditch_file = True

                # get out if the file is in the exclude list
                if ditch_file:
                    continue

                # get out if it's a folder or a symlink to somewhere else
                if os.path.isdir(file_handle) or os.path.islink(file_handle):
                    continue

                # ditch it if it's not a HTML file
                filetype = magic.from_file(file_handle)
                if not re.search('HTML', filetype):
                    continue

                # read the file - look for a DC.Identifier tag
                tree = html.parse(file_handle)

                # ditch it if it doesn't have DC.Identifier
                identifier = tree.xpath('//meta[@name="DC.Identifier"]')
                if not identifier:
                    continue

                # figure out if it's an EAC record or anything else
                #  if it's an EAC we'll cache the XML data file
                #  everything else: we use the html
                data = tree.xpath('//meta[@name="EAC"]')
                if data:
                    # we need to confirm that we can get the XML (ie that
                    #  the URL is correct) otherwise just use the HTML file
                    source = data[0].attrib['content']
                    source = source.replace(self.source[0].strip(), self.source[1].strip())
                    if os.path.exists(source):
                        log.debug("Using the XML content for: %s" % file_handle)
                        files_list.append((source, 'xml'))
                    else:
                        log.warn("Found XML datafile for %s but couldn't retrieve it" % file_handle)
                        log.debug("Using the HTML content for: %s" % file_handle)
                        files_list.append((file_handle, 'html'))

                else:
                    log.debug("Using the HTML content for: %s" % file_handle)
                    files_list.append((file_handle, 'html'))
        

        # this is the list of files to be transformed and submitted to SOLR
        return files_list