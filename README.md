# diff4html

Tools for converting HTMLs to dicts & calculating diff between them.

### 🔎 What for?
Well, if you need to calculate the diff between HTML pages without inplace markup (with `<ins>` & `<del>` tags), or maybe you experience issues with matching these tags later, or even find the [htmldiff's](https://lxml.de/api/lxml.html.diff-pysrc.html#htmldiff) behavior not entirely accurate, then diff4html may be a great fit for you.

Unlike htmldiff, the result here is a difference object. This object is a list containing information about each change. Each change, in turn, is described by the start and end indices of the modification in the original HTML page, along with the subject of the change. 

Application of this is fully handled by diff4html and can be triggered via simple Python API, so you don't have to restore snapshots on your own.

### 🛠️ Installation
```bash
pip install diff4html
```

### ⚡️ Usage
Let's start with running IPython or Jupyter and making two HtmlDicts for our pages. The one for an example.org page and the other for slightly modified version of it:
> **HtmlDict** here is simply a representation of HTML tree built on native Python dict & list data types.

```python
In [1]: import requests
        from diff4html import HtmlDict

        page_1 = HtmlDict(requests.get("https://example.org").text)
        page_2 = HtmlDict("""
            <html>
                <head>
                    <title>Example Domain</title>
                    <!-- NOTICE: missing meta & styles here -->
                </head>
                <body>
                    <div>
                        <h1>Example Domain modified</hi> <!-- NOTICE: changed text-->
                        <!-- NOTICE: missing rest -->
                    </div>
                </body>
            </html>
        """)
        page_2
Out[1]: <HtmlDict({...})>
```

Let's then calculate diff between them. For example: I don't want to store the whole page 2 source code and want only delta to remain.
```python
In [2]: diff = page_2 - page_1
        diff
Out[2]: <HtmlDiff([...])>
```
What this code does is it determines which parts of page 1 were deleted, modified, and added in page 2, and returns information about all these changes in the form of an HtmlDiff object.

>**HtmlDiff**, in the context of page 2 - page 1, is a list of changes in the form of (`s`, `e`, `t`), where `s` and `e` are the start and end indices pointing to the differing element in page 1, and `t` is the content of the corresponding differing element in page 2.

If one day I want to restore the entire source code of the page 2 I can do the following. We can check their equality right away:
```python
In [3]: page_2_restored = page_1 + diff # you can think of it as: 
        # page_1 + (page_2 - page_1) => page_1 + page_2 - page_1 => page_2
        page_2_restored == page_2
Out[3]: True
```

BTW: there is a hash mechanism under the hood that protects the delta to be applied to any random html:
```python
In [4]: diff + page_2 # diff can be applied to page_1 only
Out[4]: ValueError: wrong snapshot used for applying diff
```

And if I want to use lxml after all here's a pretty straight workaround for it:
```python
In [5]: page_2_restored.to_lxml()
Out[5]: <Element div at 0x000000000>
```

