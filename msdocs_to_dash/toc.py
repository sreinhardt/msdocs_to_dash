#!env python3

from dataclasses import dataclass, field
from typing import Union, Optional, List, Set, Tuple
import logging
import json
import os
import regex
from pathlib import Path
from bs4 import BeautifulSoup as bs, Tag

from msdocs_to_dash.sqlite import SqLiteDb, Type
from msdocs_to_dash.tar import tar_write_str, tar_write_bytes

@dataclass
class Child:
    parent: Union["Toc", "Branch"] = field(repr=False)
    toc_title: str
    href: Optional[str] = field(default="") # dirs must end in /
    contents: Optional[str] = field(default="", init=False, repr=False)
    
    def __post_init__(self):
        if not self.href:
            self.href = ""

    # call up to parent values
    def base_uri(self):
        return self.parent.base_uri()
    def add_css_uri(self, uri):
        self.parent.add_css_uri(uri)
    def add_js_uri(self, uri):
        self.parent.add_js_uri(uri)
    def domain(self):
        return self.parent.domain()
    def get_base_url(self):
        return self.parent.get_base_url()
    def get_theme_url(self, url=""):
        return self.parent.get_theme_url(url)
    @staticmethod
    def _reduce_(root, path):
        # given root: windows/win32/api and path: /windows/win32/api/adsprop/ -> adsprop/
        if root in path:
            idx = path.find(root)
            end = idx+len(root)
            path = path[end:]
        return path

    def folder(self, dir=""):
        # get a normalized path from self.href and append to dir
        # can be used for both local and uri paths
        href = self.href
        if self.isfile():
            href = os.path.dirname(href)
        if os.path.isabs(href):
            # no parent pathing, just remove base path to get module
            # href = reduce(href, base_path) # /windows/win32/api/adsprop/, windows/win32/api -> adsprop/
            href = Child._reduce_(self.base_uri(), href)
            if href.startswith("/"):
                href = href[1:] # remove before join
        else:
            href = os.path.join(self.parent.folder(""), href)
        href = os.path.join(dir, href)
        href = os.path.normpath(href) # resolve ../ without finding absolute path with current dir
        if href in [ "", ".", "./" ]:
            href = self.parent.folder(dir)
        if href and not href.endswith("/"):
            # allow blank returns without appending /
            href = f"{href}/"
        return href

    def file(self, dir=""):
        # returns local file path for this node joined to dir
        path = os.path.join(self.folder(dir), "index.html")
        if self.isfile():
            path = os.path.join(self.folder(dir), f"{os.path.basename(self.href)}.html")
        return Path(path)

    def isfile(self):
        if self.href:
            return not self.href.endswith("/")
        return False
    
    def url(self):
        domain = self.parent.get_base_url()
        uri = self.folder().lstrip("/")
        if self.isfile():
            uri = os.path.join(uri, os.path.basename(self.href))
        return f"{domain}/{uri}"

    def toc(self):
        if self.isfile():
            return None
        url = self.url().rstrip("/")
        return f"{url}/toc.json"

    @staticmethod
    def from_json(text, parent):
        title = text.get("toc_title")
        href = text.get("href")
        if not href:
            href = ""
        logging.debug(f"Creating child for \"{title}\" to {href}")
        if not title:
            raise ValueError(f"json text cannot be Child node", text)
        return Child(parent, title, href)
    
    def get_contents(self, webdriver, input) -> List[Tuple[str, Union['Toc','Branch','Child']]]:
        '''
        Downloads text contents of this child node.
        Appends href to url and output paths for download and storage.
        Uses toc_title as %s.html
        url+href -> output+href+toc_title.html
        returns: toc url, parent
        '''
        logging.info(f"Accessing child \"{self.toc_title}\"")
        tocs = set() # just paths to get future tocs from
        if self.has_contents(input):
            logging.debug("  Using previously downloaded files")
            if not self.contents:
                self.read(input)
        else:
            logging.debug("  Downloading new file")
            breakpoint()
            self.contents = webdriver.get_text(self.url())
        self.rewrite_html() # always rewrite, wont harm previously done files
        if not self.isfile():
            tocs.add( self.folder(self.base_uri()) )
        return list(map(lambda t: (t, self), tocs)) # [(toc, self), ...]
    
    def has_contents(self, output):
        if self.contents:
            return True
        return os.path.exists(self.folder(output)) and os.path.exists(self.file(output))

    def rewrite_html(self):
        if not self.contents:
            raise RuntimeError("Cannot rewrite html without contents", self)
        def remove_elements(soup):
            # remove link to external references since we can't support it
            for abs_href in soup.findAll("a", { "data-linktype" : "absolute-path"}):
                abs_href.replace_with(abs_href.text)
            # remove unsupported nav elements
            nav_elements = [
                ["nav"  , { "class" : "doc-outline", "role" : "navigation"}],
                ["ul"   , { "class" : "breadcrumbs", "role" : "navigation"}],
                ["div"  , { "class" : "sidebar", "role" : "navigation"}],
                ["div"  , { "class" : "dropdown dropdown-full mobilenavi"}],
                ["p"    , { "class" : "api-browser-description"}],
                ["div"  , { "class" : "api-browser-search-field-container"}],
                ["div"  , { "class" : "pageActions"}],
                ["div"  , { "class" : "container footerContainer"}],
                ["div"  , { "class" : "dropdown-container"}],
                ["div"  , { "class" : "page-action-holder"}],
                ["div"  , { "class" : "header-holder"}],
                ["div"  , { "id"    : "article-header"}],
                ["div"  , { "id"    : "user-feedback"}],
                ["div"  , { "aria-label" : "Breadcrumb", "role" : "navigation"}],
                ["div"  , { "data-bi-name" : "rating"}],
                ["div"  , { "data-bi-name" : "feedback-section"}],
                ["ul"   , { "class":"links", "data-bi-name":"footerlinks"}],
                ["section" , { "class" : "feedback-section", "data-bi-name" : "feedback-section"}],
                ["footer" , { "data-bi-name" : "footer", "id" : "footer"}],
            ]
            for nav in nav_elements:
                nav_class, nav_attr = nav
                
                for nav_tag in soup.findAll(nav_class, nav_attr):
                    _ = nav_tag.extract()
            for head_script in soup.head.findAll("script",{"src":True}):
                if head_script["src"].startswith('http'):
                    # only want to remove externals
                    _ = head_script.extract()
            return soup
        def fix_relative_links(soup):
            for link in soup.findAll("a", { "data-linktype" : "relative-path"}):
                href = link["href"]
                if href.endswith("/"): # is dir point to index
                    href = f"{href}index.html"
                else: # is file, just add html
                    href = f"{href}.html"
                if href != link["href"]:
                    link["href"] = href
            return soup
        def find_extra_files(soup):
            for link in soup.findAll('a',{'rel': 'stylesheet'}):
                self.add_css_uri(f"{self.get_theme_url(link['href'])}")
                link['href'] = f"/_themes_/{os.path.basename(link['href'])}"
            for link in soup.findAll('script',{"src":True}):
                self.add_js_uri(f"{self.get_theme_url(link['src'])}")
                link['href'] = f"/_themes_/{os.path.basename(link['src'])}"
            return soup
        
        soup = bs(self.contents, 'html.parser')
        soup = remove_elements(soup)
        soup = fix_relative_links(soup)
        soup = find_extra_files(soup)
        self.contents = soup.prettify("utf-8")

    def dash_type(self):
        dtype = Type.from_str(self.toc_title)
        if not dtype:
            return self.parent.dash_type()

    def db_insert(self, db):
        rec_type = self.dash_type()
        db.insert(self.toc_title, rec_type, self.file())

    def write(self, output):
        if not self.contents:
            raise RuntimeError("Cannot write contents without them")
        os.mkdirs(self.folder(output), exist_ok=True)
        with open(self.file(output), 'w', encoding="utf8") as f:
                f.write(self.contents)
    
    def read(self, input):
        with open(self.file(input), encoding="utf8") as f:
            self.contents = f.read()

    def write_tar(self, tar):
        doc_path = Path("Contents/Resources/Documents")
        tar_write_str(tar, doc_path.join_path(self.file()), self.contents)

