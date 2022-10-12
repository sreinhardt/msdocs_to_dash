#!env python3

from . import webdriver
from . import tar
from . import sqlite
from . import toc
from . import docset
from . import downloader


'''
import logging
logging.basicConfig(level=logging.INFO)
from msdocs_to_dash import *
dl = downloader.MsDownloader(downloader.DOC_SETS[1], "../doctest")
dl.build_dash()
'''