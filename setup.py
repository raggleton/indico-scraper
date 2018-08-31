#!/usr/bin/env python

from distutils.core import setup

setup(
    name='indico-scraper',
    version='0.1',
    description="Download all attachments from an Indico event",
    author='Robin Aggleton',
    author_email='',
    url='https://github.com/raggleton/indico-scraper',
    scripts=['indico-scraper.py'],
    install_requires=[
        'beautifulsoup4',
        'requests',
    ]
)