@dataclass
class Branch(Child):
    # parent: Union["Toc", "Branch"]
    # toc_title: str
    # href: Optional[str]
    children: List[Union['Branch', 'Child']] = field(default_factory=list, repr=False)
    
    @staticmethod
    def from_json(text, parent):
        logging.debug(f"Creating branch for \"{text.get('toc_title')}\"")
        branch = Branch(parent, text.get("toc_title"), text.get("href"), [])
        
        if "children" in text:
            for item in text["children"]:
                child = None
                if "children" in item:
                    child = Branch.from_json(item, branch)
                else:
                    child = Child.from_json(item, branch)
                branch.children.append(child)
        return branch
    
    def get_contents(self, webdriver, input) -> List[Tuple[str, Union['Toc','Branch','Child']]]:
        '''
        Download text contents for self if href is available as a child
        and download children to output/toc_title
        '''
        sub_tocs = list()
        logging.info(f"Downloading branch \"{self.toc_title}\"")
        if self.href:
            # download branches with href like children by using tocs
            sub_tocs.append(self.folder(self.base_uri()))
        # add href pathing, and get children to it
        sub_tocs.extend(__get_contents__(self.children, webdriver, input))
        return sub_tocs
    
    def has_contents(self, output):
        if self.href:
            if not os.path.exists(self.folder(output)) or \
            not os.path.exists(self.file(fooutputlder)):
                breakpoint()
                return False
        for child in self.children:
            if not child.has_contents(output):
                return False
                breakpoint()
        return True
    
    def toc(self, domain=""):
        if self.children:
            return None
        return super().toc(domain)

    def db_insert(self, db):
        rec_type = self.dash_type()
        # isfile?
        db.insert(self.toc_title, rec_type, self.file())
        for child in self.children:
            chld.db_insert(db)

    def write(self, output):
        if self.contents:
            super().write(output)
        os.mkdirs(self.folder(output), exist_ok=True)
        for child in self.children:
            child.write(output)
    
    def read(self, input):
        if self.isfile():
            super().read(input)
        idx = 0
        while idx < len(self.children):
            self.children[idx].read(input)
            idx += 1

    def write_tar(self, tar):
        if self.isfile():
            super().write_tar(tar)
        for child in self.children:
            child.write_tar(tar)

