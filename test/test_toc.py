#!env python3

import logging
import pytest
from pathlib import Path

from msdocs_to_dash.docset import DocSource
from msdocs_to_dash.toc import Toc, Branch, Child, Metadata
from msdocs_to_dash.downloader import DocSource

@pytest.fixture
def tmp_dir(): return "/tmp"
@pytest.fixture
def toc_uri(): return "https://learn.microsoft.com/"
@pytest.fixture
def toc_path(): return "windows/win32/api"
@pytest.fixture
def toc_json():
    return '{ "items": [ {"href":"_input_touchinjection/","toc_title":"Touch Injection"}, {"href":"_ad/","toc_title":"Active Directory Domain Services", "children": [ {"href":"../adsprop/","toc_title":"Overview"}, {"href":"/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"} ]} ], "metadata": { "author":"GrantMeStrength", "breadcrumb_path":"/windows/desktop/api/breadcrumb/toc.json", "extendBreadcrumb":true, "feedback_system":"none", "ms.author":"jken", "ms.prod":"desktop", "ms.technology":"sdk-api-reference", "ms.topic":"language-reference", "open_to_public_contributors":true, "pdf_absolute_path":"/windows/win32/api/opbuildpdf/toc.pdf", "searchScope":["Windows","Desktop"], "titleSuffix":"Win32 apps", "uhfHeaderId":"MSDocsHeader-WinDevCenter" } }'
'''
{ "items": [
    {"href":"_input_touchinjection/","toc_title":"Touch Injection"},
    {"href":"_ad/","toc_title":"Active Directory Domain Services",
    "children": [
        {"href":"../adsprop/","toc_title":"Overview"},
        {"href":"/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"}
    ]}
]}
'''
@pytest.fixture
def toc(toc_path, toc_json):
    ds = DocSource("Win32k", toc_path)
    return Toc.from_json(toc_json, ds)

def test_toc_ingest(toc_json, toc_path):
    ds = DocSource("Win32k", toc_path)
    toc = Toc.from_json(toc_json, ds)
    assert len(toc.items) == 2

def test_toc_child(toc, tmp_dir):
    branch = toc.items[0]
    folder = branch.folder(tmp_dir)
    assert folder == "/tmp/_input_touchinjection/"
    assert branch.file(tmp_dir) == Path("/tmp/_input_touchinjection/index.html")
    assert branch.url() == "https://learn.microsoft.com/en-us/windows/win32/api/_input_touchinjection/"
    assert branch.toc() == "https://learn.microsoft.com/en-us/windows/win32/api/_input_touchinjection/toc.json"

def test_toc_branch(toc, tmp_dir):
    branch = toc.items[1]
    folder = branch.folder(tmp_dir)
    assert folder == "/tmp/_ad/"
    assert branch.file(tmp_dir) == Path("/tmp/_ad/index.html")
    assert branch.url() == "https://learn.microsoft.com/en-us/windows/win32/api/_ad/"
    assert branch.toc() == None # because of children, no toc should be requested

def test_toc_child_relative(toc, tmp_dir):
    child = toc.items[1].children[0]
    assert child.folder(tmp_dir) == "/tmp/adsprop/" # remove parent _ad/ due to ../
    assert child.file(tmp_dir) == Path("/tmp/adsprop/index.html")
    assert child.url() == "https://learn.microsoft.com/en-us/windows/win32/api/adsprop/"
    assert child.toc() == "https://learn.microsoft.com/en-us/windows/win32/api/adsprop/toc.json"

def test_toc_child_absolute(toc, tmp_dir):
    child = toc.items[1].children[1]
    assert child.folder(tmp_dir) == "/tmp/adsprop/"
    assert child.file(tmp_dir) == Path("/tmp/adsprop/nf-adsprop-adspropcheckifwritable.html")
    assert child.url() == "https://learn.microsoft.com/en-us/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable"
    assert child.toc() == None # children dont generate tocs



