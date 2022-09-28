#!env python3

from dataclasses import dataclass


@dataclass
class DocSource:
    title: str
    base_uri: str
    toc_uri: str = "toc.json"   # if relative, append to base, otherwise is absolute to domain
    theme_uri: str = "_themes/docs.theme/master/en-us/_themes"
    domain: str = "learn.microsoft.com"

    def __post_init__(self):
        if self.base_uri.starts_with('/'):
            self.base_uri = self.base_uri[1:]
        if self.base_uri.ends_with('/'):
            self.base_uri = self.base_uri[:-1]
        
        if self.theme_uri.starts_with('/'):
            self.theme_uri = self.theme_uri[1:]
        
        if not self.toc_uri.starts_with('/'):
            self.toc_uri = f"{self.base_uri}/{self.toc_uri}"
    
    def toc_uri(self):
        return f"https://{self.domain}/{self.toc_uri}"
    
    def theme_uri(self):
        return f"https://{self.domain}/{self.theme_uri}"

@dataclass
class DocSet:
    title: str
    sources: [DocSource]

    def __post_init__(self):
        if isinstance(self.sources, DocSource):
            self.sources = [self.sources]
        