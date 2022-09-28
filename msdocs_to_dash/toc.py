#!env python3

from dataclasses import dataclass, field
from typing import Union, Optional
import logging
import json
import os
from urllib.parse import urljoin

@dataclass
class Child:
    toc_title: str
    href: Optional[str] = field(default="")
    
    @staticmethod
    def from_json(text):
        title = text.get("toc_title")
        href = text.get("href")
        if not href:
            href = ""
        logging.debug(f"Creating child for \"{title}\" to {href}")
        if not title:
            raise ValueError(f"json text cannot be Child node", text)
        return Child(title, href)
    
    def get_contents(self, webdriver, url, output):
        '''
        Downloads text contents of this child node.
        Appends href to url and output paths for download and storage.
        Uses toc_title as %s.html
        url+href -> output+href+toc_title.html
        '''
        logging.debug(f"Downloading child \"{self.toc_title}\"")
        if not self.has_contents(output):
            os.makedirs(self.folder(output), exist_ok=True)
            webdriver.get_text(self.url(url), self.file(output))
    
    def has_contents(self, output):
        return os.path.exists(self.folder(output)) and os.path.exists(self.file(output))
    
    def folder(self, dir):
        return os.path.join(dir, self.toc_title)

    def file(self, dir):
        return os.path.join(self.folder(dir), f"{self.toc_title}.html")

    def url(self, base):
        url = ""
        if base.endswith("/"):
            base = base[:-1]
        if self.href:
            if self.href.startswith("/"):
                url = f"{base}/{self.href[1:]}"
            url = f"{base}/{self.href}"
        else:
            url = base
        logging.debug(f"Generated url for \"{self.toc_title}\" to {url}")
        return url

    def rewrite_html(self, output):
        logging.debug(f"Rewriting html for \"{self.toc_title}\"")
        pass

@dataclass
class Branch(Child):
    children: [Union['Branch', 'Child']] = field(default_factory=list)
    #toc_title: str
    #href: Optional[str]
    
    @staticmethod
    def from_json(text):
        logging.debug(f"Creating branch for \"{text.get('toc_title')}\"")
        children = []
        if "children" in text:
            for item in text["children"]:
                child = None
                if "children" in item:
                    # is branch
                    child = Branch.from_json(item)
                else:
                    child = Child.from_json(item)
                children.append(child)
        return Branch(text.get("toc_title"), text.get("href"), children)
    
    def get_contents(self, webdriver, url, output):
        '''
        Download text contents for self if href is available as a child
        and download children to output/toc_title
        '''
        logging.debug(f"Downloading branch \"{self.toc_title}\"")
        if self.href:
            # download branches with href like children
            super().get_contents(webdriver, url, output)
        # add href pathing, and get children to it
        os.makedirs(self.folder(output), exist_ok=True)
        for child in self.children:
            child.get_contents(webdriver, self.url(url), self.folder(output))
    
    def has_contents(self, output):
        if self.href:
            if not os.path.exists(self.folder(output)) or \
            not os.path.exists(self.file(output)):
                return False
        for child in self.children:
            if not child.has_contents(output):
                return False
        return True
    

@dataclass
class Metadata:
    ms_author: str
    ms_prod: str
    title: str
    scope: [str]
    
    @staticmethod
    def from_json(text):
        author = text.get("ms.author")
        prod = text.get("ms.prod")
        title = text.get("titleSuffix")
        scope = []
        logging.debug(f"Creating metadata for \"{title}\"")

        if "searchScope" in text:
            for item in text["searchScope"]:
                scope.append(item)
        return Metadata(author, prod, title, scope)

@dataclass
class Toc:
    items: [Union['Branch', 'Child']]
    metadata: Optional['Metadata']
    
    @staticmethod
    def from_json(text):
        logging.debug("Toc.from_json()")
        items = []
        metadata = None
        if isinstance(text, str):
            text = json.loads(text)
        if "metadata" in text:
            metadata = Metadata.from_json(text["metadata"])
        if "items" in text:
            for item in text["items"]:
                if "children" in item:
                    items.append(Branch.from_json(item))
                else:
                    items.append(Child.from_json(item))
        return Toc(items, metadata)

    def get_contents(self, webdriver, url, output):
        logging.debug(f"Downloading toc to {output}")
        os.makedirs(output, exist_ok=True)
        for item in self.items:
            if not item.has_contents(output):
                item.get_contents(webdriver, url, output)
    
    def has_contents(self, output):
        if not os.path.exists(output):
            return False
        for item in self.items:
            if not item.has_contents(output):
                return False
        return True
