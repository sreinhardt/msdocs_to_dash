#!env python3

import logging
import pytest
import os
from pathlib import Path

from msdocs_to_dash.webdriver import WebDriver
from msdocs_to_dash.docset import DocSource
from msdocs_to_dash.toc import Toc, Branch, Child, Metadata

def test_toc_ingest(base_toc_json, base_toc_path):
    ds = DocSource("Win32k", base_toc_path)
    toc = Toc.from_json(base_toc_json, ds)
    assert len(toc.items) == 2

def test_toc_child(base_toc, tmp_path):
    branch = base_toc.items[0]
    folder = branch.folder(tmp_path)
    assert folder == f"{tmp_path}/_input_touchinjection/"
    assert branch.file(tmp_path) == Path(f"{tmp_path}/_input_touchinjection/index.html")
    assert branch.url() == "https://learn.microsoft.com/en-us/windows/win32/api/_input_touchinjection/"
    assert branch.toc() == "https://learn.microsoft.com/en-us/windows/win32/api/_input_touchinjection/toc.json"

def test_toc_branch(base_toc, tmp_path):
    branch = base_toc.items[1]
    folder = branch.folder(tmp_path)
    assert folder == f"{tmp_path}/_ad/"
    assert branch.file(tmp_path) == Path(f"{tmp_path}/_ad/index.html")
    assert branch.url() == "https://learn.microsoft.com/en-us/windows/win32/api/_ad/"
    assert branch.toc() == None # because of children, no toc should be requested

def test_toc_child_relative(base_toc, tmp_path):
    child = base_toc.items[1].children[0]
    assert child.folder(tmp_path) == f"{tmp_path}/adsprop/" # remove parent _ad/ due to ../
    assert child.file(tmp_path) == Path(f"{tmp_path}/adsprop/index.html")
    assert child.url() == "https://learn.microsoft.com/en-us/windows/win32/api/adsprop/"
    assert child.toc() == "https://learn.microsoft.com/en-us/windows/win32/api/adsprop/toc.json"

def test_toc_child_absolute(base_toc, tmp_path):
    child = base_toc.items[1].children[1]
    assert child.folder(tmp_path) == f"{tmp_path}/adsprop/"
    assert child.file(tmp_path) == Path(f"{tmp_path}/adsprop/nf-adsprop-adspropcheckifwritable.html")
    assert child.url() == "https://learn.microsoft.com/en-us/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable"
    assert child.toc() == None # children dont generate tocs

def test_get_contents(root_toc, webserver, html_ok_rewrite):
    urls = root_toc.get_contents(WebDriver(), "")
    ad_toc = root_toc.items[0].children[0].children[0]
    assert urls == [("windows/win32/api/_ad/", ad_toc)]
    assert ad_toc.contents == html_ok_rewrite.encode('utf-8')

def test_write(root_toc, webserver, tmp_path):
    urls = root_toc.get_contents(WebDriver(), "")
    root_toc.write(tmp_path)
    assert os.path.exists(f"{tmp_path}")
    assert os.path.exists(f"{tmp_path}/_ad")
    assert os.path.exists(f"{tmp_path}/_ad/index.html")

def test_write_tar(root_toc, webserver, tarfile):
    urls = root_toc.get_contents(WebDriver(), "")
    root_toc.write_tar(tarfile)
    assert tarfile.getnames() == ["Contents/Resources/Documents/_ad/index.html"]