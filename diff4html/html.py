import json
import re
import typing as t
from enum import Enum, EnumType

from lxml import html

Struct = t.Union[dict, list, tuple]


def prepare(s: str) -> str:
    """ Replace whitespaces

    Function used to replace all whitespaces (and '\xa0' too) in HTML string by
    Braille Blank (U+2800). Otherwise there will be troubles with comparing
    tokens in htmldiff function.
    
    """
    for k,v in {
        "\t": "", r"\n[ ]+\n": "\n", r"\n": "", r"\ [\ ]+": " ", r"\>[ ]+\<": "><"
    }.items():
        s = re.sub(k, v, s)
    for x in re.finditer(r"\>([^\<]+)\<\/", s):
        s = s[:x.span()[0]] +\
            x.group().replace(" ", " ").replace("\xa0", " ") +\
            s[x.span()[1]:]
    return s


def get_tag(
    e: html.HtmlElement,
    f: t.Callable = lambda x: True # len(x) <= 500
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
        e.tag + ' ' + " ".join("%s%s" % (
            k, ('=`%s`' % v.replace('"', "&quot;").replace("'", "&apos;")) if (
                v or k.startswith('__')
            ) else ""
        ) for k,v in {
            **e.attrib,
            "__prefix__": e.prefix or "", 
            "__text__": e.text or "", 
            "__tail__": e.tail or ""
        }.items() if f(v or ''))
        #  WARNING: possibly not use filter because of data loss
    ).strip(' ') if isinstance(e, html.HtmlElement) else None


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
            get_tag(x) for x in children if x.tag not in ignore and not isinstance(x, html.HtmlComment)
        }) == len([
            x for x in children if x.tag not in ignore and not isinstance(x, html.HtmlComment)
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
                # Each tag has __prefix, __text & __tail attrs to be removed
                try:
                    k = k.replace('&quot;', '"').replace('&apos;', "'")
                    prefix, text, tail = re.findall(r'\_\_[^ =]+\_\_\=\`([^\`]*)\`', k)
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
            s = s.replace(x.group(), x.group().replace('`', "'"))
            continue
        s = s.replace(x.group(), x.group().replace('`', '\\"'))
    
    #  TODO: replace whitespaces on Braile Blank maybe?

    return html.fromstring(_recurse(json.loads(s)))


class HtmlTag(Enum):
    """ Enumeration of HTML tags """
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
        return [x.value for x in cls]

    @property
    def single(self) -> bool:
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
