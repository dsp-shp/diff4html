import json
import re
import typing as t
from collections import UserDict, UserList
from textwrap import shorten
from uuid import uuid4

from diff4html.html import json2lxml, lxml2json, prepare
from lxml import html


class HtmlDiff(UserList):
    """ HtmlDiff

    HtmlDiff, in the context of page 2 - page 1, is a list of changes in the 
    form of (s, e, t), where s and e are the start and end indices pointing to 
    the differing element in page 1, and t is the content of the corresponding 
    differing element in page 2.

    """

    data: list[tuple[int, int, str, str]]
    """ Data structure """

    _sub_hash: int
    """ Subtrahend hash sum to validate further appliement """

    def __init__(self, *args, sub) -> None:
        self._sub_hash = hash(sub)
        super().__init__(*args)

    def __str__(self) -> str:
        """ Serialize to JSON dump """
        return json.dumps(self.data, ensure_ascii=False)

    def __repr__(self) -> str:
        """ Print in JSON format"""
        return "%s([\n%s\n])" % (
            self.__class__.__name__,
            ',\n'.join(['    %s:%s: %s' % (
                x, y, (json.dumps(z, ensure_ascii=False) if z else None)
            ) for x,y,z in self.data
        ]))


class HtmlDict(UserDict, object):
    """ HtmlDict

    A representation of HTML tree built on native Python dict & list data types.

    """

    data: dict
    """ Data structure of UserDict """

    _source: t.Optional[str]
    """ Source string used to init object """

    def __init__(self, *args, **kwargs):
        #  TODO: add xpath kwarg handling
        if len(args) == 1 and isinstance(args[0], str):
            self._source = args[0]
            args, kwargs = (), lxml2json(
                html.fromstring(prepare(self._source))
            )
        else:
            self._source = None
        super().__init__(*args, **kwargs)

    def __eq__(self, other: t.Self) -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError(
                "unsupported operand type(s) for -: 'HtmlDict' and '%s'" % (
                    other.__class__.__name__
                )
            )
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        """ Get hash sum """
        return str.__hash__(str(self))

    def __str__(self) -> str:
        """ Serialize to JSON dump """
        return json.dumps(self.data, ensure_ascii=False)

    def __repr__(self) -> str:
        """ Print object """
        return "%s(%s)" % (
            self.__class__.__name__,
            shorten(json.dumps(self.data, ensure_ascii=False), width=500)
        )

    def __add__(self, other: HtmlDiff) -> t.Self:
        """ Apply HtmlDiff delta to HtmlDict """
        if not isinstance(other, HtmlDiff):
            raise TypeError(
                "unsupported operand type(s) for +: 'HtmlDict' and '%s'" % (
                    other.__class__.__name__
                )
            )
        if hash(self) != other._sub_hash:
            raise ValueError(
                "wrong snapshot used for applying diff"
            )
        return self.__class__(**json.loads(apply_diff(self, other)))

    def __sub__(self, other: t.Self) -> HtmlDiff:
        """ Get HtmlDiff delta """
        if not isinstance(other, self.__class__):
            raise TypeError(
                "unsupported operand type(s) for -: 'HtmlDict' and '%s'" % (
                    other.__class__.__name__
                )
            )
        return diff(self, other)

    def to_lxml(self) -> html.HtmlElement:
        return json2lxml(self.data)


def find(
    e: t.Any,
    end_e: t.Any,
    end_i: t.Optional[t.Any] = None
) -> tuple[int, int]:
    """ Find the element position in structure dump

    Find start & end string indexes of the desired element in a structure dump
    with the whole dict object, a parent node and ...
    - a key, if the current node is a dictionary and should return a value
    - an element num, if the current node is a list and should return an element
    - the whole node dump, if the entire node should be returned
 
    """

    sep: str = str(uuid4())
    """ Random separator used to cut off the right side to search for the index """

    def _recurse(e: t.Any) -> tuple[t.Any, int]:
        """ Process recursively 

        """
        found: bool = False
        """ Flag to indicate that desired node has been found """
        items: list = []
        """ ... """
        length: t.Optional[int] = None
        """ Length of found element """
        i: int = 0

        if isinstance(e, list):
            while i <= len(e) - 1 and not found:
                if e == end_e and i == end_i:
                    found = True
                    length = len(json.dumps(e[i], ensure_ascii=False))
                    items.append(sep)
                else:
                    _e, _length = _recurse(e[i])
                    length = length or _length
                    items.append(_e)
                i += 1
            return items, length

        if isinstance(e, dict):
            keys = [*e.keys()]
            while i <= len(keys) - 1 and not found:
                # if keys differ
                if e is end_e and end_i and keys[i] == end_i:
                    found = True
                    if end_i and keys[i] == end_i: # if diff in key already
                        length = len(json.dumps(e[keys[i]], ensure_ascii=False))
                        items.append([keys[i], sep])
                # if have to look at the value first (string one)
                elif e[keys[i]] is end_e and end_i is None:
                    found = True
                    length = len(json.dumps(e[keys[i]], ensure_ascii=False))
                    items.append([keys[i], sep])
                elif e is end_e and end_i == json.dumps({keys[i]: e[keys[i]]}, ensure_ascii=False):
                    found = True
                    length = len(end_i[1:-1])
                    items.append([sep, None])
                # else check values
                else:
                    _e, _length = _recurse(e[keys[i]])
                    length = length or _length
                    items.append((keys[i], _e))
                i += 1
            return dict(items), length

        return str(e) if e else None, length

    s, length = _recurse(e)
    offset = len(json.dumps(s, ensure_ascii=False).split(f'"{sep}"', 1)[0].rstrip('}]'))

    return offset, length


