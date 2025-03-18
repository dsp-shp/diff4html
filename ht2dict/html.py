import json
import re
import typing as t

from lxml import html

Struct = t.Union[dict, list, tuple]


def repl_spaces(s: str) -> str:
    """ Replace whitespaces

    Function used to replace all whitespaces (and '\xa0' too) in HTML string by
    Braille Blank (U+2800). Otherwise there will be troubles with comparing
    tokens in htmldiff function.
    
    """
    s = re.sub(r"\n[\n|\t| ]+", "", s)
    for x in re.finditer(r"\>([^\<]+)\<\/", s):
        s = s[:x.span()[0]] +\
            x.group().replace(" ", " ").replace("\xa0", " ") +\
            s[x.span()[1]:]
    return s


def get_tag(
    e: html.HtmlElement,
    f: t.Callable = lambda x: len(x) <= 100
) -> t.Optional[str]:
    """ Get tag string

    Construct full tag str with all tag' parameters from lxml.HtmlElement &
    filter them by some func. Use backticks for building parameters' part.

    Args:
        e: some HTML tag
        f: func applied in filter

    Returns:
        str | None: tag string or nothing

    """
    #  TODO: move isinstance check to pydantic check
    return (
        e.tag + ' ' + " ".join(f"{k}=`{v}`" for k,v in e.attrib.items() if f(v))
        #  WARNING: possibly not use filter because of data loss
    ).strip(' ') if isinstance(e, html.HtmlElement) else None


def lxml2json(
    e: html.HtmlElement,
    ignore: set = {'defs', 'filter', 'g', 'path', 'script', 'symbol'},
) -> dict:
    """ Convert lxml HtmlElement tree into JSON 

    Args:
        e: root of some HTML tree
        ignore: set of tags to ignore when forming JSON

    Returns:
        dict: JSON formed from tree
    
    """
    def _recurse(e: html.HtmlElement) -> dict:
        e_data: Struct
        e_name = get_tag(e)

        if e.tag in ignore or isinstance(e, html.HtmlComment):
            return {}

        if not (children := e.getchildren()):
            return {e_name: e.text}

        # if all inside tags are unique – it's a single dict, otherwise – list
        if len({
            get_tag(x) for x in children if x.tag not in ignore and not isinstance(
                x, html.HtmlComment
            )
        }) == len([
            x for x in children if x.tag not in ignore and not isinstance(
                x, html.HtmlComment
            )
        ]):
        # if len({get_tag(x) for x in children}) == len(children):
            e_data = {}
            for x in children:
                e_data = {**e_data, **_recurse(x)}
        else:
            e_data = [_recurse(x) for x in e.iterchildren()]

        return {e_name: e_data}

    return _recurse(e)


def json2lxml(d: t.Union[str, Struct]) -> html.HtmlElement:
    """ Convert JSON into lxml HtmlElement tree
    
    Args:
        d: some JSON in dict or serialized form

    Returns:
        lxml.html.HtmlElement: root of HTML tree formed
    
    """
    def _recurse(data: t.Any) -> str:
        if isinstance(data, list):
            _data = [("", x, "") for x in data]
        elif isinstance(data, dict):
            _data = [(f"<{k}>", v, f"</{k.split(' ', 1)[0]}>") for k,v in data.items()]
        else:
            return str(data)

        return "".join(l + _recurse(x) + r for l, x, r in _data)

    # if given dict - serialize it in str dump first
    s: str = json.dumps(d, ensure_ascii=False) if isinstance(d, Struct) else d

    # return back all doublequotes (were replaced with backtick)
    for x in re.finditer(r'=(\`.+\`)', s):
        s = s.replace(x.group(), x.group().replace('`', '\\"'))

    #  TODO: replace whitespaces on Braile Blank maybe?

    return html.fromstring(_recurse(json.loads(s)))
