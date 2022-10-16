#!env python3

import pytest
from pathlib import Path
from msdocs_to_dash.toc import Toc
from msdocs_to_dash.docset import DocSource, DocSet

def test_nested_toc(ad_toc):
    assert ad_toc.metadata.title == "Win32 apps"
    assert ad_toc.folder("") == "_ad/"

def test_nested_branch(ad_toc):
    assert ad_toc.items[0].toc_title == "Active Directory Domain Services"
    assert ad_toc.items[0].folder("") == "_ad/"
    #
    assert ad_toc.items[0].children[0].toc_title == "Adsprop.h"
    assert ad_toc.items[0].children[0].folder("") == "_ad/"

def test_nested_relative_child(ad_toc):
    assert ad_toc.items[0].children[0].children[0].toc_title == "Overview"
    assert ad_toc.items[0].children[0].children[0].folder("") == "adsprop/"
    assert ad_toc.items[0].children[0].children[0].file("") == Path("adsprop/index.html")
    assert ad_toc.items[0].children[0].children[0].isfile() == False
    #
    assert ad_toc.items[0].children[0].children[1].toc_title == "ADsPropCheckIfWritable function"
    assert ad_toc.items[0].children[0].children[1].folder("") == "adsprop/"
    assert ad_toc.items[0].children[0].children[1].file("") == Path("adsprop/nf-adsprop-adspropcheckifwritable.html")
    assert ad_toc.items[0].children[0].children[1].isfile() == True

def test_nested_absolute_child(adsprop_toc):
    assert adsprop_toc.items[0].toc_title == "Adsprop.h"
    assert adsprop_toc.items[0].folder("") == "adsprop/"
    assert adsprop_toc.items[0].isfile() == False
    assert adsprop_toc.items[0].file("") == Path("adsprop/index.html")
    #
    assert adsprop_toc.items[0].children[1].toc_title == "ADsPropCheckIfWritable function"
    assert adsprop_toc.items[0].children[1].folder("") == "adsprop/"
    assert adsprop_toc.items[0].children[1].file("") == Path("adsprop/nf-adsprop-adspropcheckifwritable.html")
    assert adsprop_toc.items[0].children[1].isfile() == True