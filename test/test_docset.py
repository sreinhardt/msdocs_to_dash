#!env python3

import logging
import pytest

from msdocs_to_dash.docset import DocSource, DocSet

@pytest.fixture
def docsource():
    return DocSource("Win32k", "windows/win32/api")

@pytest.fixture
def docset(docsource):
    return DocSet("Windows Desktop Api", "Win32k", docsource)

def test_docsource_with_toc():
    ds = DocSource("Win32k", "windows/win32/api", "windows/different/toc.json")
    assert ds.toc_uri == "windows/different/toc.json"
    assert ds.get_toc_url() == f"https://learn.microsoft.com/en-us/windows/different/toc.json"

def test_docsource(docsource):
    assert docsource.title == "Win32k"
    assert docsource.base_uri == "windows/win32/api"
    assert docsource.domain == "learn.microsoft.com"
    assert docsource.theme_uri == "_themes/docs.theme/master/en-us/_themes"
    assert docsource.toc_uri == "windows/win32/api/toc.json"
    assert docsource.get_base_url() == f"https://learn.microsoft.com/en-us/windows/win32/api"
    assert docsource.get_toc_url() == f"https://learn.microsoft.com/en-us/windows/win32/api/toc.json"
    assert docsource.get_theme_url() == f"https://learn.microsoft.com/_themes/docs.theme/master/en-us/_themes"


def test_docset(docset, docsource):
    assert docset.title == "Windows Desktop Api"
    assert docset.folder == "Win32k"
    assert docset.sources == [ docsource ]
    assert docset.get_folder() == "Win32k"