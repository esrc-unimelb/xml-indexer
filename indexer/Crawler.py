
import os
import re
import logging
import magic
import urlparse
from lxml import html, etree
log = logging.getLogger('CRAWLER')

class Crawler:

    def __init__(self, input_folder, excludes):
        # what to index
        self.input_folder = input_folder

        # what to exclude
        #self.excludes = excludes.split(',')
        self.excludes = [ re.compile(e.strip()) for e in excludes.split(',') ] if excludes is not None else None

        log.info('Crawler initialised')

    def run(self):

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
                    try:
                        # we need to confirm that we can get the XML (ie that
                        #  the URL is correct) otherwise just use the HTML file
                        tree = etree.parse(data[0].attrib['content'])
                        files_list.append((data[0].attrib['content'], 'xml'))
                    except IOError:
                        ### THIS IS A HACK
                        # findandconnect XML files are no longer accessible from the root
                        #  via /{STATE}/eac/{XML FILE} - they are now one level further down
                        #  as /ref/{STATE}/eac/{XML FILE}.
                        #
                        # SO - if we get to here, insert '/ref' into the root and try again
                        #  (we're assuming it's a convention) and if that fails - just give up.
                        url = urlparse.urlsplit(data[0].attrib['content'])
                        second_shot = "%s://%s/ref%s" % (url.scheme, url.netloc, url.path)
                        try:
                            tree = etree.parse(second_shot)
                            log.debug("Using the XML content for: %s" % file_handle)
                            files_list.append((second_shot, 'xml'))
                        except IOError:
                            log.debug("Using the HTML content for: %s" % file_handle)
                            files_list.append((file_handle, 'html'))

                else:
                    log.debug("Using the HTML content for: %s" % file_handle)
                    files_list.append((file_handle, 'html'))
        

        # this is the list of files to be transformed and submitted to SOLR
        return files_list