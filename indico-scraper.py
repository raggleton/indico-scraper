#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Script to download all attachments from an Indico event"""


from __future__ import print_function, unicode_literals
import os
import sys
import argparse
from time import sleep
from collections import namedtuple
import itertools
import re
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
    r = requests.get(url)
    r.raise_for_status()
    soup = bs4.BeautifulSoup(r.text, 'html.parser')
    return soup


def get_entries(soup, use_extensions=None):
    """Get all contributions in the timetable.
    Optionally only get filenames that have an extension in use_extensions.
    Returns list of TalkEntry objects that contain info about each talk.
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

        for link_tag in entry.find_all('a', 'attachment'):
            link = link_stem + link_tag['href']
            if ((use_extensions is not None and os.path.splitext(link)[1].lstrip(".") in use_extensions)
                or use_extensions is None):
                entries.append(TalkEntry(title, speaker, affiliation, link, abstract))

    return entries


def default_filename(entry):
    template = "{title}-{speaker}.pdf"
    return template.format(**entry._asdict())


# needed for sanitizing filenames in restricted mode
ACCENT_CHARS = dict(zip('ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ',
                        itertools.chain('AAAAAA', ['AE'], 'CEEEEIIIIDNOOOOOOO', ['OE'], 'UUUUUYP', ['ss'],
                                        'aaaaaa', ['ae'], 'ceeeeiiiionooooooo', ['oe'], 'uuuuuypy')))


def sanitize_filename(s, restricted=False, is_id=False):
    """Sanitizes a string so it could be used as part of a filename.
    If restricted is set, use a stricter subset of allowed characters.
    Set is_id if this is not an arbitrary string, but an ID that should be kept
    if possible.

    TAKEN FROM youtube-dl
    https://github.com/rg3/youtube-dl/blob/9e21e6d96bed929ba57b8ce775e2a0e29e54dd60/youtube_dl/utils.py
    """
    def replace_insane(char):
        if restricted and char in ACCENT_CHARS:
            return ACCENT_CHARS[char]
        if char == '?' or ord(char) < 32 or ord(char) == 127:
            return ''
        elif char == '"':
            return '' if restricted else '\''
        elif char == ':':
            return '_-' if restricted else ' -'
        elif char in '\\/|*<>':
            return '_'
        if restricted and (char in '!&\'()[]{}$;`^,#' or char.isspace()):
            return '_'
        if restricted and ord(char) > 127:
            return '_'
        return char

    # Handle timestamps
    s = re.sub(r'[0-9]+(?::[0-9]+)+', lambda m: m.group(0).replace(':', '_'), s)
    result = ''.join(map(replace_insane, s))
    if not is_id:
        while '__' in result:
            result = result.replace('__', '_')
        result = result.strip('_')
        # Common case of "Foreign band name - English song title"
        if restricted and result.startswith('-_'):
            result = result[2:]
        if result.startswith('-'):
            result = '_' + result[len('-'):]
        result = result.lstrip('.')
        if not result:
            result = '_'
    return result


def download_file(url, output_filename):
    print("Downloading", url, "to", output_filename)
    r = requests.get(url)
    r.raise_for_status()
    with open(output_filename, 'wb') as f:
        f.write(r.content)


def download_talks(entries, download_dir, filename_generator, pause=5, skip_existing=True, dry_run=False):
    pause = int(pause)
    if pause < 1:
        pause = 1
        print("You should be nice to the server, setting pause to 1 second")

    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)

    for entry in entries:
        output_filename = os.path.join(download_dir, sanitize_filename(filename_generator(entry)))
        # replace extensions with the one from URL
        output_filename = os.path.splitext(output_filename)[0] + os.path.splitext(entry.URL)[1]
        if dry_run:
            print(entry.URL, "->", output_filename)
        else:
            if not os.path.isfile(output_filename) or not skip_existing:
                download_file(entry.URL, output_filename)
                sleep(pause)  # be nice to the server
            else:
                print("Skipping", entry.URL, "as already downloaded (use -f to override)")


def main(in_args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url",
                        help="Indico event URL")
    parser.add_argument("-e", "--ext",
                        action='append',
                        help="Only use these file extensions. Default is ['pdf']",
                        default=['pdf'])
    parser.add_argument("-f", "--force",
                        help="Download file even if it already exists",
                        action='store_true')
    parser.add_argument("-o", "--output",
                        help="Directory to place files. Defaults to name of Indico event")
    parser.add_argument("--pause",
                        help="Time to wait between files being downloaded (in seconds). Default is 1 second.",
                        default=1,
                        type=int)
    parser.add_argument("-n", "--number",
                        help="Total number of entries to download. -1 is all (default)",
                        type=int,
                        default=-1)
    parser.add_argument("--dry",
                        help="Parse event page, print but do not download talk files.",
                        action='store_true')
    args = parser.parse_args(in_args)

    soup = get_soup_from_url(validate_indico_url(args.url))
    event_title = soup.title.text.replace("· Indico", "").strip()
    output_dir = args.output if args.output else event_title
    # strip preceeding periods for consistency
    if args.ext:
        args.ext = [x.lstrip(".") for x in args.ext]
    entries = get_entries(soup, args.ext)
    num_entries = len(entries)
    print("Found", num_entries, "talks")
    end_ind = num_entries if args.number < 0 else args.number
    download_talks(entries=entries[:end_ind],
                   download_dir=output_dir,
                   filename_generator=default_filename,
                   pause=args.pause,
                   skip_existing=not args.force,
                   dry_run=args.dry)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
