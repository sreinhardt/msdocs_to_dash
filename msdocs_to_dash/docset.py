#!env python3

from dataclasses import dataclass, field
from typing import List, Union, Tuple
import logging
import os
from urllib.parse import urljoin
from pathlib import Path
from tarfile import TarFile, TarInfo
import plistlib

from msdocs_to_dash.tar import tar_write_str, tar_write_bytes
from msdocs_to_dash.sqlite import SqLiteDb, Type
from msdocs_to_dash.toc import Toc

@dataclass
class DocCommon:
    # a class to share common data and fuctions between DocSource and DocSet
    # _css_files
    # _js_files

    def ico_path(self, dir=""):
        return Path(dir).joinpath("icon.png")
    def contents_path(self, dir=""):
        return Path(dir).joinpath("Contents/")
    def plist_path(self, dir=""):
        return self.contents_path(dir).joinpath("Info.plist")
    def resource_path(self, dir=""):
        return self.contents_path(dir).joinpath("Resources/")
    def database_path(self, dir=""):
        return self.resource_path(dir).joinpath("docSet.dsidx")
    def documents_path(self, dir=""):
        return self.resource_path(dir).joinpath("Documents/")
    def theme_path(self, dir=""):
        return self.documents_path(dir).joinpath("_themes_/")
    def theme_file_path(self, fname, dir=""):
        fname = os.path.basename(fname)
        return self.theme_path(dir).join_path(f"{fname}.html")
        
    def add_css_uri(self, uri):
        uri = uri.strip()
        if uri not in self._css_files:
                self._css_files.append(uri)
    def add_js_uri(self, uri):
        uri = uri.strip()
        if uri not in self._js_files:
            self._js_files.append(uri)

    def get_themes(self, webdriver):
        def _get_(urls, webdriver):
            results = list()
            for url in urls:
                fname = os.path.basename(url)
                data = webdriver.get_text(url)
                results.append((fname, data))
            return results

        self._css_files = _get_(self._css_files, webdriver)
        self._js_files =  _get_(self._js_files, webdriver)
    def write_contents(self, output):
        # writes to local files
        theme_path = self.theme_path(output)
        os.makedirs(theme_path)
        for data in self._css_files + self._js_files:
            with open(self.theme_file_path(data[0]), 'w') as f:
                f.write(data[1])

@dataclass
class DocSource(DocCommon):
    title: str    # win32k
    base_uri: str # "/windows/win32/api"
    toc_uri: str = "toc.json"   # if relative, append to base, otherwise is absolute to domain
    theme_uri: str = "_themes/docs.theme/master/en-us/_themes"
    language: str = "en-us"
    domain: str = "learn.microsoft.com"
    parent: 'DocSet' = None
    index: 'Toc' = field(default=None, init=False, repr=False)
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
        self.index = Toc.from_json(toc_json, self)
        self.index.get_index(self.title, webdriver, input)
        todo_tocs = self.index.get_contents(webdriver, input)
        self._tocs.append(self.index)
        complete_tocs.add(self.get_toc_url())
        idx = 0
        while idx < len(todo_tocs): # (toc_uri, parent)
            toc = todo_tocs[idx]
            if not isinstance(toc, tuple):
                idx += 1
                continue
            toc_json = ""
            if toc[0].strip("/") == self.index.base_uri():
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
        self.index.write_index(self.documents_path(output))
        super().write_contents(self.documents_path(output))
        for toc in self._tocs:
            toc.write(self.documents_path(output))
    
    def write_tar(self, tar):
        self.index.write_index_tar(tar)
        for data in self._css_files + self._js_files:
            tar_write_str(
                tar,
                self.theme_file_path(data[0]),
                data[1]
            )
        for toc in self._tocs:
            toc.write_tar(tar)
        
    def make_database(self, db):
        for toc in self._tocs:
            toc.db_insert(db)
    # terminate
    def folder(self, dir):
        return dir
    def output(self, dir):
        if self.parent:
            return self.parent.output(dir)
        return dir

@dataclass
class DocSet(DocCommon):
    title: str
    identifier: str = field(default="")    
    sources: List["DocSource"] = field(default_factory=list)
    ico_uri: str = "media/logos/logo-ms-social.png"
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
    
    def write_contents(self, output):
        # writes to local files
        super().write_contents(output)
        with open(self.ico_path(output), 'wb') as f:
            f.write(self._ico)
        with open(self.plist_path(output), 'wb') as f:
            f.write(self.make_plist())
        for source in self.sources:
            source.write_contents(output)
        self.make_database(output)
        
    def make_plist(self, index_path="") -> str:
        index_path = Path(index_path).joinpath("index.html")
        data = {
            'CFBundleIdentifier':           self.identifier,
            'CFBundleName':                 self.title,
            'DashDocSetFallbackURL':        self.sources[0].get_base_url(),
            'dashIndexFilePath':            str(index_path),
            'DashDocSetFamily':             "dashtoc",
            'DocSetPlatformFamily':         self.identifier,
            'isDashDocset':                 True,
            'isJavaScriptEnabled':          True,
            'DashDocSetDefaultFTSEnabled':  True

        }
        return plistlib.dumps(data)
    
    def make_database(self, output):
        db_path = self.database_path(output)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db = SqLiteDb.new(db_path)
        for source in self.sources:
            source.make_database(db)
        db.close()

    def make_package(self, output):
        tar_path = Path(output).joinpath(f"{self.title}.tar")
        with TarFile.open(str(tar_path), "w:gz") as tar:
            tar_write_bytes(tar, self.ico_path(), self._ico)
            tar_write_bytes(tar, self.plist_path(), self.make_plist())
            for data in self._css_files + self._js_files:
                tar_write_str(
                    tar,
                    self.theme_file_path(data[0], output),
                    data[1]
                )
            for source in self.sources:
                source.write_tar(tar)
            tar.add(self.database_path(output), self.database_path())
            # add toc

    def get_themes(self, webdriver):
        self._ico = self.get_ico(webdriver)
        super().get_themes(webdriver)
    
    def get_ico_url(self, domain="", uri=""):
        if not domain:
            domain = self.sources[0].domain
        if not uri:
            uri = self.ico_uri
        return f"https://{domain}/{uri}"
    
    def get_ico(self, webdriver) -> bytes:
        return webdriver.get_binary(self.get_ico_url())
    


# add plist entries to docset, explore multi docsource pathing and entries
# replace get_ico in docsource with variable pathing

