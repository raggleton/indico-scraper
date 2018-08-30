#!/usr/bin/env python


"""Script to download all attachments from an Indico event"""


from __future__ import print_function
import os
import sys
import argparse
from time import sleep
from collections import namedtuple
import requests
import bs4

try:
    # python3
    import urllib.parse as urlparse
except ImportError:
    # python2
    import urlparse


# Class to hold info about each talk entry
TalkEntry = namedtuple("TalkEntry", ["title", "speaker", "affiliation", "URL", "abstract"])


def validate_indico_url(url):
    # "https://indico.cern.ch/event/662485/timetable/?view=standard"
    url_info = urlparse.urlparse(url)
    path_parts = url_info.path.split("/")
    start_ind = path_parts.index("event")
    parts = path_parts[start_ind:start_ind+2]
    parts.append("timetable")
    new_path = "/".join([""]+parts+[""])
    new_url_info = urlparse.ParseResult(
        scheme=url_info.scheme,
        netloc=url_info.netloc,
        path=new_path,
        params='',
        query='view=standard',
        fragment=''
    )
    return new_url_info.geturl()


def get_soup_from_url(url):
    r = requests.get(url)  # use standard view as includes abstract info
    if r.status_code != requests.codes.ok:
        print("Could not get Indico page, please check URL")
        return 1
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    return soup


def get_entries(soup):
    """Get all contributions in the timetable

    Returns list of TalkEntry objects that contain info about each talk
    """
    entries = []

    link_stem = "https://indico.cern.ch"
    for entry in soup.findAll('li', 'timetable-contrib'):
        title_tag = entry.find('span', 'timetable-title')
        if not title_tag:
            continue
        title = title_tag.text

        speaker = ""
        affiliation = ""
        speaker_tag = entry.find('div', 'speaker-list')
        if speaker_tag:
            speaker_tag = speaker_tag.find('span', "")
            # need the blank classname to avoid getting title
            speaker = speaker_tag.find('span', "").text
            affiliation_tag = speaker_tag.find('span', 'affiliation')
            if affiliation_tag:
                affiliation = affiliation_tag.find('span', 'text').text

        abstract = ""
        abstract_tag = entry.find("div", "contrib-description")
        if abstract_tag:
            abstract = abstract_tag.find('p').text

        link_tag = entry.find('a', 'attachment')
        if link_tag:
            link = link_stem + link_tag['href']
            entries.append(TalkEntry(title, speaker, affiliation, link, abstract))

    return entries


def default_filename(entry):
    template = "{title}-{speaker}.pdf"
    return template.format(**entry._asdict())


def download_file(url, output_filename):
    print("Downloading", url, "to", output_filename)
    r = requests.get(url)
    if r.status_code != requests.codes.ok:
        print("Cannot download", url, "status code:", r.status_code)
    else:
        with open(output_filename, 'wb') as f:
            f.write(r.content)


def download_talks(entries, download_dir, filename_generator, pause=5, skip_existing=True):
    pause = float(pause)
    if pause <= 1:
        pause = 1
        print("You should be nice to the server, setting pause to 1 second")

    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)

    for entry in entries:
        output_filename = os.path.join(download_dir, filename_generator(entry))
        # replace extensions with the one from URL
        output_filename = os.path.splitext(output_filename)[0] + os.path.splitext(entry.URL)[1]
        if not os.path.isfile(output_filename) or not skip_existing:
            download_file(entry.URL, output_filename)
            sleep(pause)  # be nice to the server
        else:
            print("Skipping", entry.URL, "as already downloaded (use -f to override)")


def main(in_args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url",
                        help="Indico event URL")
    parser.add_argument("-f", "--force",
                        help="Download file even if it already exists", action='store_true')
    parser.add_argument("-o", "--output",
                        help="Directory to place files. Defaults to name of Indico event")
    parser.add_argument("--pause",
                        help="Time to wait between files being downloaded (in seconds)",
                        type=int)
    parser.add_argument("-n", "--number",
                        help="Total number of entries to download. -1 is all (default)",
                        type=int,
                        default=-1)
    args = parser.parse_args(in_args)

    soup = get_soup_from_url(validate_indico_url(args.url))
    event_title = soup.title.text.replace("· Indico", "").strip()
    output_dir = args.output if args.output else event_title
    entries = get_entries(soup)
    num_entries = len(entries)
    print("Found", num_entries, "talks")
    end_ind = num_entries if args.number < 0 else args.number
    download_talks(entries=entries[:end_ind],
                   download_dir=output_dir,
                   filename_generator=default_filename,
                   pause=args.pause,
                   skip_existing=not args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
