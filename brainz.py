from os import write
import pylistenbrainz
import musicbrainzngs
from pylistenbrainz import listen
from pylast import User, LastFMNetwork

from datetime import datetime, timedelta, date
import json
import requests
import argparse

from analyze_data import print_data

LAST_FM_API = ""

def date_to_epoch(desired_date):
	if desired_date is None:
		return None
	return int(datetime.combine(desired_date, datetime.min.time()).timestamp())

def write_to_file(filename, artist_dict, song_dict, total_tags, total_time):
	d = {'artists': artist_dict, 'songs':song_dict, 'tags':total_tags, 'time':total_time}
	json_string = json.dumps(d, indent=4)
	with open(filename, "w") as outfile:
		outfile.write(json_string)

def read_file(filename):
	with open(filename, "r") as data:
		js_data = json.load(data)
	return js_data['artists'], js_data['songs'], js_data['tags'], js_data['time']

def listen_brainz(username, start_time=None, end_time=None, artist_dict=None, song_dict=None, tag_dict=None, total_listening_time=0):
	"""
	username: listenbrainz username to scrape
	start_time: The start time to look for music (in epoch)
	end_time: None for current time, set time in epoch if you want a custom timeframe
	artist_dict: Dictionary of {artist:num} to append data to
	song_dict: Dictionary of {song:num} to append data to
	tag_dict: Dictionary of {tags:num} to append data to
	total_listening_time: Total time spent listening, in ms
	"""
	print("Using Listenbrainz + Musicbrainz")
	# Define musicbrainz and listenbrainz clients
	musicbrainzngs.set_useragent("Brainz Data script", "0.1", "http://cool00geek.github.io/")
	client = pylistenbrainz.ListenBrainz()

	# Define data structures if they aren't already
	artist_dict = {} if artist_dict is None else artist_dict
	song_dict = {} if song_dict is None else song_dict
	tag_dict = {} if tag_dict is None else tag_dict
	max_ts = end_time

	# Get all tracks until we run out of tracks
	while True:
		listens = client.get_listens(username=username, count=100, min_ts=start_time, max_ts=max_ts)
		for listen in listens:
			print("Track name:", listen.track_name)
			print("Listened at:", listen.listened_at)
			max_ts=listen.listened_at
			result = musicbrainzngs.search_recordings(limit=10, artist=listen.artist_name, recording=listen.track_name, type="Album")
			rec_type = result['recording-list'][0]['release-list'][0]['release-group']['type']
			if rec_type != "Single" and rec_type != "Album":
				result = musicbrainzngs.search_recordings(limit=10, artist=listen.artist_name, recording=listen.track_name, type="Single")

			# Get the length
			index = 0
			while index < 10:
				try:
					length = result['recording-list'][index]['release-list'][0]['medium-list'][0]['track-list'][0]['length']
					break
				except:
					index+=1
			if index==10:
				# Unable to find the length, so just set it to be 0
				length = 0

			# Get the tags (genre)
			index = 0
			while index < 10:
				try:
					tags = result['recording-list'][index]['tag-list']
					break
				except:
					index+=1
			if index==10:
				# Unable to find tags, so just set it to be empty
				tags = []

			# Add data to the data structures
			total_listening_time += int(length)
			artist_dict.update({listen.artist_name: 1+ artist_dict.get(listen.artist_name, 0)})
			song_dict.update({listen.track_name: 1+song_dict.get(listen.track_name, 0)})
			for tag_entry in tags:
				tag_dict.update({tag_entry['name']: 1+tag_dict.get(tag_entry['name'], 0)})
		
		# If we've reached the end of listens, exit
		if len(listens) < 100:
			break
	return artist_dict, song_dict, tag_dict, total_listening_time

def _last_fm_request(start=None, end=None, **params):
	params['api_key'] = LAST_FM_API
	if start is not None:
		params['from'] = start
	if end is not None:
		params['to'] = end
	
	r = requests.get("https://ws.audioscrobbler.com/2.0/", params=params)
	return r.json()


def get_full_data_lastfm(username, start_time=None, end_time=None, artist_dict=None, song_dict=None, tag_dict=None, total_listening_time=0):
	"""
	Slow way to get user data given last.fm, will fill in the gaps that the quick n dirty function leaves
	Works exactly the same as listenbrainz (so it'll be slower)
	"""
	print("Using lastfm")
	# Define data structures if they aren't already
	artist_dict = {} if artist_dict is None else artist_dict
	song_dict = {} if song_dict is None else song_dict
	tag_dict = {} if tag_dict is None else tag_dict
	max_ts = end_time

	# Get all tracks until we run out of tracks
	while True:
		listens_params = {"method": "user.getrecenttracks", "user":username, "format":"json", "limit":100}
		listens_raw = _last_fm_request(start=start_time, end=max_ts, **listens_params)
		listens = listens_raw.get('recenttracks', {}).get('track', {})
		for listen in listens:
			# If we're currently listening to it we don't care
			if '@attr' in listen:
				continue
			# Print some info helpful for debugging
			print("Track name:", listen['name'])
			print("Listened at:", listen['date']['uts'])
			# Update the maximum timestamp
			max_ts=listen['date']['uts']
			# Get more info about the track
			track_params = {"method": "track.getInfo", "artist": listen['artist']["#text"], "track":listen['name'], "format":"json", "autocorrect":1}
			track_info = _last_fm_request(**track_params)
			# Get the track length
			length = track_info['track']['duration']

			# Get the tags (genre)
			try:
				tags = track_info['track']['toptags']['tag']
			except:
				# In the rare event there are no tags
				tags = []

			# Add data to the data structures
			total_listening_time += int(length)
			artist_dict.update({listen['artist']["#text"]: 1+ artist_dict.get(listen['artist']["#text"], 0)})
			song_dict.update({listen['name']: 1+song_dict.get(listen['name'], 0)})
			for tag_entry in tags:
				tag_dict.update({tag_entry['name']: 1+tag_dict.get(tag_entry['name'], 0)})
		# If we've reached the end of listens, exit
		if len(listens) < 100:
			break
	return artist_dict, song_dict, tag_dict, total_listening_time

