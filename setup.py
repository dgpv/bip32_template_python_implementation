#!/usr/bin/env python

import os

from setuptools import setup, find_packages  # type: ignore

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

setup(
    name='bip32template',
    version='0.0.4',
    description='Reference implementation of BIP32 templates',
    long_description=README,
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.6',
    url='https://github.com/dgpv/bip32_template_python_implementation',
    keywords='bitcoin bip32',
    packages=find_packages(),
    zip_safe=False,
    install_requires=[],
    test_suite="tests"
)
