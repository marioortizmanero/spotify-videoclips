import time
import platform
import logging
from typing import Callable, Union

import youtube_dl
import lyricwikia

from .config import Config
from .utils import stderr_redirected, ConnectionNotReady


config = Config()
config.parse()

# Logger initialzation with precise milliseconds handler
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s.%(msecs)03d] "
                              "%(levelname)s: %(message)s", datefmt="%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Youtube-dl config
ydl_opts = {
    'format': 'bestvideo',
    'quiet': True
}

if config.max_width is not None:
    ydl_opts['format'] += f"[width<={config.max_width}]"

if config.max_height is not None:
    ydl_opts['format'] += f"[height<={config.max_height}]"

# Can't append to a string if the config file has an empty field for it
if config.vlc_args is None:
    config.vlc_args = ""

if config.debug:
    logger.setLevel(logging.DEBUG)
    config.vlc_args += " --verbose 1"
    ydl_opts['quiet'] = False
else:
    logger.setLevel(logging.ERROR)
    config.vlc_args += " --quiet"


def format_name(artist: str, title: str) -> str:
    """
    Some local songs may not have an artist name so the formatting
    has to be different.
    """

    if artist in (None, ""):
        return f"{title}"
    else:
        return f"{artist} - {title}"


def get_url(artist: str, title: str) -> str:
    """
    Getting the youtube direct link to play it directly with VLC.
    """

    name = f"ytsearch:'{format_name(artist, title)} Official Video'"

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(name, download=False)

    return info['entries'][0]['url']


def print_lyrics(artist: str, title: str) -> None:
    """
    Using lyricwikia to get lyrics.

    Colors are not displayed on Windows because it doesn't support ANSI
    escape codes and importing colorama isn't worth it currently.
    """

    name = format_name(artist, title)

    if platform.system() == 'Windows':
        print(f">> {name}")
    else:
        print(f"\033[4m{name}\033[0m")

    try:
        print(lyricwikia.get_lyrics(artist, title) + "\n")
    except (lyricwikia.LyricsNotFound, AttributeError):
        print("No lyrics found\n")


def play_videos_linux(player: Union['VLCPlayer', 'MpvPlayer']) -> None:
    """
    Playing videos with the DBus API (Linux).

    Spotify doesn't currently support the MPRIS property `Position`
    so the starting offset is calculated manually and may be a bit rough.

    After playing the video, the player waits for DBus events like
    pausing the video.
    """

    from .api.linux import DBusAPI
    spotify = DBusAPI(player, logger)

    msg = "Waiting for a Spotify session to be ready..."

    if not wait_for_connection(spotify.connect, msg):
        return

    while True:
        start_time = time.time()

        url = get_url(spotify.artist, spotify.title)
        is_playing = spotify.is_playing
        player.start_video(url, is_playing)

        # Waits until VLC actually plays the video to set the offset
        if is_playing:
            while player.position == 0:
                pass
            offset = int((time.time() - start_time) * 1000)
            player.position = offset
            logging.debug(f"Starting offset is {offset}")

        if config.lyrics:
            print_lyrics(spotify.artist, spotify.title)

        spotify.wait()


def play_videos_swspotify(player: Union['VLCPlayer', 'MpvPlayer']) -> None:
    """
    Playing videos with the SwSpotify API.

    It's really basic and can only get the window title.
    """

    from .api.swspotify import SwSpotifyAPI
    spotify = SwSpotifyAPI(logger)

    msg = "Waiting for a Spotify session to be ready..."
    if not wait_for_connection(spotify.connect, msg):
        return

    while True:
        url = get_url(spotify.artist, spotify.title)
        player.start_video(url)

        if config.lyrics:
            print_lyrics(spotify.artist, spotify.title)

        spotify.wait()


def play_videos_web(player: Union['VLCPlayer', 'MpvPlayer']) -> None:
    """
    Playing videos with the Web API (macOS, Windows).

    Unlike the DBus API, the position can be requested and synced easily.
    """

    from .api.web import WebAPI
    spotify = WebAPI(player, logger, config.client_id,
                     config.client_secret, config.redirect_uri,
                     config.auth_token)

    msg = "Waiting for a Spotify song to play..."
    if not wait_for_connection(spotify.connect, msg):
        return

    # Saves the auth token inside the config file for future usage
    config.write_config_file('auth_token', spotify._token)

    while True:
        url = get_url(spotify.artist, spotify.title)
        player.start_video(url, spotify.is_playing)

        offset = spotify.position
        player.position = offset

        if config.lyrics:
            print_lyrics(spotify.artist, spotify.title)

        spotify.wait()


def wait_for_connection(connect: Callable, msg: str,
                        attempts: int = 30) -> bool:
    """
    Waits for a Spotify session to be opened or for a song to play.
    Times out after <attempts> seconds to avoid infinite loops and to
    avoid too many API/process requests.

    Returns True if the connect was succesfull and False otherwise.
    """

    counter = 0
    while counter < attempts:
        try:
            connect()
        except ConnectionNotReady:
            if counter == 0:
                print(msg)
            counter += 1
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        else:
            return True
    else:
        print("Timed out")

    return False


def choose_platform() -> None:
    """
    Chooses a platform and player and starts the corresponding API function.
    """

    if config.use_mpv:
        from .player.mpv import MpvPlayer
        player = MpvPlayer(logger, config.mpv_flags, config.fullscreen)
    else:
        from .player.vlc import VLCPlayer
        player = VLCPlayer(logger, config.vlc_args, config.fullscreen)

    if config.use_web_api:
        play_videos_web(player)
    elif platform.system() == 'Linux':
        play_videos_linux(player)
    elif platform.system() in ('Windows', 'Darwin'):
        play_videos_swspotify(player)


def main() -> None:
    """
    Redirects stderr to /dev/null if debug is turned off, since
    sometimes VLC will throw non-fatal errors even when configured
    to be quiet.
    """

    if config.debug:
        choose_platform()
    else:
        with stderr_redirected():
            choose_platform()


if __name__ == '__main__':
    main()
