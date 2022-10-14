#!env python3

from dataclasses import dataclass, field
from typing import List, Union, Tuple
import logging
import os
from urllib.parse import urljoin
from pathlib import Path
import plistlib

from msdocs_to_dash.tar import tar_write_str, tar_write_bytes
from msdocs_to_dash.sqlite import SqLiteDb, Type
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
    _tocs: List[Toc] = field(default_factory=list, init=False, repr=False)
    # complete urls built on addition url -> (url, data)
    _css_files: List[Union[str, Tuple[str,str]]] = field(default_factory=list, init=False, repr=False)
    _js_files: List[Union[str, Tuple[str,str]]] = field(default_factory=list, init=False, repr=False)

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
    
    def get_theme_url(self, url=""):
        if not url:
            url = self.theme_uri
        url = url.lstrip("/")
        return f"https://{self.domain}/{url}"
    
    def get_contents(self, webdriver, input):
        todo_tocs = list() # (str, toc)
        complete_tocs = set() # str
        toc_json = webdriver.get_text(self.get_toc_url())
        base_toc = Toc.from_json(toc_json, self)
        todo_tocs = base_toc.get_contents(webdriver, input)
        self._tocs.append(base_toc)
        complete_tocs.add(self.get_toc_url())
        idx = 0
        while idx < len(todo_tocs): # (toc_uri, parent)
            toc = todo_tocs[idx]
            if not isinstance(toc, tuple):
                idx += 1
                continue
            toc_json = ""
            if toc[0].strip("/") == base_toc.base_uri():
                idx += 1
                continue
            toc_json = webdriver.get_text(self.get_toc_url(toc[0]))
            child_toc = Toc.from_json(toc_json, toc[1])
            moar_tocs = child_toc.get_contents(webdriver, input)
            complete_tocs.add(toc[0])
            self._tocs.append(child_toc)
            for mtoc in moar_tocs:
                if mtoc[0] not in complete_tocs:
                    todo_tocs.append(mtoc)
            idx += 1

    def write_contents(self, output):
        for toc in self._tocs:
            toc.write(output)
    
    def get_themes(self, webdriver):
        css_files = list()
        for css in self._css_files:
            fname = os.path.basename(css)
            css = webdriver.get_text(css)
            css_files.append(fname, css)
        self._css_files = css_files
        js_files = list()
        for js in self._js_files:
            fname = os.path.basename(css)
            js = webdriver.get_text(css)
            js_files.append(fname, js)
        self._js_files = js_files

    def write_tar(self, tar):
        theme_path = Path("Contents/Resources/Documents/_themes_")
        for data in self._css_files + self._js_files:
            tar_write_str(
                tar,
                theme_path.joinpath(os.path.basename(data[0])),
                data[1]
            )
        for toc in self._tocs:
            toc.write_tar(tar)
        
    def make_db(self, db):
        for toc in self._tocs:
            toc.db_insert(db)
    # terminate
    def folder(self, dir):
        return dir
    def output(self, dir):
        if self.parent:
            return self.parent.output(dir)
        return dir
    def add_css_uri(self, uri):
        if uri.startswith("/"):
            if uri not in self._css_files:
                self._css_files.append(uri)
        else:
            self.parent.add_css_uri
    def add_js_uri(self, uri):
        if uri.startswith("/"):
            if uri not in self._js_files:
                self._js_files.append(uri)
        else:
            self.parent.add_js_uri
    def get_ico(self, webdriver) -> bytes:
        return webdriver.get_binary(self.get_toc_url("media/logos/logo-ms-social.png"))

@dataclass
class DocSet:
    title: str
    identifier: str = field(default="")
    sources: List["DocSource"] = field(default_factory=list)
    # complete urls built on addition url -> (url, data)
    _css_files: List[Union[str, Tuple[str,str]]] = field(default_factory=list, init=False, repr=False)
    _js_files: List[Union[str, Tuple[str,str]]] = field(default_factory=list, init=False, repr=False)
    _ico: bytes = field(default=b'', init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.sources, DocSource):
            self.sources = [self.sources]
        for source in self.sources:
            if not source.parent:
                source.parent = self
    
    def get_contents(self, webdriver, input):
        for source in self.sources:
            source.get_contents(webdriver, input)
        self.get_themes(webdriver)
    
    def write_contents(self, tar):
        for data in self._css_files + self._js_files:
            breakpoint()
        for source in self.sources:
            source.write_contents(tar)
        
    def make_plist(self, index_path="") -> str:
        index_path = Path(index_path).joinpath("index.html")
        data = {
            'CFBundleIdentifier':    self.identifier,
            'CFBundleName':          self.title,
            'DashDocSetFallbackURL': self.sources[0].get_base_url(),
            'dashIndexFilePath':     index_path,
            'DashDocSetFamily':      self.identifier,
            'DocSetPlatformFamily':  self.identifier,
            'isDashDocset':          True,
            'isJavaScriptEnabled':   True

        }
        return plistlib.dumps(data)
    
    def make_database(self, output):
        db = Path(output).joinpath("docSet.dsidx")
        db = sqlite.new(db)
        for source in self.sources:
            source.make_database(db)
        db.close()

    def make_package(self, output):
        tar_path = Path(output).joinpath(f"{self.title}.tar")
        ico_path = Path("icon.png")
        plist_path = Path("Contents/Info.plist")
        rec_path = Path("Contents/Resources")
        db_file_path = Path(output).joinpath("docSet.dsidx")
        db_path = rec_path.joinpath("docSet.dsidx")
        doc_path = rec_path.joinpath("Documents")
        theme_path = doc_path.joinpath("_themes_")
        with tarfile.open(tar_path, "w:gz") as tar:
            tar_write_bytes(tar, ico_path, self._ico)
            tar_write_str(tar, plist_path, self.make_plist())
            for data in self._css_files + self._js_files:
                tar_write_str(
                    tar,
                    theme_path.joinpath(os.path.basename(data[0])),
                    data[1]
                )
            for source in self.sources:
                source.write_tar(tar)
            tar.add(db_file_path, db_path)
            # add toc

    def get_themes(self, webdriver):
        self._ico = self.sources[0].get_ico(webdriver)
        css_files = list()
        for css in self._css_files:
            fname = os.path.basename(css)
            css = webdriver.get_text(css)
            css_files.append(fname, css)
        self._css_files = css_files
        js_files = list()
        for js in self._js_files:
            fname = os.path.basename(css)
            js = webdriver.get_text(css)
            js_files.append(fname, js)
        self._js_files = js_files
        for source in self.sources:
            source.get_themes(webdriver)
    
    def add_css_uri(self, uri):
        uri = uri.strip()
        if uri not in self._css_files:
                self._css_files.append(uri)
    def add_js_uri(self, uri):
        uri = uri.strip()
        if uri not in self._js_files:
            self._js_files.append(uri)

# add plist entries to docset, explore multi docsource pathing and entries
# make tocs


