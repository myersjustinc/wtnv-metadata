#!/usr/bin/env python
import argparse
import os
import posixpath
import shutil
import subprocess
import sys

from six.moves.urllib import parse, request
from six.moves import zip_longest


REPO_ROOT = os.path.dirname(__file__)


def directory(path):
    try:
        os.makedirs(path)
    except OSError:
        raise argparse.ArgumentTypeError(
            '{0} is not a valid directory'.format(path))


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
    help='Path to ffmpeg')


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


def download_file(remote_url, raw_dir):
    """
    Downloads a remote file and returns its path.
    """
    filename_only = posixpath.basename(parse.urlparse(remote_url).path)
    local_filename = os.path.join(raw_dir, filename_only)

    remote_file = request.urlopen(remote_url)
    with open(local_filename, 'wb') as local_file:
        shutil.copyfileobj(remote_file, local_file)
    remote_file.close()

    return local_filename


def split_episode(episode_data, episode_filename, output_dir, ffmpeg):
    episode_number = episode_data['episode_number']
    episode_title = episode_data['title']

    segments = episode_data['segments']
    segment_pairs = zip_longest(segments, segments[1:])

    for i, (current_segment, next_segment) in enumerate(segment_pairs):
        ffmpeg_args = []
        segment_title = current_segment['title']

        # Figure out where the segment starts (in seconds).
        current_start = current_segment['start']
        current_start_seconds = current_start[0] * 60 + current_start[1]
        ffmpeg_args.extend(['-ss', str(current_start_seconds)])

        # Figure out where the segment ends (in seconds) so we know how long
        # the segment will be. If there is no next segment, then we don't care
        # --ffmpeg will just go til the end of the episode, which is what we
        # want.
        if next_segment is not None:
            next_start = next_segment['start']
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

        # Fix the reported file duration. See
        # https://trac.ffmpeg.org/ticket/2697 for details.
        ffmpeg_args.extend(['-write_xing', '0'])

        # Determine where the segment should be saved.
        ffmpeg_args.append(os.path.join(output_dir, (
            '{episode_number}-{episode_title}-'
            '{segment_number}-{segment_title}.mp3'.format(
                episode_number=episode_number,
                episode_title=episode_title,
                segment_number=i + 1,
                segment_title=segment_title))))

        # Tell ffmpeg to do the hard work.
        return_code, output = call_external_program(ffmpeg, *ffmpeg_args)


def main(*args):
    script_args = parser.parse_args(args)
    # TODO: Keep going.


if __name__ == '__main__':
    main(*sys.argv[1:])
