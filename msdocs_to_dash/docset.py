#!env python3

from dataclasses import dataclass, field
from typing import List, Union, Tuple
import logging
import os
from urllib.parse import urljoin

from msdocs_to_dash.toc import Toc

@dataclass
class DocSource:
    title: str    # win32k
    base_uri: str # "/windows/win32/api"
    toc_uri: str = "toc.json"   # if relative, append to base, otherwise is absolute to domain
    theme_uri: str = "_themes/docs.theme/master/en-us/_themes"
    language: str = "en-us"
    domain: str = "learn.microsoft.com"
    parent: 'DocSet' = None

    def __post_init__(self):
        # remove leading and trailing for appending
        for member in ["base_uri", "theme_uri", "toc_uri", "language", "domain"]:
            val = getattr(self, member).strip("/")
            setattr(self, member, val)
        # append toc to base for full path
        if "toc.json" == self.toc_uri:
            self.toc_uri = f"{self.base_uri}/{self.toc_uri}"
        
    def get_base_url(self):
        return f"https://{self.domain}/{self.language}/{self.base_uri}"
    
    def get_toc_url(self, toc=""):
        if not toc:
            toc = self.toc_uri
        toc = toc.strip("/")
        if not toc.endswith("/toc.json"):
            toc = f"{toc}/toc.json"
        return f"https://{self.domain}/{self.language}/{toc}"
    
    def get_theme_url(self):
        return f"https://{self.domain}/{self.theme_uri}"
    
    def get_contents(self, webdriver, output):
        todo_tocs = list() # (str, toc)
        complete_tocs = set() # str
        toc_json = webdriver.get_text(self.get_toc_url())
        base_toc = Toc.from_json(toc_json, self)
        todo_tocs = base_toc.get_contents(webdriver, output)
        complete_tocs.add(self.get_toc_url())
        idx = 0
        while idx < len(todo_tocs): # (toc_uri, parent)
            toc = todo_tocs[idx]
            toc_json = ""
            if toc[0].strip("/") == base_toc.base_uri():
                idx += 1
                continue
            toc_json = webdriver.get_text(self.get_toc_url(toc[0]))
            child_toc = Toc.from_json(toc_json, toc[1])
            moar_tocs = child_toc.get_contents(webdriver, output)
            complete_tocs.add(toc[0])
            for mtoc in moar_tocs:
                if mtoc[0] not in complete_tocs:
                    todo_tocs.append(mtoc)
            idx += 1

    # terminate
    def folder(self, dir):
        return dir
    def output(self, dir):
        if self.parent:
            return self.parent.output(dir)
        return dir

@dataclass
class DocSet:
    title: str
    folder: str = field(default="")
    sources: List["DocSource"] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.sources, DocSource):
            self.sources = [self.sources]
        for source in self.sources:
            if not source.parent:
                source.parent = self
        
    def get_folder(self):
        return self.folder if self.folder else self.title
    
    def get_contents(self, webdriver, output):
        if output:
            output = os.path.join(output, self.folder)
        for source in self.sources:
            source.get_contents(webdriver, output)