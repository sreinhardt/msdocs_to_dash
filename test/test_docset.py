#!env python3

import logging
import pytest
import os
from copy import deepcopy
from tarfile import TarFile
from pathlib import Path

from msdocs_to_dash.webdriver import WebDriver
from msdocs_to_dash.docset import DocSource, DocSet

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

def test_docsource_get_contents(root_toc, webserver, html_ok):
    ds = root_toc.parent
    ds.get_contents(WebDriver(), "")
    assert ds._css_files == ['https://learn.microsoft.com/test/blah/file.css']
    assert ds._js_files == []
    assert len(ds._tocs) == 3

def test_docsource_get_css(root_toc, webserver, css_ok):
    ds = root_toc.parent
    ds.get_contents(WebDriver(), "")
    assert ds._css_files == ['https://learn.microsoft.com/test/blah/file.css']
    ds.get_themes(WebDriver())
    assert ds._css_files == [(Path('Contents/Resources/Documents/_themes_/file.css'), css_ok)]
    
def test_docsource_write(root_toc, webserver, tmp_path):
    # docsource forces packaging paths
    ds = root_toc.parent
    ds.get_contents(WebDriver(), "")
    ds.get_themes(WebDriver())
    ds.write_contents(tmp_path)
    docs_path = f"{tmp_path}/Contents/Resources/Documents"
    assert os.path.exists(f"{tmp_path}")
    assert os.path.exists(f"{docs_path}")
    assert os.path.exists(f"{docs_path}/index.html")
    assert os.path.exists(f"{docs_path}/_ad")
    assert os.path.exists(f"{docs_path}/_ad/index.html")

def test_docsource_write_tar(root_toc, webserver, tarfile):
    ds = root_toc.parent
    ds.get_contents(WebDriver(), "")
    ds.get_themes(WebDriver())
    ds.write_tar(tarfile)
    assert tarfile.getnames().sort() == [
        "Contents/Resources/Documents/index.html",
        "Contents/Resources/Documents/_ad/index.html",
        "Contents/Resources/Documents/adsprop/index.html",
        "Contents/Resources/Documents/adsprop/nf-adsprop-adspropcheckifwritable.html",
        "Contents/Resources/Documents/_themes_/file.css"
    ].sort()

def test_docset(docset, docsource):
    assert docset.title == "Windows Desktop Api"
    assert docset.identifier == "Win32k"
    assert docset.sources == [ docsource ]

def test_docset_get_contents(root_toc, webserver, html_ok):
    ds = root_toc.parent.parent
    ds.get_contents(WebDriver(), "")
    assert ds._css_files == [] # stored in sources
    assert ds._js_files == []
    assert ds._ico == b''

def test_docset_get_theme(root_toc, webserver, css_ok, bytes_ok):
    ds = root_toc.parent.parent
    ds.get_contents(WebDriver(), "")
    ds.get_themes(WebDriver())
    assert ds._css_files == [] # [(Path('Contents/Resources/Documents/_themes_/file.css'), css_ok)] # stored in sources
    assert ds._js_files == []
    assert ds._ico == bytes_ok

def test_docset_write_contents(root_toc, webserver, tmp_path):
    # docsource forces packaging paths
    ds = root_toc.parent.parent
    ds.get_contents(WebDriver(), "")
    ds.get_themes(WebDriver())
    ds.write_contents(tmp_path)
    docs_path = f"{tmp_path}/Contents/Resources/Documents"
    assert os.path.exists(f"{tmp_path}")
    assert os.path.exists(f"{tmp_path}/icon.png")
    assert os.path.exists(f"{tmp_path}/Contents/Info.plist")
    assert os.path.exists(f"{tmp_path}/Contents/Resources/docSet.dsidx")
    assert os.path.exists(f"{docs_path}")
    assert os.path.exists(f"{docs_path}/index.html")
    assert os.path.exists(f"{docs_path}/_ad")
    assert os.path.exists(f"{docs_path}/_ad/index.html")
    assert os.path.exists(f"{docs_path}/_themes_/file.css")

def test_docset_make_package(root_toc, webserver, tmp_path):
    ds = root_toc.parent.parent
    ds.get_contents(WebDriver(), "")
    ds.get_themes(WebDriver())
    ds.make_database(tmp_path)
    ds.make_package(tmp_path)
    with TarFile.open(f"{tmp_path}/Windows Desktop Api.docset.tar") as tf:
        assert tf.getnames().sort() == [
            "icon.png",
            "Contents/Info.plist",
            "Contents/Resources/docSet.dsidx",
            "Contents/Resources/Documents/index.html",
            "Contents/Resources/Documents/_ad/index.html",
            "Contents/Resources/Documents/adsprop/index.html",
            "Contents/Resources/Documents/adsprop/nf-adsprop-adspropcheckifwritable.html",
            "Contents/Resources/Documents/_themes_/file.css"
        ].sort()