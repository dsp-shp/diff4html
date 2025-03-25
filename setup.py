from os import path

from setuptools import find_packages, setup

long_description = open("README.md", "r", -1, "utf8").read() if path.exists('README.md') else ""

setup(
    name="diff4html",
    url="https://github.com/dsp-shp/diff4html",
    project_urls={
        "Source Code": "https://github.com/dsp-shp/diff4html",
    },
    author="Ivan Derkach",
    author_email="dsp_shp@icloud.com",
    description="Tools for converting HTMLs to dicts & calculating diff between them",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    license_files=("LICENSE.txt",),
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"": ["examples/**"]},
    python_requires=">=3.11",
    install_requires=[
        "lxml==5.3.1",
    ],
    extras_require={
        "dev": [
            "mypy",
            "pylint",
            "pytest",
            "notebook"
        ],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
