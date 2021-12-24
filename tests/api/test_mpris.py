import os
import unittest

from qtpy.QtWidgets import QApplication

from vidify import CUR_PLATFORM, Platform

if QApplication.instance() is None:
    _ = QApplication(["vidify"])
CI = "CI" in os.environ and os.environ["CI"] == "true"
SKIP_MSG = "Skipping this test as it won't work on the current system."


class MPRISTest(unittest.TestCase):
    @unittest.skipIf(CI or CUR_PLATFORM not in (Platform.BSD, Platform.LINUX), SKIP_MSG)
    def test_simple(self):
        from vidify.api.mpris import MPRISAPI

        api = MPRISAPI()
        api.connect_api()
        api._refresh_metadata()

    @unittest.skipIf(CUR_PLATFORM not in (Platform.BSD, Platform.LINUX), SKIP_MSG)
    def test_bool_status(self):
        from vidify.api.mpris import MPRISAPI

        self.assertFalse(MPRISAPI._bool_status("stopped"))
        self.assertFalse(MPRISAPI._bool_status("sToPPeD"))
        self.assertFalse(MPRISAPI._bool_status("paused"))
        self.assertFalse(MPRISAPI._bool_status("paUsEd"))
        self.assertTrue(MPRISAPI._bool_status("playing"))
        self.assertTrue(MPRISAPI._bool_status("Playing"))


if __name__ == "__main__":
    unittest.main()