@dataclass
class Metadata:
    ms_author: str
    ms_prod: str
    title: str
    scope: List[str]
    
    @staticmethod
    def from_json(text):
        author = text.get("ms.author")
        prod = text.get("ms.prod")
        title = text.get("titleSuffix")
        scope = []
        logging.info(f"Creating metadata for \"{title}\"")

        if "searchScope" in text:
            for item in text["searchScope"]:
                scope.append(item)
        return Metadata(author, prod, title, scope)

@dataclass
class Toc:
    items: List[Union['Branch', 'Child']]
    metadata: Optional['Metadata']
    parent: Optional[Union['DocSource', 'Toc']] = field(default=None, repr=False)
    
    @staticmethod
    def from_json(text, parent=None):
        logging.info("Toc.from_json()")
        items = []
        metadata = None
        if isinstance(text, str):
            text = json.loads(text)
        if "metadata" in text:
            metadata = Metadata.from_json(text["metadata"])
        toc = Toc([], metadata, parent)
        if "items" in text:
            for item in text["items"]:
                if "children" in item:
                    toc.items.append(Branch.from_json(item, toc))
                else:
                    toc.items.append(Child.from_json(item, toc))
        return toc
    
    def get_contents(self, webdriver, input) -> List[Tuple[str, Union['Toc','Branch','Child']]]:
        logging.info(f"Downloading toc {self.metadata.title}")
        sub_tocs = list()
        sub_tocs = __get_contents__(self.items, webdriver, input)
        logging.info(f"Completed toc download for {self.metadata.title}")
        return sub_tocs
    
    def has_contents(self, output):
        for item in self.items:
            if not item.has_contents(output):
                return False
        return True

    def write_contents(self, output):
        for item in self.items:
            item.write(output)

    def db_insert(self, db):
        for item in self.items:
            # should this be nothing, having sqlite inside of base_path and relative internally?
            item.db_insert(db)

    def write_tar(self, tar):
        for item in self.items:
            item.write_tar(tar)

    # terminate parent calls
    def folder(self, dir):
        if not self.parent:
            return dir
        return self.parent.folder(dir)
    def dash_type(self):
        return Type.Category
    
    # to docsource
    def base_uri(self):
        if self.parent:
            if isinstance(self.parent, (Toc, Branch, Child)):
                return self.parent.base_uri()
            return self.parent.base_uri
        raise RuntimeError("No docsource to request base_uri from")
    def domain(self):
        if self.parent:
            if isinstance(self.parent, Toc):
                return self.parent.domain()
            else:
                return self.parent.domain
        raise RuntimeError("No docsource to request domain from")
    def get_base_url(self):
        if self.parent:
            return self.parent.get_base_url()
        raise RuntimeError("No docsource to request base url from")
    def get_theme_url(self, url=""):
        return self.parent.get_theme_url(url)
    def add_css_uri(self, uri):
        self.parent.add_css_uri(uri)
    def add_js_uri(self, uri):
        self.parent.add_js_uri(uri)

def __get_contents__(items, webdriver, input):
    sub_tocs = list()
    toc_paths = set()
    for item in items:
        tocs = item.get_contents(webdriver, input)
        for toc in tocs:
            if toc[0] not in toc_paths:
                sub_tocs.append(toc)
                toc_paths.add(toc[0])
    return sub_tocs