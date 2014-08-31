
import os
import sys
import os.path
import re
import logging
import magic
import urlparse
from lxml import html, etree
from datetime import datetime, timedelta
log = logging.getLogger('CRAWLER')

class Crawler:

    def __init__(self, cfg):

        input_folder = cfg.get('crawl', 'input') if (cfg.has_section('crawl') and cfg.has_option('crawl', 'input')) else None
        exclude_types = cfg.get('crawl', 'exclude_types') if (cfg.has_section('crawl') and cfg.has_option('crawl', 'exclude_types')) else None
        exclude_files = cfg.get('crawl', 'exclude_files') if (cfg.has_section('crawl') and cfg.has_option('crawl', 'exclude_files')) else None
        exclude_paths = cfg.get('crawl', 'exclude_paths') if (cfg.has_section('crawl') and cfg.has_option('crawl', 'exclude_paths')) else None
        source = cfg.get('crawl', 'source').split(',') if (cfg.has_section('crawl') and cfg.has_option('crawl', 'source')) else None
        log.debug("Input folder for crawl: %s" % input_folder)
        log.debug("Excluded types list: %s" % exclude_types)
        log.debug("Excluded paths list: %s" % exclude_paths)
        log.debug("Excluded files list: %s" % exclude_files)
        log.debug("Map to source: %s" % source)

        if input_folder is None:
            log.error("I think input folder is missing from the config: %s" % site_configuration)
            sys.exit()

        # what to index
        self.input_folder = input_folder

        # types to exclude
        self.exclude_types = [ p.strip() for p in exclude_types.split(',') ] if exclude_types is not None else None

        # paths to exclude
        self.exclude_paths = [ os.path.join(self.input_folder, p.strip()) for p in exclude_paths.split(',') ] if exclude_paths is not None else None

        # files to exclude
        #self.exclude_files = exclude_files.split(',')
        self.exclude_files = [ re.compile(e.strip()) for e in exclude_files.split(',') ] if exclude_files is not None else None

        # whether the source should be re-mapped for file loads
        self.source = source

        # initialise date boundaries
        self.date_from = None
        self.date_to = None

        log.info('Crawler initialised')

    def run(self):
        log.info("Crawling %s" % self.input_folder)

        # walk the content folder, generating list of 
        #  available content => self.input_folder
        files_list = []
        for (dirpath, dirnames, filenames) in os.walk(self.input_folder):
            ditch_path = False
            for d in self.exclude_paths:
                if re.match(d, dirpath):
                    log.debug("Excluding: %s" % dirpath)
                    ditch_path = True 

            if ditch_path:
                continue

            log.debug("Scanning: %s for content" % dirpath)
            for f in filenames:
                file_handle = os.path.join(dirpath, f)

                # clean out anything from new that matches an exclude
                ditch_file = False
                for e in self.exclude_files:
                    if e.search(file_handle) is not None:
                        ditch_file = True

                # get out if the file is in the exclude list
                if ditch_file:
                    continue

                # get out if it's a folder or a symlink to somewhere else
                if os.path.isdir(file_handle) or os.path.islink(file_handle):
                    continue

                # ditch it if it's not a HTML file
                try:
                    filetype = magic.from_file(file_handle)
                    if not re.search('HTML', filetype):
                        continue
                except:
                    log.error("What the hell sort of file is this Helen?: %s" % file_handle)

                # read the file - look for a DC.Identifier tag
                tree = html.parse(file_handle)

                # ditch it if it doesn't have DC.Identifier
                identifier = tree.xpath('//meta[@name="DC.Identifier"]')
                if not identifier:
                    continue

                document = self.which_file(tree, file_handle)
                if document is not None:
                    files_list.append(document)

        # print the dataset existance dates
        log.debug("Dataset existance range: %s - %s" % (self.date_from, self.date_to))

        # this is the list of files to be transformed and submitted to SOLR
        return files_list, [self.date_from, self.date_to]

    def which_file(self, tree, file_handle):

        # figure out if it's an EAC record or anything else
        #  if it's an EAC we'll cache the XML data file
        #  everything else: we use the html
        data = tree.xpath('//meta[@name="EAC"]')
        if data:
            # we need to confirm that we can get the XML (ie that
            #  the URL is correct) otherwise just use the HTML file
            source = data[0].attrib['content']
            if len(self.source) == 2:
                source = source.replace(self.source[0].strip(), self.source[1].strip())
                if os.path.exists(source):
                    try:
                        tree = etree.parse(source)
                    except etree.XMLSyntaxError:
                        log.error("Broken XML datafile. Using the HTML content for: %s" % file_handle)
                        return (file_handle, 'html')

                    # ditch it if it's a type which is to be excluded
                    etype = tree.xpath("/n:eac-cpf/n:control/n:localControl[@localType='typeOfEntity']/n:term",
                           namespaces={'n': 'urn:isbn:1-931666-33-4' })
                    try:
                        etype = etype[0]
                    except IndexError:
                        log.error("Bad XML datafile LocalControl seems to be missing. Using the HTML content for: %s" % file_handle)
                        return (file_handle, 'html')

                    if etype.text in self.exclude_types:
                        log.info("Excluding: %s, (type: %s)" % (file_handle, etype.text))
                        return None
                    else:
                        log.debug("Using the XML content for: %s" % file_handle)

                        # now extract date_from and date_to from the dataset
                        #  so we can determine the bounds of the dataset
                        date_from = tree.xpath("/n:eac-cpf/n:cpfDescription/n:description/n:existDates/n:dateRange/n:fromDate/@standardDate",
                            namespaces={'n': 'urn:isbn:1-931666-33-4' })
                        date_to = tree.xpath("/n:eac-cpf/n:cpfDescription/n:description/n:existDates/n:dateRange/n:toDate/@standardDate",
                            namespaces={'n': 'urn:isbn:1-931666-33-4' })

                        if (date_from):
                            dn = datetime.strptime(date_from[0], '%Y-%m-%d')
                            try:
                                do = datetime.strptime(self.date_from, '%Y-%m-%d')

                                if dn < do:
                                    self.date_from = dn.strftime('%Y-%m-%d')
                            except:
                                self.date_from = date_from[0]

                        if (date_to):
                            dt = datetime.strptime(date_to[0], '%Y-%m-%d')
                            try:
                                do = datetime.strptime(self.date_to, '%Y-%m-%d')
                                if dt > do:
                                    self.date_to = dt.strftime('%Y-%m-%d')
                            except:
                                self.date_to = date_to[0]
                            

                        return (source, 'xml')
                else:
                    log.warn("XML datafile referenced in %s but I couldn't retrieve it." % file_handle)
                    log.debug("Using the HTML content for: %s" % file_handle)
                    return (file_handle, 'html')
            else:
                log.error("Trying to handle %s but don't know how to map it." % file_handle)
                log.error("Define map_url and possibly map_path in the indexing config to transpose the URL to the filesystem location.")

        else:
            log.debug("Using the HTML content for: %s" % file_handle)
            return (file_handle, 'html')

