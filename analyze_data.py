def write_html(title, minutes_listened, artists, songs):
	f = open('report.html', 'w')
	print("""<!DOCTYPE html><html><head><title>Wrapped</title><style type="text/css">body{background-color: #f58d15;}.center-div{position: absolute; margin: auto; top: 0; right: 0; bottom: 0; left: 0; width: 50%; height: 90%; background-color: #503651; border-radius: 3px; padding: 10px;}.play_logo{width: 7%;position: relative;top: 30px;left: 50px;}.title_logo{width: 30%;position: relative;top: 30px;left: 50px;}.right_title{position: absolute;font-family: "Product Sans";top: 55px;right: 10%;font-size: 2em;color: #f2481d;}.container{position: relative;top: 13%;left: 53px;}.minutes_title{font-family: "Product Sans";font-size: 2em;color: #f58d15;}.minutes{font-family: "Product Sans";font-size: 6em;color: #f58d15;}.row{display: flex;}.column{flex: 50%;}.list{font-family: "Roboto";font-size: 1.5em;line-height: 30px;color: #f58d15;}</style></head><body><div class="center-div"><img src="play_logo.png" class="play_logo"><img src="title.png" class="title_logo"/><span class="right_title">""", file=f)
	print(title, file=f)
	print (""" Wrapped</span><div class="container"><div class="minutes_title">Minutes Listened</div><div class="minutes">""", file=f)
	print(minutes_listened, file=f)
	print ("""</div><br><br><div class="row"><div class="column"><div class="minutes_title">Top Artists</div><div class="list">""", file=f)
	for artist in artists:
		print ("<br>", file=f)
		print('{0}'.format(artist[0]), file=f)
	print ("""</div></div><div class="column"><div class="minutes_title">Top Songs</div><div class="list">""", file=f)
	for song in songs:
		print ("<br>", file=f)
		print ('{0}'.format(song[0]), file=f)
	print ("""</div></div></div></div></div></body></html>""", file=f)
	f.close()


def print_data(lengh_in_ms, artist_dict, song_dict, tag_dict):
	"""
	Aim for a Spotify wrapped themed info dump. Prettyfying the data comes later

    Params:
    length_in_ms: Total listening time in milliseconds
    artist_dict: {artist:num_listens}
    song_dict: {song:num_listens}
    tag_dict: {tag:num_matches}

	Spotify displays the following:
	[x] Minutes spent listening
	[ ] Top song (most played), artist of the song, number of times song was played
	[x] Top 5 songs [We also show number of times each song was played]
	[ ] Playlist with your top 100 songs
	[ ] "Audio aura" - music moods [Not entirely sure what this is]
	[x] Number of genres listened to
	[x] Top 5 genres [We also show number of times each genre was counted]
	[x] Total number of unique artists
	[ ] Top Artist (most played), Minutes listened to this artist, top song by artist
	[x] Top 5 artists [We also show number of plays of each of these artists]

	In addition we show
	- Total number of songs listened to
	- Total number of unique songs listened to
	"""
	seconds = lengh_in_ms // 1000
	total_minutes = seconds // 60
	seconds = seconds % 60
	hours = total_minutes // 60
	minutes = total_minutes % 60
	print("{} Hours, {} Minutes, {} Seconds ({} Minutes)".format(hours, minutes, seconds, total_minutes))

	if artist_dict is not None:
		artist_list = [i for i in reversed([(k,v) for k,v in sorted(artist_dict.items(), key=lambda item:item[1])])]
		print("Listened to {} different artists".format(len(artist_list)))
		print(artist_list[:5])

	if song_dict is not None:
		song_list = [i for i in reversed([(k,v) for k,v in sorted(song_dict.items(), key=lambda item:item[1])])]
		print("Listened to {} songs, of which {} were unique".format(sum(n for _,n in song_list), len(song_list)))
		print(song_list[:5])

	if tag_dict is not None:
		genre_list = [i for i in reversed([(k,v) for k,v in sorted(tag_dict.items(), key=lambda item:item[1])])]
		if len(genre_list) != 0:
			print("Listened to {} different genres".format(len(genre_list)))
			print(genre_list[:5])

	write_html("Week", total_minutes, artist_list[:5], song_list[:5])