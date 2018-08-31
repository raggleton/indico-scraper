# indico-scraper

This script is designed to scrape an Indico event, and download all the attachments.
By default it only downloads PDFs, but one can filter for any file extensions

## Install

TODO

## Running

Show options: `indico-scraper.py -h`

e.g. `indico-scraper.py https://indico.cern.ch/event/662485/`

Note that you can pass it any level of the event, and it will automatically figure out the event and download everything.

e.g. `indico-scraper.py https://indico.cern.ch/event/662485/contributions/3050131/attachments/1708201/2752955/rottoli_resum_Dresden2018.pdf` has the same result as the above command

**Please use responsibly.**

## Current limitations

Can't handle webpages behind CERN SSO. Need to pass user certs + CERN CA + ?
