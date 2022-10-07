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

@dataclass
class Child:
    parent: Union["Toc", "Branch"] = field(repr=False)
    toc_title: str
    href: Optional[str] = field(default="") # dirs must end in /
    
    def __post_init__(self):
        if not self.href:
            self.href = ""

    # call up to parent values
    def base_uri(self):
        return self.parent.base_uri()
    #def base_path(self):
    #    return self.parent.base_path()
    def domain(self):
        return self.parent.domain()
    def get_base_url(self):
        return self.parent.get_base_url()

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
        logging.info(f"Creating child for \"{title}\" to {href}")
        if not title:
            raise ValueError(f"json text cannot be Child node", text)
        return Child(parent, title, href)
    
    def get_contents(self, webdriver, output) -> List[Tuple[str, Union['Toc','Branch','Child']]]:
        '''
        Downloads text contents of this child node.
        Appends href to url and output paths for download and storage.
        Uses toc_title as %s.html
        url+href -> output+href+toc_title.html
        returns: toc url, parent
        '''
        logging.info(f"Downloading child \"{self.toc_title}\"")
        tocs = set() # just paths to get future tocs from
        if self.has_contents(output):
            logging.info("  Using previously downloaded files")
        else:
            folder = self.folder(output)
            os.makedirs(folder, exist_ok=True)
            webdriver.get_text(self.url(), self.file(output))
        if not self.isfile():
            toc = self.folder(self.base_uri())
            tocs.add(toc)
        return list(map(lambda t: (t, self), tocs)) # [(toc, self), ...]
    
    def has_contents(self, output):
        folder = self.folder(output)
        return os.path.exists(folder) and os.path.exists(self.file(output))

    def rewrite_html(self, base_uri, output, content=None):
        logging.info(f"Rewriting html for \"{self.toc_title}\"")
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
                ["div"  , { "aria-label" : "Breadcrumb", "role" : "navigation"}],
                ["div"  , { "data-bi-name" : "rating"}],
                ["div"  , { "data-bi-name" : "feedback-section"}],
                ["section" , { "class" : "feedback-section", "data-bi-name" : "feedback-section"}],
                ["footer" , { "data-bi-name" : "footer", "id" : "footer"}],
            ]
            for nav in nav_elements:
                nav_class, nav_attr = nav
                
                for nav_tag in soup.findAll(nav_class, nav_attr):
                    _ = nav_tag.extract()
            # remove script elems
            for head_script in soup.head.findAll("script"):
                    _ = head_script.extract()
            return soup
        def fix_relative_links(soup):
            for link in soup.findAll("a", { "data-linktype" : "relative-path"}):
                href = link["href"]
                fixed = href

        folder = self.folder(output)
        if not content:
            with open(self.file(folder), 'r', encoding='utf8') as f:
                content = f.read()
        
        soup = bs(content, 'html.parser')
        soup = remove_elements(soup)

        content = soup.prettify("utf-8")
        with open(self.file(folder), 'wb') as f:
            f.write(content)
        
        return content

    def dash_type(self):
        dtype = Type.from_str(self.toc_title)
        if not dtype:
            return self.parent.dash_type()

    def db_insert(self, db, dir=""):
        rec_type = self.dash_type()
        db.insert(self.toc_title, rec_type, self.file(dir))

@dataclass
class Branch(Child):
    # parent: Union["Toc", "Branch"]
    # toc_title: str
    # href: Optional[str]
    children: List[Union['Branch', 'Child']] = field(default_factory=list, repr=False)
    
    @staticmethod
    def from_json(text, parent):
        logging.info(f"Creating branch for \"{text.get('toc_title')}\"")
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
    
    def get_contents(self, webdriver, output) -> List[Tuple[str, Union['Toc','Branch','Child']]]:
        '''
        Download text contents for self if href is available as a child
        and download children to output/toc_title
        '''
        sub_tocs = list()
        logging.info(f"Downloading branch \"{self.toc_title}\"")
        if self.href:
            # download branches with href like children by using tocs
            toc = self.folder(self.base_uri())
            if toc:
                sub_tocs.append((toc, self))
        # add href pathing, and get children to it
        folder = self.folder(output)
        os.makedirs(folder, exist_ok=True)
        sub_tocs.extend(__get_contents__(self.children, webdriver, output))
        return sub_tocs
    
    def has_contents(self, output):
        folder = self.folder(output)
        if self.href:
            if not os.path.exists(folder) or \
            not os.path.exists(self.file(folder)):
                return False
        for child in self.children:
            if not child.has_contents(folder):
                return False
        return True
    
    def toc(self, domain=""):
        if self.children:
            return None
        return super().toc(domain)

    def db_insert(self, db, dir=""):
        rec_type = self.dash_type()
        db.insert(self.toc_title, rec_type, self.file(dir))
        for child in self.children:
            chld.db_insert(db, dir)

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
    
    def get_contents(self, webdriver, output) -> List[Tuple[str, Union['Toc','Branch','Child']]]:
        logging.info(f"Downloading toc to {output}")
        sub_tocs = list()
        os.makedirs(output, exist_ok=True)
        sub_tocs = __get_contents__(self.items, webdriver, output)
        logging.info(f"Completed toc download for {output}")
        return sub_tocs
    
    def has_contents(self, output):
        if not os.path.exists(output):
            return False
        for item in self.items:
            if not item.has_contents(output):
                return False
        return True

    def db_insert(self, db):
        for item in self.items:
            # should this be nothing, having sqlite inside of base_path and relative internally?
            item.db_insert(db, self.parent.base_path())

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


def __get_contents__(items, webdriver, output):
    sub_tocs = list()
    toc_paths = set()
    for item in items:
        tocs = item.get_contents(webdriver, output)
        for toc in tocs:
            if toc[0] not in toc_paths:
                sub_tocs.append(toc)
                toc_paths.add(toc[0])
    return sub_tocs