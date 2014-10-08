#!/usr/bin/env python
import argparse
import logging
import os
import posixpath
import re
import shutil
import subprocess
import sys

from six.moves.urllib import parse, request
from six.moves import zip_longest
import yaml


REPO_ROOT = os.path.dirname(__file__)


def directory(path):
    try:
        os.makedirs(path)
    except OSError:
        pass
    return path


parser = argparse.ArgumentParser(
    description='Split episodes of Welcome to Night Vale into segments')
parser.add_argument(
    '--output_dir', '-o',
    type=directory,
    default=os.path.join(REPO_ROOT, 'output'),
    help='Directory to hold split segments')
parser.add_argument(
    '--raw_dir', '-r',
    type=directory,
    default=os.path.join(REPO_ROOT, 'raw'),
    help='Directory to hold original (unsplit) episodes')
parser.add_argument(
    '--data_file', '-d',
    type=argparse.FileType('r'),
    default=os.path.join(REPO_ROOT, 'episode_info.yaml'),
    help='YAML file with episode segment information')
parser.add_argument(
    '--ffmpeg', '-f',
    default='/usr/local/bin/ffmpeg',
    help='Path to ffmpeg 2.2 or later')
parser.add_argument(
    '--overwrite', '-w',
    action='store_true',
    help='Overwrite existing files')


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def call_external_program(*args):
    """
    Provides uniform interface to subprocess.check_output.

    Regardless of the external program's exit code, this always returns a tuple
    of the return code and the output string (including stderr).
    """
    try:
        output = subprocess.check_output(
            args, stderr=subprocess.STDOUT, universal_newlines=True)
        return_code = 0
        return return_code, output
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output


def download_file(remote_url, raw_dir, overwrite=False):
    """
    Downloads a remote file.

    If a file already exists at the intended path and `overwrite` is False (the
    default), the download does not take place.

    Returns the local path to the file and a boolean saying whether the file
    was downloaded just now or whether it existed before and was left alone.
    """
    filename_only = posixpath.basename(parse.urlparse(remote_url).path)
    local_filename = os.path.join(raw_dir, filename_only)

    if os.path.exists(local_filename) and not overwrite:
        return local_filename, False

    remote_file = request.urlopen(remote_url)
    with open(local_filename, 'wb') as local_file:
        shutil.copyfileobj(remote_file, local_file)
    remote_file.close()

    return local_filename, True


def split_episode(
        episode_data, episode_filename, output_dir, ffmpeg, overwrite=False):
    """
    Splits an episode into segments using ffmpeg.

    `episode_data` should be a dict such as those you might load from
    episode_info.yaml.

    `episode_filename` should be a path to the entire episode's MP3.

    `output_dir` should be a path to the directory to which segment MP3s should
    be written.

    `ffmpeg` should be a path to the ffmpeg binary.

    `overwrite` should be truthy if the user wants existing files to be
    overwritten.
    """
    episode_number = episode_data['episode_number']
    episode_title = episode_data['title']

    segments = episode_data['segments']
    segment_pairs = zip_longest(segments, segments[1:])
    segment_count = len(segments)

    for i, (current_segment, next_segment) in enumerate(segment_pairs):
        ffmpeg_args = []
        segment_title = current_segment['title']
        segment_number = i + 1

        # Tell ffmpeg whether to overwrite any file that might already exist
        # for this segment.
        ffmpeg_args.append('-y' if overwrite else '-n')

        # Figure out where the segment starts (in seconds).
        current_start = map(float, current_segment['start'])
        current_start_seconds = current_start[0] * 60 + current_start[1]
        ffmpeg_args.extend(['-ss', str(current_start_seconds)])

        # Figure out where the segment ends (in seconds) so we know how long
        # the segment will be. If there is no next segment, then we don't care
        # --ffmpeg will just go til the end of the episode, which is what we
        # want.
        if next_segment is not None:
            next_start = map(float, next_segment['start'])
            next_start_seconds = next_start[0] * 60 + next_start[1]
            segment_length = next_start_seconds - current_start_seconds
            ffmpeg_args.extend(['-t', str(segment_length)])

        # Note where the full episode is.
        ffmpeg_args.extend(['-i', episode_filename])

        # Add some ID3 tags.
        ffmpeg_args.extend(['-metadata', (
            'title="{episode_number} - {episode_title} '
            '({segment_title})"'.format(
                episode_number=episode_number,
                episode_title=episode_title,
                segment_title=segment_title))])
        ffmpeg_args.extend(['-metadata', 'artist="Welcome to Night Vale"'])
        ffmpeg_args.extend(['-metadata', 'album="{episode_title}"'.format(
            episode_title=episode_title)])
        ffmpeg_args.extend(['-metadata', (
            'track="{segment_number}/{total_segments}"'.format(
                segment_number=segment_number,
                total_segments=segment_count))])

        # Fix the reported file duration. See
        # https://trac.ffmpeg.org/ticket/2697 for details.
        ffmpeg_args.extend(['-write_xing', '0'])

        # Determine where the segment should be saved.
        episode_number_match = re.match(r'^(\d+)(.*)$', str(episode_number))
        episode_number_number, episode_number_suffix = (
            episode_number_match.groups() if episode_number_match
            else ('', ''))
        ffmpeg_args.append(os.path.join(output_dir, (
            '{episode_number_number:0>3}{episode_number_suffix}-'
            '{episode_title}-{segment_number:0>2}-{segment_title}.mp3'.format(
                episode_number_number=episode_number_number,
                episode_number_suffix=episode_number_suffix,
                episode_title=episode_title,
                segment_number=segment_number,
                segment_title=segment_title))))

        # Tell ffmpeg to do the hard work.
        return_code, output = call_external_program(ffmpeg, *ffmpeg_args)
        if return_code == 0:
            logger.debug('Wrote segment "{title}"'.format(**current_segment))


def split_all_episodes(
        all_episode_data, raw_dir, output_dir, ffmpeg, overwrite):
    """
    Splits all episodes described in `all_episode_data`.

    `raw_dir` should be a path to the directory to which full-episode MP3s
    should be written.

    `output_dir` should be a path to the directory to which segment MP3s should
    be written.

    `ffmpeg` should be a path to the ffmpeg binary.

    `overwrite` should be truthy if the user wants existing files to be
    overwritten.
    """
    for episode_data in all_episode_data:
        episode_filename, episode_downloaded = download_file(
            episode_data['mp3_url'], raw_dir, overwrite)
        if episode_downloaded:
            logger.debug('Downloaded "{title}"'.format(**episode_data))

        split_episode(
            episode_data, episode_filename, output_dir, ffmpeg, overwrite)
        logger.info('Done with "{title}"'.format(**episode_data))


def main(*args):
    script_args = parser.parse_args(args)
    all_episode_data = yaml.safe_load(script_args.data_file)
    split_all_episodes(
        all_episode_data, script_args.raw_dir, script_args.output_dir,
        script_args.ffmpeg, script_args.overwrite)


if __name__ == '__main__':
    main(*sys.argv[1:])