def diff(
    e1: t.Union[dict, HtmlDict],
    e2: t.Union[dict, HtmlDict]
) -> HtmlDiff:
    """ Get changes between two HTML dicts

    Returns:
        HtmlDiff: difference object  
    
    """

    d: list[tuple[int, int, str, str]] = []
    """ List to accumulate found changes here """

    def _recurse(e1: t.Any, e2: t.Any, path: list = []) -> None:
        """ Process recursively

        Parameters:
            e1 (t.Any): minuend
            e2 (t.Any): subtrahend
            path (list): list to accumulate path parts till specific node
        
        """

        if e1 is None and e2 is None:
            return

        # Save the dict on a recursion root step
        if path is None:
            if not isinstance(e2, dict) or not e2:
                raise Exception('Dict structure with at least one key expected')
            path = [e2, list(e2)[0]]

        # If e1 & e2 types differ then this is a final diff
        if type(e1) != type(e2):
            pass

        # If compare two lists
        elif type(e1) == type(e2) and isinstance(e1, list):
            for i, e in enumerate(e1):
                _e2 = None if not i in range(len(e2)) else e2[i]
                _recurse(e, _e2, path=[*path, _e2 or path[-2][path[-1]], i])

            if len(e2) > len(e1):
                for i, e in enumerate(e2[len(e1):]):
                    _recurse(None, e, path=[*path, e2, len(e1)+i])
            return

        # If compare two dicts
        elif type(e1) == type(e2) and isinstance(e1, dict):
            _keys = []
            for i,k,v in [[i,*x] for i,x in enumerate((e1 or {}).items())]:
                try:
                    _k = [*e2.keys()][i]
                except IndexError:
                    _k = None

                if not _k: # if the key is missing in prev version
                    _recurse({k:v}, None, path=[*path])
                elif k != _k: # if keys differ
                    _recurse({k:v}, _k, path=[*path, e2, json.dumps({_k:e2[_k]}, ensure_ascii=False)])
                    _keys.append(_k)
                else:
                    _recurse(v, e2[k], path=[*path, e2, k])

            _e2_items = {k:v for k,v in e2.items() if k not in {*e1, *_keys}}
            for k,v in _e2_items.items():
                _recurse(None, v or '', path=[*path, e2, json.dumps({k:v}, ensure_ascii=False)])
            return

        # If compare two strings
        else:
            if str(e1) == str(e2):
                return

        if path:
            try:
                offset, length = find(path[0], *path[-2:])
                _s = json.dumps(path[0], ensure_ascii=False)[offset:offset+length]
            except: #  TODO: fix bare except
                pass

            _d = ()
            e1_dump = json.dumps(e1, ensure_ascii=False) if e1 else None

            #  TODO: more clear comments
            # If was added
            if e1 is not None and e2 is None:
                # For lists on add should look on prev elem
                if isinstance(path[-2], list):
                    offset, length = find(path[0], path[-2], len(path[-2])-1)
                elif isinstance(path[-2], dict):
                    try:
                        _is_dict = isinstance(json.loads(path[-1]), dict)
                    except json.JSONDecodeError:
                        _is_dict = False
                    if not _is_dict:
                        __e = path[-2][path[-1]]
                        path += [__e, [*__e][-1]]
                        offset, length = find(path[0], *path[-2:])
                _d = (offset+length, offset+length, e1_dump)

            # If was replaced
            elif e1 is not None and e2 is not None:
                if isinstance(path[-2], dict):
                    if re.match(r'\{\"[^\"]+\":.+', e1_dump):
                        e1_dump = e1_dump[1:-1]
                _d = (offset, offset+length, e1_dump)

            # If was removed
            elif e1 is None and e2 is not None:
                _d = (offset, offset+length, None)

            if _d:
                d.append(_d)

            return

    _recurse(
        e1.data if isinstance(e1, HtmlDict) else e1,
        e2.data if isinstance(e2, HtmlDict) else e2,
    )
    return HtmlDiff(d, sub=e2)


def apply_diff(html_or_str: t.Union[str, HtmlDict], changes: HtmlDiff) -> str:
    """ Apply changes

    Restore page snapshot with source code & delta.

    """
    s: str = str(html_or_str)

    # check if specific change is in dict scope - inside
    _in_dict: t.Callable = lambda x: _in_dict(_) if (
        _ := re.sub(r'\{[^\}\{]+\}', '', x)
    ) != x else [*re.findall(
        r'[\}|\(|\)|\]|\ \,]\}+',
        x.replace(' ', '').replace(',', '')
    ), ''][0].startswith('}')

    for i, j, res in changes.data[::-1]:
        # when removed in update
        if (s[:i].endswith(', ') or s[i:].startswith(', ')) and res is None:
            i -= 2
        # if need to trim ", " from left (when added in update)
        if i == j:
            # if cur is a dict unpacked in parent structure - trim curly braces
            try:
                if isinstance(json.loads(res), dict) and _in_dict(s[i:]):
                    res = res[1:-1]
            except json.JSONDecodeError:
                pass
            res = ', ' + res
        s = s[:i] + (res or '') + s[j:]

    return s
