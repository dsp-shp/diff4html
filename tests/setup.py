import os

import setuptools

#  INFO: install dev & extra dependencies
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
diff4html_dist = setuptools.distutils.core.run_setup("setup.py", stop_after="init")
requirements = diff4html_dist.install_requires + diff4html_dist.extras_require["dev"]
os.chdir(os.path.dirname(__file__))

setuptools.setup(
    name="diff4html-tests",
    description="Tests for diff4html",
    url="https://github.com/dsp-shp/diff4html",
    author="Ivan Derkach",
    author_email="dsp_shp@icloud.com",
    license="Apache License 2.0",
    package_dir={"diff4html_tests": ""},
    install_requires=requirements,
)

