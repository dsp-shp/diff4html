import os
import re
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import requests
import urllib3
from diff4html.html import get_tag, json2lxml, lxml2json, prepare
from lxml import etree, html

urllib3.disable_warnings()


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
    ConvertTest(x, f"https://{x}") for x in [
        "example.org",
        "2ch.hk",
        "muztorg.ru",
        "wikipedia.org",
        "dtf.ru",
        "jupyter-server.readthedocs.io",
    ]
], ids=lambda x: x.id)
def test_convert(case):
    _ = lambda x: html.tostring(x.xpath('//body')[0], encoding='unicode')

    r = requests.get(case.url, timeout=60)
    r.raise_for_status()

    #  TODO: move as warning function to diff4html.html module
    assert _(json2lxml(lxml2json(r.text))) == _(html.fromstring(prepare(r.text)))
