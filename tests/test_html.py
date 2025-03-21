import os
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import requests
from diff4html.html import get_tag, json2lxml, lxml2json, prepare
from lxml import etree, html


@dataclass
class ConvertTest:
    """ lxml2json & json2lxml functions' test case """
    id: str
    url: str
    exc_type: t.Optional[type[Exception]] = None

    def __post_init__(self):
        self.id = self.id


# Check if source code can be properly converted to json & backwards
@pytest.mark.parametrize("case", [
    ConvertTest(x, x) for x in [
            "https://example.org",
            "https://2ch.hk/b/res/317830044.html"
        ]
    ], ids=lambda x: x.id
)
def test_convert(case):
    r = requests.get(case.url, verify=False)
    if not r.ok:
        raise Exception("cannot get HTML source code")

    l_text = html.tostring(
        json2lxml(lxml2json(r.text)).xpath('//body')[0],
        encoding='unicode'
    )

    c_text = prepare(html.tostring(
        html.fromstring(prepare(r.text)).xpath('//body')[0],
        encoding='unicode'
    ))

    assert l_text == c_text
