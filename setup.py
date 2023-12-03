# -*- coding: utf-8 -*-

"""
:copyright: (c) 2021 by Michael Krukov
:license: MIT, see LICENSE for more details.
"""

import os
import setuptools


assert os.environ.get('GITHUB_REF_TYPE') == 'tag'
assert os.environ.get('GITHUB_REF_NAME')
VERSION = os.environ['GITHUB_REF_NAME'].lstrip('v')


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="mongomock_motor",
    version=VERSION,
    author="Michael Krukov",
    author_email="krukov.michael@ya.ru",
    keywords=["library", "mongodb"],
    description="Library for mocking AsyncIOMotorClient built on top of mongomock.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/michaelkryukov/mongomock_motor",
    packages=setuptools.find_packages(include=('mongomock_motor',)),
    install_requires=[
        "mongomock>=3.23.0,<5.0.0",
    ],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
