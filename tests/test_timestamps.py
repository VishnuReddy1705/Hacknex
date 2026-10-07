import unittest
from backend.app.utils.timestamps import seconds_to_timestamp, timestamp_to_seconds, format_duration_str

class TestTimestamps(unittest.TestCase):
    def test_seconds_to_timestamp(self):
        self.assertEqual(seconds_to_timestamp(0), "00:00")
        self.assertEqual(seconds_to_timestamp(27), "00:27")
        self.assertEqual(seconds_to_timestamp(130), "02:10")
        self.assertEqual(seconds_to_timestamp(3665), "01:01:05")

    def test_timestamp_to_seconds(self):
        self.assertEqual(timestamp_to_seconds("00:27"), 27.0)
        self.assertEqual(timestamp_to_seconds("02:10"), 130.0)
        self.assertEqual(timestamp_to_seconds("01:01:05"), 3665.0)

    def test_format_duration_str(self):
        self.assertEqual(format_duration_str(15), "15s")
        self.assertEqual(format_duration_str(130), "2m 10s")

if __name__ == "__main__":
    unittest.main()
