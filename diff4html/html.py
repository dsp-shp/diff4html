import json
import re
import typing as t
from enum import Enum

from lxml import etree, html

Struct = t.Union[dict, list, tuple]


def prepare(s: str) -> str:
    """ Prepare HMTL source string
    
    Remove all new lines, empty attribute values & redundant spaces and replace
    all whitespaces (and '\xa0' too) in HTML string with Braille Blank (U+2800). 
    Otherwise there will be troubles with comparing tokens in htmldiff function,
    which actually is not used anymore, lol.
    
    """
    # remove new lines, empty attribute values & gaps between tags
    s = s.replace('\n', '')
    s = s.replace('=""', '')
    s = re.sub(re.compile(r"\>[\ ]*\<"), "><", s)
    # replace \xa0
    for x in re.finditer(r"\>([^\<]+)\<", s):
        y = x.group()
        y = re.sub(re.compile(r"\>[\ ]*\<"), "><", y)
        y = y.replace(" ", " ").replace("\xa0", " ")
        s = s[:x.span()[0]] + y + s[x.span()[1]:]

    return html.tostring(
        html.fromstring(s, parser=etree.HTMLParser(remove_comments=True)),
        encoding='unicode'
    )


def get_tag(
    e: html.HtmlElement,
    f: t.Callable = lambda x: True
) -> t.Optional[str]:
    """ Get tag string

    Construct full tag str with all tag' parameters from lxml.HtmlElement &
    filter them by some func. Use backticks for attributes' values, underscores
    for special prefix, text & tail parameters & replace quotes, apostrophe and
    backticks inside values with HTML codes.

    """
    attrs: list[str] = []
    for k,v in {
        **e.attrib,
        "__prefix__": e.prefix or "", 
        "__text__": e.text or "", 
        "__tail__": e.tail or "",
    }.items():
        if not f(v):
            continue
        if v or k.startswith('__'):
            for x in {'"': "&quot;", "'": "&apos;", "`": "&#x60;"}.items():
                v = v.replace(*x)
            attrs.append(str(k) + f"=`{v}`")
        else:
            attrs.append(str(k))
    s = e.tag + ' ' + " ".join(attrs)
    if 'ulclass' in s:
        print([e.tag, s])
    return s


