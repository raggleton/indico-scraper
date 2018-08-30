#!/usr/bin/env python


"""Script to download all attachments from an Indico event"""


from __future__ import print_function
import os
import sys
from time import sleep
from collections import namedtuple
import requests
import bs4


# Class to hold info about each talk entry
TalkEntry = namedtuple("TalkEntry", ["title", "speaker", "affiliation", "URL", "abstract"])


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
            speaker = speaker_tag.find('span', "").text  # need the blank classname to avoid getting title
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


def download_talks(entries, download_dir, filename_generator, pause=5):
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
        if not os.path.isfile(output_filename):
            download_file(entry.URL, output_filename)
            sleep(pause)  # be nice to the server
        else:
            print("Skipping", entry.URL, "as already downloaded")


def main(in_args):
    r = requests.get("https://indico.cern.ch/event/662485/timetable/?view=standard")  # use standard view as includes abstract info
    if r.status_code != requests.codes.ok:
        print("Could not get Indico page, please check URL")
        return 1
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    event_title = soup.title.text.replace("· Indico", "").strip()
    output_dir = event_title
    entries = get_entries(soup)
    print("Found", len(entries), "talks")
    download_talks(entries[:5], output_dir, default_filename)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
