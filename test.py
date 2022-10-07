#!env python3
import logging
logging.basicConfig(level=logging.INFO)
from msdocs_to_dash import *
dl = downloader.MsDownloader(downloader.DOC_SETS[1], "../doctest")
dl.build_dash()
