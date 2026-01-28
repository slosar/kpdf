#!/usr/bin/env python3
"""Setup script for kpdf."""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kpdf",
    version="0.2.0",
    author="kpdf contributors",
    description="Display PDF files in terminal using Kitty graphics protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slosar/kpdf",
    py_modules=["kpdf"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "kpdf=kpdf:main",
        ],
    },
)
