

import pytest
import responses
from pathlib import Path
from tarfile import TarFile

from msdocs_to_dash.toc import Toc, Branch, Child, Metadata
from msdocs_to_dash.docset import DocSource, DocSet

def __join__(txt):
    rst = ""
    for line in txt.splitlines():
        rst += line.strip()
    return rst

## Toc module
@pytest.fixture
def toc_uri(): return "https://learn.microsoft.com/"

@pytest.fixture
def base_toc_path(): return "windows/win32/api"

@pytest.fixture
def base_toc_json():
    return __join__('''
    { "items": [
        {"href":"_input_touchinjection/","toc_title":"Touch Injection"},
        {"href":"_ad/","toc_title":"Active Directory Domain Services",
        "children": [
            {"href":"../adsprop/","toc_title":"Overview"},
            {"href":"/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"}
        ]}
    ]}
    ''')

@pytest.fixture
def base_toc(docsource, base_toc_json):
    return Toc.from_json(base_toc_json, docsource)

## Docset module

@pytest.fixture
def docsource(base_toc_path):
    return DocSource("Win32k", base_toc_path)

@pytest.fixture
def docset(docsource):
    return DocSet("Windows Desktop Api", "Win32k", docsource)


## for complex tests
@pytest.fixture
def root_json():
   return __join__('''
        {
            "items":[
                {
                    "toc_title":"Windows Desktop Technologies",
                    "href":"./",
                    "children":[
                        {
                            "toc_title":"Headers",
                            "children":[
                                {"href":"_ad/","toc_title":"Active Directory Domain Services"}
                            ]
                        }
                    ]
                }
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
@pytest.fixture
def root_toc(docset, root_json):
    ds = docset.sources[0]
    toc = Toc.from_json(root_json, ds)
    return toc

@pytest.fixture
def ad_json():
    return __join__('''
        {
            "items":[
                {
                    "children":[
                        {
                            "children":[
                                {"href":"../adsprop/","toc_title":"Overview"},
                                {"href":"../adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"}
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
@pytest.fixture
def ad_toc(root_toc, ad_json):
    # being nested and relative hrefs these need to call up and mutate paths
    parent = root_toc.items[0].children[0].children[0] # _ad child
    toc = Toc.from_json(ad_json, parent)
    return toc

@pytest.fixture
def adsprop_json():
    return __join__('''
        {
            "items":[
                {
                    "children":[
                        {"href":"./","toc_title":"Overview"},
                        {"href":"/windows/win32/api/adsprop/nf-adsprop-adspropcheckifwritable","toc_title":"ADsPropCheckIfWritable function"}
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
@pytest.fixture
def adsprop_toc(ad_toc, adsprop_json):
    parent = ad_toc.items[0].children[0].children[0] # overview child
    toc = Toc.from_json(adsprop_json, parent)
    return toc

@pytest.fixture
def html_ok():
    return "<html>\n <head>\n  <link rel=\"stylesheet\" href=\"/test/blah/file.css\"/>\n  </head><body>\n  exists\n </body>\n</html>"
@pytest.fixture
def html_ok_rewrite():
    return "<html>\n <head>\n  <a class=\"dashAnchor\" name=\"//apple_ref/cpp/Category/Active%20Directory%20Domain%20Services\">\n  </a>\n  <link href=\"/_themes_/file.css\" rel=\"stylesheet\"/>\n </head>\n <body>\n  exists\n </body>\n</html>"
@pytest.fixture
def bytes_ok():
    return b'png\0'
@pytest.fixture
def css_ok():
    return ".body: 10px;"

@pytest.fixture
def webserver(root_json, ad_json, adsprop_json, html_ok, bytes_ok, css_ok):
    domain = "https://learn.microsoft.com"
    url = f"{domain}/en-us/windows/win32/api"
    theme = f"{domain}/_themes/docs.theme/master/en-us/_themes/styles"
    with responses.RequestsMock(assert_all_requests_are_fired=False) as r:
        # icon
        r.add(responses.GET, f"{domain}/media/logos/logo-ms-social.png", body=bytes_ok)
        # general html responses
        for entry in ["", "_ad/", "adsprop/", "adsprop/nf-adsprop-adspropcheckifwritable"]:
            r.add(responses.GET, f'{url}/{entry}', body=html_ok)
        # toc/json responses
        r.add(responses.GET, f'{url}/toc.json', body=root_json)
        r.add(responses.GET, f'{url}/_ad/toc.json', body=ad_json)
        r.add(responses.GET, f'{url}/adsprop/toc.json', body=adsprop_json)
        # extra css/js
        r.add(responses.GET, f'{domain}/test/blah/file.css', body=css_ok)
        yield r

@pytest.fixture
def tarfile(tmp_path):
    tar_path = Path(tmp_path).joinpath(f"test.tar")
    with TarFile.open(tar_path, "w:gz") as tar:
        yield tar