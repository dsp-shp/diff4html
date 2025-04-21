import json
import re
import typing as t
from dataclasses import dataclass, field
from functools import reduce
from pathlib import Path

import pytest
import requests
from lxml import html

from diff4html.diff import find
from diff4html.html import Struct, lxml2json


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


# check if elements of HtmlDict can be properly found
@pytest.mark.parametrize("case", [
    Test(x, f"https://{x.strip()}", None) for x in [
        "example.org",
        "2ch.hk     ",
        "ebay.com   ",
        "google.com ",
        "youtube.com",
    ]
], ids=lambda x: x.id)
def test_dict_find(case):
    """

    Recursively get all items of struct, pass them through find and compare the
    original content with found by find one.

    """
    r = requests.get(case.sub, timeout=60)
    r.raise_for_status()
    d = lxml2json(r.text)
    s = json.dumps(d, ensure_ascii=False)
    c = [0]

    def _recurse(
        e: t.Union[Struct, t.Any],
        parent: t.Optional[Struct] = None
    ) -> bool:
        c[0] = c[0] + 1
        if isinstance(e, dict):
            return reduce(
                lambda a, b: a and b,
                [_recurse(k, e) for k,v in e.items()]
            )

        if isinstance(e, list):
            return reduce(
                lambda a, b: a and b,
                [_recurse(i, e) for i,x in enumerate(e)]
            )

        if not isinstance(e, int) and not isinstance(e, str):
            raise TypeError()

        l: bool = True
        try:
            value = parent[e] # type: ignore
            if isinstance(value, dict):
                #  TODO: fix dict dump check in list parent
                l = (_recurse(json.dumps({e: value}, ensure_ascii=False), parent) if not isinstance(parent, list) else True) and _recurse(value, parent[e])
                return l
            if isinstance(value, list):
                l = _recurse(value, parent)
                return l
        except ValueError as exc:
            raise exc # reraise error on failed find
        except Exception:
            value = e

        start, length = find(d, parent or d, e)
        end = start + length

        value = value or "null"
        # cut start & end braces (unpack dump): {({a:1}), b:1}
        if isinstance(parent, dict) and len(parent) > 1 and re.match(r"\{.+\}", str(value)):
            value = value[1:-1]
        result = value == s[start:end]

        return l and (
            # skip check for root recursion node
            result if json.dumps(parent, ensure_ascii=False) != e else True
        )

    assert _recurse(d)
    print(f"- tested on {c[0]} inner elements")
