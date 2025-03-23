import typing as t
from dataclasses import dataclass, field

import pytest
import requests
from diff4html.html import validate


@dataclass
class ConvertTest:
    """ lxml2json & json2lxml functions' test case """
    id: str
    url: str
    exc_type: t.Optional[type[Exception]] = None

    def __post_init__(self):
        self.id = self.id


# check if source code can be properly converted to json & backwards
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
    r = requests.get(case.url, timeout=60)
    r.raise_for_status()
    assert validate(r.text)
