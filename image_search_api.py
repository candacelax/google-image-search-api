#!/usr/bin/env python3

# see https://github.com/NikolaiT/GoogleScraper for API details

# TODO can set this up somewhere else
SEARCH_ENGINE = 'google'

import argparse
import sys
from os import path
sys.path.append('GoogleScraper')
sys.path.append('GoogleScraper/chromedriver')
from GoogleScraper import scrape_with_config, GoogleSearchError
from GoogleScraper.database import ScraperSearch, SERP, Link
import time
from selenium import webdriver


DRIVER_PATH = path.abspath('GoogleScraper/chromedriver')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', dest='target_directory', default='images/',
                        help='directory to save downloaded images to')
    return parser.parse_args()


# simulating a image search for all search engines that support image search
# then download all found images :)
def image_search(target_directory, keyword):

    # See in the config.cfg file for possible values
    config = {
        'SCRAPING': {
            'keyword': keyword,
            'search_engines': 'google,yahoo',
            'search_type': 'image',
            'scrapemethod': 'selenium'
        }
    }

    
    try:
        sqlalchemy_session = scrape_with_config(config) # in core.py
    except GoogleSearchError as e:
        print(e)
        
    image_urls = []
    print('type', type(sqlalchemy_session))
    exit()
    search = sqlalchemy_session.query(ScraperSearch).all()[-1]

    for serp in search.serps:
        image_urls.extend(
            [link.link for link in serp.links]
        )

        
    print('[i] Going to scrape {num} images and saving them in "{dir}"'.format(
        num=len(image_urls),
        dir=target_directory
    ))

    import threading,requests, os, urllib

    class FetchResource(threading.Thread):
        """Grabs a web resource and stores it in the target directory"""
        def __init__(self, target, urls):
            super().__init__()
            self.target = target
            self.urls = urls

        def run(self):
            for url in self.urls:
                url = urllib.parse.unquote(url)
                with open(os.path.join(self.target, url.split('/')[-1]), 'wb') as f:
                    try:
                        content = requests.get(url).content
                        f.write(content)
                    except Exception as e:
                        pass
                    print('[+] Fetched {}'.format(url))

    # make a directory for the results
    try:
        os.mkdir(target_directory)
    except FileExistsError:
        pass

    # fire up 100 threads to get the images
    num_threads = 100

    threads = [FetchResource('images/', []) for i in range(num_threads)]

    while image_urls:
        for t in threads:
            try:
                t.urls.append(image_urls.pop())
            except IndexError as e:
                break

    threads = [t for t in threads if t.urls]

    for t in threads:
        t.start()

    for t in threads:
        t.join()



if __name__ == '__main__':
    args = parse_args()
    
    image_search(args.target_directory,
                 'dogs') # TODO read in list of keywords from args
