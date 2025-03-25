import typing as t
from dataclasses import dataclass, field

import pytest
import requests
from diff4html.html import get_tag, validate
from lxml import html


@dataclass
class Test:
    """ Test case instance """
    id: str
    sub: str
    res: t.Optional[str]
    exc_type: t.Optional[type[Exception]] = None
    __test__ = False # skip pytest inspect which leads to warnings

    def __post_init__(self):
        self.id = self.id


# check if tag can be properly parsed to json
@pytest.mark.parametrize("case", [
    Test(x, f"<html>{y}</html>", z) for x,y,z in [(
        "basic_empty",
        '<div></div>',
        "div"
    ), (
        "basic_attrs",
        '<div class="1">2</div>3',
        "div class=`1` __text__=`2` __tail__=`3`"
    ), (
        "empty_attrs",
        '<div class="" id="">2</div>3',
        "div class id __text__=`2` __tail__=`3`"
    ), (
        "space_attrs",
        '<div class="1"> </div> ',
        "div class=`1` __text__=` ` __tail__=` `"
    ), (
        "quote_attrs",
        '<div class="\'1\'">"2"</div>`3`', 
        "div class=`&apos;1&apos;` __text__=`&quot;2&quot;` __tail__=`&#x60;3&#x60;`"
    )]
], ids=lambda x: x.id)
def test_tag_parse(case):
    assert get_tag(html.fromstring(case.sub).xpath('//div')[0]) == case.res


# check if source code can be properly converted to json & backwards
@pytest.mark.parametrize("case", [
    Test(x, f"https://{x.strip()}", None) for x in [
        "example.org",
        "4chan.org  ",
        "ebay.com   ",
        "google.com ",
        "youtube.com",
    ]
], ids=lambda x: x.id)
def test_html_cast(case):
    r = requests.get(case.sub, timeout=60)
    r.raise_for_status()
    assert validate(r.text)
