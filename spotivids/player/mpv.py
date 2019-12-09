"""
This module is a generic implementation of the video player used in the
program. It must have the same usage, functionality and behavior as the
default player, VLC.

Mpv is a good alternative to VLC because it's relatively lightweight and
straightforward, but it's mostly used only on Linux systems.
"""

import logging
from typing import Optional

try:
    from mpv import MPV
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "No module named 'mpv'.\nTo use this player, please install spotivids"
        " along with python-mpv. Please read the installation guide for more"
        " details.") from None
from PySide2.QtWidgets import QFrame


class MpvPlayer(QFrame):
    def __init__(self, flags: Optional[str] = None) -> None:
        """
        It inherits from a QFrame so that it can be directly added as a widget
        in the Qt GUI.
        """

        super().__init__()

        # Converting the flags passed by parameter (str) to a tuple
        flags = flags.split() if flags not in (None, '') else []
        # The audio is always muted, which is needed because not all the
        # youtube-dl videos are silent. The keep-open flag stops mpv from
        # closing after the video is over.
        flags.extend(['mute', 'keep-open'])

        args = {}
        if logging.root.level <= logging.INFO:
            args['log_handler'] = print
            args['loglevel'] = 'info'
        args['wid'] = str(int(self.winId()))

        self._mpv = MPV(*flags, **args)

    def __del__(self) -> None:
        try:
            self._mpv.terminate()
        except AttributeError:
            pass

    @property
    def pause(self) -> bool:
        return self._mpv.pause

    @pause.setter
    def pause(self, do_pause: bool) -> None:
        """
        The video will be paused if `do_pause` is true.
        """

        logging.info("Playing/Pausing video")
        self._mpv.pause = do_pause

    @property
    def position(self) -> int:
        """
        Getting the position of the VLC player in milliseconds
        """

        time = self._mpv.playback_time
        return time if time is not None else 0

    @position.setter
    def position(self, ms: int) -> None:
        """
        Setting the position in milliseconds. Unlike VLC, mpv will throw an
        error if the position is changed before the video starts, so
        this waits for 'seekable' to be set to True.
        """

        self._mpv.wait_for_property('seekable')
        logging.info(f"Time set to {ms} milliseconds")
        self._mpv.seek(ms / 1000, reference='absolute')

    def start_video(self, url: str, is_playing: bool = True) -> None:
        """
        Starts a new video in the mpv player. It can be directly played or
        paused with `is_playing` to avoid extra calls.
        """

        logging.info(f"Started new video")
        self._mpv.play(url)
        # Mpv starts automatically playing the video
        if not is_playing:
            self.pause = True
