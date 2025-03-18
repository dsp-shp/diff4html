from os import path

from setuptools import find_packages, setup

long_description = open("README.md", "r", -1, "utf8").read() if path.exists('README.md') else ""

setup(
    name="ht2dict",
    version="0.0.0",
    author="Ivan Derkach",
    author_email="dsp_shp@icloud.com",
    description="HTML to python dict converter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    license_files=("LICENSE.txt",),
    url="https://github.com/dsp-shp/ht2dict",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"": ["examples/**"]},
    python_requires=">=3.7",
    install_requires=[
        "lxml",
    ],
    extras_require={
        "dev": [
            "mypy",
            "pylint",
            "pytest",
        ],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT Software License",
        "Operating System :: OS Independent",
        "Programming Language :: SQL",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
