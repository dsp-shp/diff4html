# diff4html

Tools for converting HTMLs to dicts & calculating diff between them.

### 🛠️ Installation
```bash
pip install diff4html
```

### ⚡️ Usage
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
        page_1 == page_2
Out[1]: False
```

Let's then calculate diff between them. For example: I don't want to store the whole page 2 source code and want only delta to remain.
```python
In [2]: diff = page_2 - page_1
        diff
Out[2]: <HtmlDiff>
```
What this code does is getting data about what parts of page 1 will be added, changed or removed in page 2.

If one day I want to restore the entire source code of the page 2 I can do the following. We can check their equality right away:
```python
In [3]: page_2_restored = page_1 + diff
        page_2_restored == page_2
Out[3]: True
```

There is also a hash mechanism under the hood that protects the delta to be applied to any random html:
```python
In [4]: diff + page_2 # diff can be applied to page_1 only
Out[4]: ValueError: wrong snapshot used for applying diff
```

And one want to use lxml after all here's a workaround:
```python
In [5]: page_2_restored.to_lxml()
Out[5]: <Element div at 0x000000000>
```

