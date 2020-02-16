"""
This module chooses the player and platform and starts them. The Qt GUI is
also initialized here.
"""

import os
import sys
import logging

from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QIcon
import qdarkstyle

from vidify.config import Config
from vidify.gui import set_dark_mode, Res
from vidify.gui.window import MainWindow


def start_gui(config: Config) -> None:
    """
    Initializing the Qt application. MainWindow takes care of initializing
    the player and the API, and acts as the "main function" where everything
    is put together.
    """

    app = QApplication(['vidify'])
    # Setting dark mode if enabled
    if config.dark_mode:
        logging.info("Enabling dark mode")
        app.setStyleSheet(qdarkstyle.load_stylesheet_from_environment())
        set_dark_mode()
    app.setWindowIcon(QIcon(Res.icon))
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec_())


def main() -> None:
    # Initialization and parsing of the config from arguments and config file
    config = Config()
    config.parse()

    # Logger initialzation with precise milliseconds handler.
    logging.basicConfig(level=logging.DEBUG if config.debug else logging.ERROR,
                        format="[%(asctime)s.%(msecs)03d] %(levelname)s:"
                        " %(message)s", datefmt="%H:%M:%S")

    # Redirecting stderr to /dev/null if debug is turned off, since sometimes
    # VLC will print non-fatal errors even when configured to be quiet.
    # This could be redirected to a log file in the future, along with any
    # other output from the logging module.
    if not config.debug:
        null_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null_fd, sys.stderr.fileno())

    start_gui(config)


if __name__ == '__main__':
    main()
