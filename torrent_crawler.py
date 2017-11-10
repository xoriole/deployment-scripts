import os
import sys

import requests
from bs4 import BeautifulSoup


def error(msg):
    """ Prints error and exits """
    print 'ERROR: %s' % msg
    sys.exit(1)


def extract_torrents(webpage_url, filename):
    """ Extracts magnet links from the page and writes to a file"""
    request = requests.get(webpage_url)
    html_content = request.text
    soup = BeautifulSoup(html_content, "html.parser")

    with open(filename, 'a') as magnet_file:
        for link in soup.find_all('a'):
            url = link.get('href')
            if 'magnet:?' in url:
                magnet_file.write(url+"\n")

    print "Extracting torrent links completed"


if __name__ == '__main__':
    # Check if webpage url is set
    WEBPAGE_URL = os.environ.get("WEBPAGE_URL")
    if WEBPAGE_URL is None:
        error("WEBPAGE_URL is not provided")

    # File to write the magnet links
    MAGNET_FILENAME = os.environ.get("MAGNET_FILENAME")
    if not MAGNET_FILENAME:
        MAGNET_FILENAME = 'magnets.txt'

    # Start extracting magnet links from the webpage url
    extract_torrents(WEBPAGE_URL, MAGNET_FILENAME)
