#!env python3

from dataclasses import dataclass, field
from typing import List
import logging

from .webdriver import *
from .toc import *
from .docset import *

DOC_SETS = [
    DocSet("Powershell",
    [
        DocSource("PsDocs", "powershell/module", "psdocs/toc.json"),
        DocSource("Ps2019", "powershell/module", "windowsserver2019-ps/toc.json?view=windowsserver2019-ps")
    ]),
    DocSet("Windows Desktop Api", "Win32k", DocSource("Win32k", "windows/win32/api")),
    DocSet("Windows Driver Framework", "WDF", DocSource("WDF", "windows-hardware/drivers/wdf")),
    DocSet("Kernel Mode Development", "KMD", DocSource("KMD", "windows-hardware/drivers/kernel")),
]

@dataclass
class MsDownloader:
    source: 'DocSet'
    output: str = "./docs"
    webdriver: 'WebDriver' = field(init=False, repr=False)


    def __post_init__(self):
        logging.info(f"Created downloader for {self.source.title}")
        self.webdriver = WebDriver()
    
    def build_dash(self):
        logging.info(f"Building dash docset for {self.source.title}")
        self.source.get_contents(self.webdriver, self.output)
        self.source.get_themes(self.webdriver)
        self.source.make_database(self.output)
        self.source.make_package(self.output)