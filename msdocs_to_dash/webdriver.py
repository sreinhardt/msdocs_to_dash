#!env python3

from dataclasses import dataclass, field
from typing import Any

import logging
import os
import requests
import time
import urllib
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import ConnectionError

from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

@dataclass
class WebDriver:
    options: 'Options' = field(init=False, repr=False)
    driver: 'Chrome' = field(init=False, repr=False)
    session: 'Session' = field(init=False, repr=False)

    def __post_init__(self):
        logging.info("Initalizing WebDriver")
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--window-size=1920x1080")   
        self.driver = webdriver.Chrome(options=self.options)
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def quit():
        logging.info("Closing WebDriver")
        return self.driver.quit()

    def get_url_page(self, url):
        """ retrieve the full html content of a page after Javascript execution """
        logging.info(f"Chrome request for \"{url}\"")
        index_html = None
        try:
            self.driver.get(url)
            index_html = self.driver.page_source
        except (ConnectionResetError, urllib.error.URLError) as e:
            self.driver.quit()
            time.sleep(2)
            self.driver = webdriver.Chrome(options=self.options)
            index_html = None
        # try a second time, and raise error if fail
        if not index_html:
            self.driver.get(url)
            index_html = self.driver.page_source

        return index_html

    def get_binary(self, url, output=None):
        logging.info(f"Binary request for \"{url}\"")
        if output:
            os.makedirs(os.path.dirname(output), exist_ok = True)
        r = None
        while True:
            try:
                r = self.session.get(url, stream=True)
            except ConnectionError:
                logging.info("caught ConnectionError, retrying...")
                time.sleep(2)
            else:
                break
        if output:
            with open(output, 'wb') as f:
                for data in r.iter_content(32*1024):
                    f.write(data)
            return None
        return r.content
    
    def get_text(self, url, output=None, params=None):
        logging.info(f"Text request for \"{url}\"")
        if output:
            os.makedirs(os.path.dirname(output), exist_ok = True)
        while True:
            try:
                r = self.session.get(url, data = params)
            except ConnectionError:
                logging.info("caught ConnectionError, retrying...")
                time.sleep(2)
            else:
                break
        if output:
            with open(output, 'w', encoding="utf8") as f:
                f.write(r.text)
            return None
        return r.text
