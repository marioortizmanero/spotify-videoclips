import os
import unittest
import unittest.mock

from qtpy.QtWidgets import QApplication

if QApplication.instance() is None:
    _ = QApplication(["vidify"])
CI = "CI" in os.environ and os.environ["CI"] == "true"
SKIP_MSG = "Skipping this test as it won't work on the current system."


class SpotifyWebTest(unittest.TestCase):
    @unittest.skipIf(CI, SKIP_MSG)
    def test_simple(self):
        """
        The web credentials have to be already in the config file, including
        the auth token and the expiration date.
        """

        from vidify.api.spotify.web import SpotifyWebAPI, get_token
        from vidify.config import Config

        config = Config()
        with unittest.mock.patch("sys.argv", [""]):
            config.parse()
        token = get_token(config.refresh_token, config.client_id, config.client_secret)
        api = SpotifyWebAPI(token)
        api.connect_api()
        api._refresh_metadata()
        api.event_loop()


if __name__ == "__main__":
    unittest.main()
