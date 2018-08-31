# indico-scraper

This script is designed to scrape an Indico event, and download all the attachments.
By default it only downloads PDFs, but one can filter for any file extensions

## Install

TODO

## Running

Show options: `indico-scraper.py -h`

e.g. `indico-scraper.py https://indico.cern.ch/event/662485/`

**Please use responsibly.**

## Current limitations

Can't handle webpages behind CERN SSO. Need to pass user certs + CERN CA + ?
