# Music Wrapped

A tool utilizing the last.fm APIs or musicbrainz/listenbrainz to analyze what you've been listening to and provide a Spotify-wrapped like summary of your listening. Currently prints to console.

## Usage

Install the requirements:
`pip3 install -r requirements.txt`

```text
usage: brainz.py [-h] [--fast] [--listenbrainz] [-t str] [--output str] [--input str] str

Get aggregates like Spotify Wrapped from Last.FM/ListenBrainz.

positional arguments:
  str                 Last.FM/ListenBrainz username

optional arguments:
  -h, --help          show this help message and exit
  --fast              Use last.fm generated aggregates for faster results. Only works for last 7 days
  --listenbrainz      Use listenbrainz instead of last.fm
  -t str, --time str  Specify the timeframe. Defaults to all time, you can say 'today', 'week', 'xd' (where x is the number of previous days), '1m', 'xxxxy' (where xxxx is the calendar year), or 'all'
  --output str        Filename to output to
  --input str         Read a JSON file instead of getting the data from last.fm/listenbrainz
```

Be sure to add your last.fm API token in `brainz.py` if you wish to use last.fm
