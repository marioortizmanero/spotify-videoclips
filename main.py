#! /usr/bin/pn
import os
from datetime import datetime

from libs import vlc
from libs import youtube
from libs import spotify


# Dictionary with previous downloads to not repeat
videos = {}


# Plays the video until a new song is found
def main(artist, title):
    name = spotify.format_name(artist, title)
    
    # Counts seconds to add a delay and sync the start
    start_time = datetime.now()
    # Only downloading the video if it's not listed
    if name not in videos:
        filename = youtube.download_video(name)
        videos[name] = filename
    else:
        filename = videos[name]

    offset = int((datetime.now() - start_time).microseconds / 1000)
    vlc.play_video(filename, offset)
    spotify.get_lyrics(artist, title)

    # Waiting for the song to finish
    while True:
        artist, title = spotify.get_name()
        new_name = spotify.format_name(artist, title)
        if new_name != name:
            break
    main(artist, title)


if __name__ == '__main__':
    artist, title = spotify.get_name()
    try:
        main(artist, title)
    except KeyboardInterrupt:
        print("\n>> Removing cache...")
        os.system("rm downloads/*")
        exit()

