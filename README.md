# Welcome to Night Vale episode metadata #

This is an effort to tag segments of episodes of
[Welcome to Night Vale](http://www.welcometonightvale.com/).

## Episode-splitting script ##

This repository also includes a script to automate the splitting of those
episodes into the tagged segments, mainly for those trying to seek to specific
parts of the podcast.

The script requires [Python](http://www.python.org/) 2 (2.6 or later) or
Python 3. It also requires [ffmpeg](http://ffmpeg.org/) 2.2 or later.

To use the script, run `split_episodes.py` (or `python split_episodes.py`) from
the command line. If your copy of ffmpeg does not live at
`/usr/local/bin/ffmpeg`, you'll need to specify that with the `-f` option.

Usage information (from `split_episodes.py -h`):

    $ ./split_episodes.py -h
    usage: split_episodes.py [-h] [--output_dir OUTPUT_DIR] [--raw_dir RAW_DIR]
                             [--data_file DATA_FILE] [--ffmpeg FFMPEG]
                             [--overwrite]

    Split episodes of Welcome to Night Vale into segments

    optional arguments:
      -h, --help            show this help message and exit
      --output_dir OUTPUT_DIR, -o OUTPUT_DIR
                            Directory to hold split segments
      --raw_dir RAW_DIR, -r RAW_DIR
                            Directory to hold original (unsplit) episodes
      --data_file DATA_FILE, -d DATA_FILE
                            YAML file with episode segment information
      --ffmpeg FFMPEG, -f FFMPEG
                            Path to ffmpeg 2.2 or later
      --overwrite, -w       Overwrite existing files

## Contributing ##

If you want to help improve the episode splitter or tag certain episodes, feel
free! I'm always happy to look over pull requests, especially since some of the
back episodes aren't tagged yet.

## Q&A ##

* **How does the episode info file work?**

  It's written in [YAML](http://en.wikipedia.org/wiki/YAML), which is a nice,
  human-readable data format that works a lot like
  [JSON](http://en.wikipedia.org/wiki/JSON).

  The use of it here is inspired by the
  [unitedstates](https://github.com/unitedstates) project's
  [legislator lists](https://github.com/unitedstates/congress-legislators).

* **Can I add other data to the episode file?**

  Sure! I just need at least the following for each episode:

  * episode number
  * title
  * MP3 URL (from [libsyn](nightvale.libsyn.com))
  * segments, each with a title (short and spoiler-free) and a start time (in minutes and seconds)

  Any other info is optional and welcomed.

* **Where can I download segments of WTNV episodes?**

  Not here. I don't want to get involved with copyright infringement by
  distributing that stuff directly. I'm simply giving you a way to generate
  those segments (sort of similar to
  [format-shifting](http://en.wikipedia.org/wiki/Format_shifting) the
  originals) by yourself if you choose to do so.

* **Why isn't this called an FAQ section?**

  Because nobody's actually asked me these questions yet--let alone frequently.
