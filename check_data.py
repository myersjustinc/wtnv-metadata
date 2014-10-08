#!/usr/bin/env python
import argparse
import logging
import os
import sys

from six import string_types
import yaml

# ABCs moved in Python 3, but six doesn't keep track of them.
try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence


REPO_ROOT = os.path.dirname(__file__)


parser = argparse.ArgumentParser(
    description='Verify the format of a '
    'Welcome to Night Vale episode data file')
parser.add_argument(
    '--data_file', '-d',
    type=argparse.FileType('r'),
    default=os.path.join(REPO_ROOT, 'episode_info.yaml'),
    help='YAML file with episode segment information')


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def check_overall_data_type(all_episode_data):
    """
    The file should describe a list or other sequence.
    """
    ok = (
        isinstance(all_episode_data, Sequence) and
        not isinstance(all_episode_data, string_types))
    if not ok:
        raise TypeError('Top-level data structure is not a list')


def check_required_segment_data(segment):
    """
    Make sure the segment has all required fields.
    """
    try:
        title = segment['title']
    except KeyError:
        raise KeyError('Segment is missing its title')
    if not isinstance(title, string_types):
        raise TypeError('Segment title must be a string')

    try:
        start = segment['start']
    except KeyError:
        raise KeyError('Segment is missing its start time')

    if not isinstance(start, Sequence):
        raise TypeError('Segment start time must be a list of length 2')
    if len(start) < 2:
        raise TypeError('Segment start time must have two elements')

    try:
        start_minutes = float(start[0])
    except ValueError:
        raise TypeError('Segment start minute must be castable to float')
    if start_minutes < 0:
        raise ValueError('Segment start minute must not be negative')

    try:
        start_seconds = float(start[1])
    except ValueError:
        raise TypeError('Segment start second must be castable to float')
    if start_seconds < 0:
        raise ValueError('Segment start second must not be negative')


def check_required_episode_data(episode):
    """
    Make sure the episode has all required fields.
    """
    try:
        episode_number = episode['episode_number']
    except KeyError:
        raise KeyError('Episode is missing its episode number')
    if not (
            isinstance(episode_number, int) or
            isinstance(episode_number, string_types)):
        raise TypeError('Episode number must be a string or an integer')

    try:
        title = episode['title']
    except KeyError:
        raise KeyError('Episode is missing its title')
    if not isinstance(title, string_types):
        raise TypeError('Episode title must be a string')

    try:
        mp3_url = episode['mp3_url']
    except KeyError:
        raise KeyError('Episode is missing its MP3 URL')
    if not isinstance(mp3_url, string_types):
        raise TypeError('Episode MP3 URL must be a string')

    try:
        segments = episode['segments']
    except KeyError:
        raise KeyError('Episode is missing its segments')
    if not isinstance(segments, Sequence):
        raise TypeError('Episode MP3 URL must be a list')

    if not segments:
        raise ValueError('Episode must have at least one segment')

    for segment in segments:
        check_required_segment_data(segment)
        logger.info('    Segment data OK for "{title}"'.format(**segment))


def main(*args):
    script_args = parser.parse_args(args)
    all_episode_data = yaml.safe_load(script_args.data_file)

    check_overall_data_type(all_episode_data)
    logger.info('Overall data type OK\n')

    for episode in all_episode_data:
        check_required_episode_data(episode)
        logger.info('Episode data OK for "{title}"\n'.format(**episode))

    logger.info('All OK!')


if __name__ == '__main__':
    main(*sys.argv[1:])