def get_data_lastfm(username, period="7day"):
	"""
	Easy and quick way to get user data given last.fm generates aggregates
	"""
	print("Using last.fm fast mode!")
	# Setup required data
	last_network = LastFMNetwork(api_key=LAST_FM_API)
	last_user = User(username, last_network)

	# Get top artists
	top_artists = last_user.get_top_artists(period=period, limit=5)
	artist_dict = {i.item.get_name():i.weight for i in top_artists}

	# Get top tracks
	top_tracks = last_user.get_top_tracks(period=period, limit=50)
	song_dict = {i.item.get_correction():i.weight for i in top_tracks[:5]}

	# LastFM does not give the top listened tags - pylast also doesn't let me get this :(
	# Hack/workaround to get the time. THis will NOT be accurate!
	total_time = 0
	for track in top_tracks:
		total_time += track.item.get_duration() * track.weight
	return artist_dict, song_dict, {}, total_time
	

def get_data(username, source=0, time=None):
	"""
	Get data using the preferred source (0: lastfm, 1: listenbrainz)
	"""
	function = get_full_data_lastfm
	if source == 1:
		function = listen_brainz

	start_time = None
	end_time = None

	if time is None or time=='all':
		# Get history from all time
		pass
	elif time=="today":
		# Get history for last day
		start_time = datetime.date(datetime.now())
	elif time=="week":
		# Get history for last week
		start_time = datetime.date(datetime.now()) - timedelta(days=7)
	elif time[-1]=="d":
		# Get history for last x days
		days_to_sub = time[-1:]
		try:
			delta = int(days_to_sub)
		except:
			print("Invalid number of dates given!")
			exit(1)
		start_time = datetime.date(datetime.now()) - timedelta(days=delta)
	elif time=="1m":
		# Get history for previous calendar month
		now = datetime.now()
		if now.month == 1:
			start_time = datetime.date(datetime.combine(date(year=now.year-1, month=12, day=1), datetime.min.time()))
			end_time = datetime.date(datetime.combine(date(year=now.year, month=1, day=1), datetime.min.time()))
		else:
			start_time = datetime.date(datetime.combine(date(year=now.year, month=now.month-1, day=1), datetime.min.time()))
			end_time = datetime.date(datetime.combine(date(year=now.year, month=now.month, day=1), datetime.min.time()))
	elif time[-1]=="y":
		# Get history for last calendar year
		year_str = time[-1:]
		if len(year_str) != 4:
			print("You must specify a year in YYYY format!")
			exit(1)
		try:
			year = int(year_str)
		except:
			print("Invalid year given!")
			exit(1)
		now = datetime.now()
		start_time = date(year=year, month=1, day=1)
		end_time = date(year=year+1, month=1, day=1)
	else:
		print("Invalid time parameter given!")
		exit(1)

	return function(username, start_time=date_to_epoch(start_time),end_time=date_to_epoch(end_time))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Get aggregates like Spotify Wrapped from Last.FM/ListenBrainz.', formatter_class=argparse.MetavarTypeHelpFormatter)
	parser.add_argument('username', type=str, help='Last.FM/ListenBrainz username')
	parser.add_argument('--fast', dest="fast", help='Use last.fm generated aggregates for faster results. Only works for last 7 days', action="store_true")
	parser.add_argument('--listenbrainz', dest="listenbrainz", help='Use listenbrainz instead of last.fm', action="store_true")
	parser.add_argument('-t', '--time', type=str, help="Specify the timeframe. Defaults to all time, you can say 'today', 'week', 'xd' (where x is the number of previous days), '1m', 'xxxxy' (where xxxx is the calendar year), or 'all'")
	parser.add_argument('--output', type=str, help='Filename to output to')
	parser.add_argument('--input', type=str, help="Read a JSON file instead of getting the data from last.fm/listenbrainz")
	args = parser.parse_args()

	filename = "data.json"
	if args.listenbrainz and args.fast:
		print("Fast mode is incompatible with Listenbrainz!")
		exit(1)
	if args.time is not None and args.fast:
		print("Fast mode is incompatible with custom time frames!")
		exit(1)
	if (args.fast or args.listenbrainz or args.time) and args.input:
		print("You can't specify an input and fast/listenbrainz, or a time frame!")

	if args.input:
		artist_dict, song_dict, tag_dict, total_listening_time = read_file(args.input)
	else:
		# use Last.fm fast mode
		if args.fast:
			artist_dict, song_dict, tag_dict, total_listening_time = get_data_lastfm(args.username)
		else:
			# Set source to listenbrainz if listenbrainz is set
			source = 1 if args.listenbrainz else 0
			artist_dict, song_dict, tag_dict, total_listening_time = get_data(args.username, source=source, time=args.time)
	

	if args.output is not None:
		write_to_file(args.output, artist_dict, song_dict, tag_dict, total_listening_time)
	print_data(total_listening_time, artist_dict, song_dict, tag_dict)