def lxml2json(
    html_or_str: t.Union[html.HtmlElement, str],
    ignore: set = {}, # {'defs', 'filter', 'g', 'path', 'script', 'symbol'},
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
            return {e_name: None}

        # if all inside tags are unique – it's a single dict, otherwise – list
        if len({
            get_tag(x) for x in children if (
                x.tag not in ignore and not isinstance(x, html.HtmlComment)
            )
        }) == len([
            x for x in children if (
                x.tag not in ignore and not isinstance(x, html.HtmlComment)
            )
        ]):
            e_data = {}
            for x in children:
                e_data = {**e_data, **_recurse(x)}
        else:
            e_data = [_recurse(x) for x in e.iterchildren()]

        return {e_name: e_data}


    return _recurse(
        html_or_str if isinstance(html_or_str, html.HtmlElement) else html.fromstring(
            prepare(html_or_str)
        )
    )


def json2lxml(d: t.Union[str, Struct]) -> html.HtmlElement:
    """ Convert JSON into lxml HtmlElement tree
    
    Args:
        d: some JSON in dict or serialized form

    Returns:
        lxml.html.HtmlElement: root of HTML tree formed
    
    """
    def _recurse(data: t.Any) -> str:
        if isinstance(data, list):
            _data = [("", "", x, "") for x in data]
        elif isinstance(data, dict):
            _data = []
            for k,v in data.items():
                # each tag has __(prefix|text|tail)__ attrs to be removed
                try:
                    # get back quotes, apostrophe & backquote
                    for x in {'&quot;': '"', '&apos;': "'"}.items():
                        k = k.replace(*x)
                    prefix, text, tail = [x.replace('&#x60;', "`") for x in \
                        re.findall(r'\_\_[^ =]+\_\_\=\`([^\`]*)\`', k)
                    ]
                    k = re.sub(r'\_\_[^ =]+\_\_\=\`[^\`]*\`', "", k).rstrip(' ')
                except:
                    prefix, text, tail = [""]*3
                _data.append((
                    prefix + f"<{k}>",
                    text,
                    v or '',
                    ("" if HtmlTag(_t := k.split(' ', 1)[0]).single else f"</{_t}>") + tail
                ))
        else:
            return str(data)

        res = "".join(l + c + _recurse(x) + r for l, c, x, r in _data)
        return res

    # if given dict - serialize it in str dump first
    s: str = json.dumps(d, ensure_ascii=False) if isinstance(d, Struct) else d

    # return back all doublequotes (were replaced with backtick)
    for x in re.finditer(r'[^\_ =]+\=(\`[^\`]*\`)', s):
        if "&quot;" in x.group():
            # use apostrophe if doublequote found inside attr
            s = s.replace(x.group(), x.group().replace('`', "'"))
            continue
        s = s.replace(x.group(), x.group().replace('`', '\\"'))

    return html.fromstring(_recurse(json.loads(s)))


def validate(s: str) -> bool:
    """ Validate HTML source 

    Check if page code after lxml2json & json2lxml steps will return the same 
    lxml representation as if it was processed by lxml only.

    """
    _ = lambda x: html.tostring(x, encoding='unicode')
    return _(json2lxml(lxml2json(s))) == _(html.fromstring(prepare(s)))


#  TODO: possibly remove this enum?
class HtmlTag(Enum):
    """ Enumeration of HTML tags 

    Class can also handle tags not enlisted below with overriden _missing_ class 
    method.

    """
    ABBREVIATION = 'abbr'
    ACRONYM = 'acronym'
    ADDRESS = 'address'
    ANCHOR = 'a'
    APPLET = 'applet'
    AREA = 'area'
    ARTICLE = 'article'
    ASIDE = 'aside'
    AUDIO = 'audio'
    BASE = 'base'
    BASEFONT = 'basefont'
    BDI = 'bdi'
    BDO = 'bdo'
    BGSOUND = 'bgsound'
    BIG = 'big'
    BLOCKQUOTE = 'blockquote'
    BODY = 'body'
    BOLD = 'b'
    BREAK = 'br'
    BUTTON = 'button'
    CAPTION = 'caption'
    CANVAS = 'canvas'
    CENTER = 'center'
    CITE = 'cite'
    CODE = 'code'
    COLGROUP = 'colgroup'
    COLUMN = 'col'
    DATA = 'data'
    DATALIST = 'datalist'
    DD = 'dd'
    DEFINE = 'dfn'
    DELETE = 'del'
    DETAILS = 'details'
    DIALOG = 'dialog'
    DIR = 'dir'
    DIV = 'div'
    DL = 'dl'
    DT = 'dt'
    EMBED = 'embed'
    FIELDSET = 'fieldset'
    FIGCAPTION = 'figcaption'
    FIGURE = 'figure'
    FONT = 'font'
    FOOTER = 'footer'
    FORM = 'form'
    FRAME = 'frame'
    FRAMESET = 'frameset'
    G = 'g'
    HEAD = 'head'
    HEADER = 'header'
    HEADING1 = 'h1'
    HEADING2 = 'h2'
    HEADING3 = 'h3'
    HEADING4 = 'h4'
    HEADING5 = 'h5'
    HEADING6 = 'h6'
    HGROUP = 'hgroup'
    HR = 'hr'
    HTML = 'html'
    IFRAMES = 'iframe'
    IMAGE = 'img'
    INPUT = 'input'
    INS = 'ins'
    ISINDEX = 'isindex'
    ITALIC = 'i'
    KBD = 'kbd'
    KEYGEN = 'keygen'
    LABEL = 'label'
    LEGEND = 'legend'
    LINEARGRADIENT = 'lineargradient'
    LINK = 'link'
    LIST = 'li'
    MAIN = 'main'
    MARK = 'mark'
    MARQUEE = 'marquee'
    MENUITEM = 'menuitem'
    META = 'meta'
    METER = 'meter'
    NAV = 'nav'
    NOBREAK = 'nobr'
    NOEMBED = 'noembed'
    NOINDEX = 'noindex'
    NOSCRIPT = 'noscript'
    OBJECT = 'object'
    OL = 'ol'
    OPTGROUP = 'optgroup'
    OPTION = 'option'
    OUTPUT = 'output'
    PARAGRAPHS = 'p'
    PARAM = 'param'
    PATH = 'path'
    PHRASE = 'em'
    PICTURE = 'picture'
    POLYGON = 'polygon'
    PRE = 'pre'
    PROGRESS = 'progress'
    Q = 'q'
    RP = 'rp'
    RT = 'rt'
    RUBY = 'ruby'
    S = 's'
    SAMP = 'samp'
    SCRIPT = 'script'
    SECTION = 'section'
    SELECT = 'select'
    SMALL = 'small'
    SOURCE = 'source'
    SPACER = 'spacer'
    SPAN = 'span'
    STOP = 'stop'
    STRIKE = 'strike'
    STRONG = 'strong'
    STYLE = 'style'
    SUMMARY = 'summary'
    SUB = 'sub'
    SUP = 'sup'
    SVG = 'svg'
    SYMBOL = 'symbol'
    TABLE = 'table'
    TBODY = 'tbody'
    TD = 'td'
    TEMPLATE = 'template'
    TEXTAREA = 'textarea'
    TFOOT = 'tfoot'
    TH = 'th'
    THEAD = 'thead'
    TIME = 'time'
    TITLE = 'title'
    TR = 'tr'
    TRACK = 'track'
    TT = 'tt'
    UL = 'ul'
    UNDERLINE = 'u'
    USE = 'use'
    VAR = 'var'
    VIDEO = 'video'
    WBR = 'wbr'
    XMP = 'xmp'

    @classmethod
    def values(cls) -> list[str]:
        """ ... """
        return [x.value for x in cls]

    @classmethod
    def _missing_(cls, value) -> t.Self:
        # return new object on unknown tag
        unknown_tag = object.__new__(cls)
        unknown_tag._name_ = str(value).upper()
        unknown_tag._value_ = value
        return unknown_tag

    @property
    def single(self) -> bool:
        """ Check if tag is single & doesn't need an ending tag """
        return self.value in {
            "area", 
            "base", 
            "br", 
            "col", 
            "command", 
            "embed", 
            "hr", 
            "img", 
            "input", 
            "keygen", 
            "link", 
            "meta", 
            "param", 
            "source", 
            "track", 
            "wbr"
        }
