#!env python3

from dataclasses import dataclass, field
import logging

from .webdriver import *
from .toc import *
from .docset import *

DOC_SETS = [
    DocSet("Powershell",
    [
        DocSource("PsDocs", "en-us/powershell/module", "psdocs/toc.json"),
        DocSource("Ps2019", "en-us/powershell/module", "windowsserver2019-ps/toc.json?view=windowsserver2019-ps")
    ]),
    DocSet("Windows Desktop Api", DocSource("Win32k", "en-us/windows/win32/api")),
    DocSet("Windows Driver Framework", DocSource("WDF", "en-us/windows-hardware/drivers/wdf")),
    DocSet("Kernel Mode Development", DocSource("KMD", "en-us/windows-hardware/drivers/kernel")),
]

@dataclass
class MsDownloader:
    source: 'DocSet'
    output: str = "./docs"
    webdriver: 'WebDriver' = field(init=False, repr=False)


    def __post_init__(self):
        logging.debug(f"Created downloader for {self.source.title}")
        self.webdriver = WebDriver()
    
    def build_dash(self):
        logging.debug(f"Building dash docset for {self.source.title}")
        for source in self.source.sources:
            toc = self.webdriver.get_text(source.get_toc_uri())
            toc = Toc.from_json(toc)
            toc.get_contents(self.webdriver, source.get_base_uri(), self.output)
