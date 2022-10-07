#!env python3

import pytest
from pathlib import Path
from msdocs_to_dash.toc import Toc
from msdocs_to_dash.docset import DocSource, DocSet

def __join__(txt):
    rst = ""
    for line in txt.splitlines():
        rst += line.strip()
    return rst

@pytest.fixture
def docsource():
    return DocSource("Win32k", "windows/win32/api")

@pytest.fixture
def docset(docsource):
    return DocSet("Windows Desktop Api", "Win32k", docsource)

@pytest.fixture
def root_toc(docsource):
    json = __join__('''
{
    "items":[
        {"children":[
            {"children":[
                {"href":"_ad/","toc_title":"Active Directory Domain Services"},
                {"href":"_adam/","toc_title":"Active Directory Lightweight Directory Services"},
                {"href":"_rm/","toc_title":"Active Directory Rights Management Services SDK"},
                {"href":"_adsi/","toc_title":"Active Directory Service Interfaces"},
                {"href":"_activity_coordinator/","toc_title":"Activity Coordinator"},
                {"href":"_alljoyn/","toc_title":"AllJoyn API"},
                {"href":"_amsi/","toc_title":"Antimalware Scan Interface"}
            ],"toc_title":"Headers"}
        ],"href":"./","toc_title":"Windows Desktop Technologies"}
    ],"metadata":{
        "author":"GrantMeStrength",
        "breadcrumb_path":"/windows/desktop/api/breadcrumb/toc.json",
        "extendBreadcrumb":true,
        "feedback_system":"none",
        "ms.author":"jken",
        "ms.prod":"desktop",
        "ms.technology":"sdk-api-reference",
        "ms.topic":"language-reference",
        "open_to_public_contributors":true,
        "pdf_absolute_path":"/windows/win32/api/opbuildpdf/toc.pdf",
        "searchScope":["Windows","Desktop"],
        "titleSuffix":"Win32 apps",
        "uhfHeaderId":"MSDocsHeader-WinDevCenter"
    }
}
''')
    toc = Toc.from_json(json, docsource)
    return toc

@pytest.fixture
def ad_toc(root_toc):
    # being nested and relative hrefs these need to call up and mutate paths
    json = __join__('''
{
    "items":[
        {
            "children":[
                {
                    "children":[
                        {"href":"../adsprop/","toc_title":"Overview"},
                        {"href":"../adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"},
                        {"href":"../adsprop/nf-adsprop-adspropcreatenotifyobj","toc_title":"ADsPropCreateNotifyObj function"},
                        {"href":"../adsprop/ns-adsprop-adsproperror","toc_title":"ADSPROPERROR structure"},
                        {"href":"../adsprop/nf-adsprop-adspropgetinitinfo","toc_title":"ADsPropGetInitInfo function"},
                        {"href":"../adsprop/ns-adsprop-adspropinitparams","toc_title":"ADSPROPINITPARAMS structure"}
                    ],
                    "toc_title": "Adsprop.h"
                }
            ], 
            "href":"./", "toc_title":"Active Directory Domain Services"
        }
    ],
    "metadata":{
        "author":"GrantMeStrength",
        "breadcrumb_path":"/windows/desktop/api/breadcrumb/toc.json",
        "extendBreadcrumb":true,
        "feedback_system":"none",
        "ms.author":"jken",
        "ms.prod":"desktop",
        "ms.technology":"sdk-api-reference",
        "ms.topic":"language-reference",
        "open_to_public_contributors":true,
        "pdf_absolute_path":"/windows/win32/api/opbuildpdf/_ad/toc.pdf",
        "searchScope":["Windows","Desktop"],
        "titleSuffix":"Win32 apps",
        "uhfHeaderId":"MSDocsHeader-WinDevCenter"
    }
}
''')
    parent = root_toc.items[0].children[0].children[0] # _ad child
    toc = Toc.from_json(json, parent)
    return toc

@pytest.fixture
def adsprop_toc(ad_toc):
    json = __join__('''
{
    "items":[
        {
            "children":[
                {"href":"./","toc_title":"Overview"},
                {"href":"/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"},
                {"href":"/windows/win32/api/adsprop/nf-adsprop-adspropcreatenotifyobj","toc_title":"ADsPropCreateNotifyObj function"},
                {"href":"/windows/win32/api/adsprop/ns-adsprop-adsproperror","toc_title":"ADSPROPERROR structure"}
            ],
            "toc_title":"Adsprop.h"
        }
    ],
    "metadata":{
        "author":"alvinashcraft",
        "breadcrumb_path":"/windows/desktop/api/breadcrumb/toc.json",
        "extendBreadcrumb":true,
        "feedback_system":"none",
        "ms.author":"aashcraft",
        "ms.prod":"desktop",
        "ms.technology":"sdk-api-reference",
        "ms.topic":"language-reference",
        "open_to_public_contributors":true,
        "pdf_absolute_path":"/windows/win32/api/opbuildpdf/adsprop/toc.pdf",
        "searchScope":["Windows","Desktop"],
        "titleSuffix":"Win32 apps",
        "uhfHeaderId":"MSDocsHeader-WinDevCenter"
    }
}
''')
    parent = ad_toc.items[0].children[0].children[0] # overview child
    toc = Toc.from_json(json, parent)
    return toc


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