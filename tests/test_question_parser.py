import unittest
from backend.app.services.question_parser import QuestionParser

class TestQuestionParser(unittest.TestCase):
    def setUp(self):
        self.parser = QuestionParser()

    def test_count_query(self):
        parsed = self.parser.parse("How many times did the machine stop?")
        self.assertTrue(parsed["is_count"])
        self.assertEqual(parsed["relation"], "COUNT")
        self.assertEqual(parsed["target_event"], "STOPPED")
        self.assertEqual(parsed["target_object"], "machine")

    def test_after_query(self):
        parsed = self.parser.parse("Who entered the restricted area after the delivery truck?")
        self.assertEqual(parsed["relation"], "AFTER")
        self.assertTrue(parsed["is_who"])
        self.assertEqual(parsed["target_object"], "truck")

    def test_immediately_before(self):
        parsed = self.parser.parse("What happened immediately before the alarm?")
        self.assertEqual(parsed["relation"], "IMMEDIATELY_BEFORE")
        self.assertEqual(parsed["target_event"], "ALARM")

    def test_between_query(self):
        parsed = self.parser.parse("What happened between 00:20 and 01:00?")
        self.assertEqual(parsed["relation"], "BETWEEN")
        self.assertEqual(parsed["time_range"], (20.0, 60.0))

if __name__ == "__main__":
    unittest.main()
