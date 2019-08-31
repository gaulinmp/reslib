# -*- coding: utf-8 -*-
"""
ResLib (Research Library) is a python based package to facilitate the basic
functionality useful for a research project in Python.
"""

import os
import re
from codecs import open

# Prefer setuptools over distutils
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

_dir = lambda *x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

# Get the long description from the README file
with open(_dir('README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the version information from __version__.py
version = {}
with open(_dir('reslib', '__version__.py'), 'r', encoding='utf-8') as f:
    exec(f.read(), version)

setup(
    name=version['__title__'],
    version=version['__version__'],
    description=version['__description__'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=version['__author__'],
    author_email=version['__author_email__'],
    url=version['__url__'],
    project_urls={
        'Documentation': version['__url__'],
        'Source': 'https://github.com/gaulinmp/reslib',
    },
    license=version['__license__'],
    keywords='academic research,data pipelines',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    packages=['reslib',],
    install_requires=[
        'pandas>=0.22.0',
        ],
    extras_require={
        'dev': [
            'bs4'
            'tqdm',
            # 'pyedgar',
            ],
        # 'test': ['coverage'],
    },
)
