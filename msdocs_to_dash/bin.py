#!env python3

from dataclasses import dataclass

from .webdriver import *
from .toc import *
from .docset import *

DOC_SOURCES = [
    DocSet("Powershell",
    [
        DocSource("Powershell", "en-us/powershell/module", "psdocs/toc.json")
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
        self.webdriver = WebDriver()
    
    def build_dash(self):
        
