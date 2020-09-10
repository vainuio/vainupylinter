#! /usr/bin/env python
# Copyright (C) 2019 Susanna Aro
# License: 3-clause BSD

import sys
import os

from setuptools import setup, find_packages

if sys.version_info[0] < 3:
    if sys.version_info[1] < 7:
        raise ValueError("Only python >= 2.7 is supported")
    INSTALL_REQUIRES = ["pylint==1.9", "mock"]
else:
    INSTALL_REQUIRES = ["pylint>2.0"]

LONG_DESCRIPTION = open("README.md").read()

setup(
    name="vainupylinter",
    url="https://github.com/vainuio/vainupylinter",
    author="susanna@vainu.io",
    author_email="susanna@vainu.io",
    description="A custom pylint runner for pylint in use in some Vainu repositories",
    version="1.1.1",
    packages=find_packages(),
    entry_points={"console_scripts": ["vainupylinter=vainupylinter.custom_runner:run"],},
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    license="BSD",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 2.7",
    ],
)
