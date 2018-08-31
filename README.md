# indico-scraper

This script is designed to scrape an Indico event, and download all the attachments.
By default it only downloads PDFs, but one can filter for any file extensions

## Install

Git clone this repository, then inside the clonded directory do: `pip install -e .`

Note that the directory `pip` installs the files to may not be on your `PATH` variable and you may have to add it manually.
e.g. for python3 from homebrew on Mac OSX, it is `/usr/local/bin/`

## Running

Show options: `indico-scraper.py -h`

e.g. `indico-scraper.py https://indico.cern.ch/event/662485/`

Note that you can pass it any level of the event, and it will automatically figure out the event and download everything.

e.g. `indico-scraper.py https://indico.cern.ch/event/662485/contributions/3050131/attachments/1708201/2752955/rottoli_resum_Dresden2018.pdf` has the same result as the above command

**Please use responsibly.**

## Current limitations

Can't handle webpages behind CERN SSO. Need to pass user certs + CERN CA + ?
