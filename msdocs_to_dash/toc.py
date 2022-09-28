#!env python3

from dataclasses import dataclass
from typing import Union, Optional

@dataclass
class Child:
    toc_title: str
    href: Optional[str]
    
    @classmethod
    def from_json(cls, text, self=None):
        title = ""
        href = ""
        if "title" in text:
            title = text["title"]
        if "href" in text:
            href = text["href"]
        if not title:
            raise ValueError(f"json text cannot be {cls.__name__} node", text)
        if self:
            self.title = title
            self.href = href
            return self
        return cls(title=title, href=href)

@dataclass
class Branch(Child):
    children: [Union['Branch', 'Child']]
    #toc_title: str
    #href: Optional[str]
    
    @classmethod
    def from_json(cls, text):
        branch = None
        children = []
        if "children" in text:
            for item in text["children"]:
                child = None
                if "children" in item:
                    child = cls.from_json(item)    
                # append title and possibly href
                # or if child is none, create new child node
                child = super().from_json(item, child)
                children.push(child)
            branch = cls(children)
        # as above, append title and possibly href
        # or if child is none, create new child node
        branch = super().from_json(text, branch)
        return branch

@dataclass
class Metadata:
    ms_author: str
    ms_prod: str
    title: str
    scope: [str]
    
    @classmethod
    def from_json(cls, text):
        author = ""
        prod = ""
        title = ""
        scope = []

        if "ms.author" in text:
            author = text["ms.author"]
        if "ms.prod" in text:
            prod = text["ms.prod"]
        if "titleSuffix" in text:
            title = text["titleSuffix"]
        if "searchScope" in text:
            for item in text["searchScope"]:
                scope.push(item)
        return cls(author, prod, title, scope)

@dataclass
class Toc:
    items: [Union['Branch', 'Child']]
    metadata: Optional['Metadata']
    
    @classmethod
    def from_json(cls, text):
        items = []
        metadata = None
        if "metadata" in text:
            metadata = Metadata.from_json(text["metadata"])
        if "items" in text:
            for item in text["items"]:
                if "children" in item:
                    items.push(Branch.from_json(item))
                else:
                    items.push(Child.from_json(item))
        return cls(items, metadata)

