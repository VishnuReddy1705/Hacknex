import unittest
from backend.app.database import SessionLocal
from backend.app.services.question_parser import QuestionParser
from backend.app.services.evidence_retriever import EvidenceRetriever
from backend.app.services.answer_generator import AnswerGenerator

class TestQAPipeline(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.video_id = "timesense_demo_cctv"
        self.parser = QuestionParser()
        self.retriever = EvidenceRetriever(db=self.db, video_id=self.video_id)
        self.generator = AnswerGenerator()

    def tearDown(self):
        self.db.close()

    def test_who_entered_after_truck(self):
        q = "Who entered the restricted area after the truck arrived?"
        parsed = self.parser.parse(q)
        retrieved = self.retriever.retrieve(parsed)
        ans = self.generator.generate(parsed, retrieved)

        self.assertIn("00:27", ans.timestamps)
        self.assertIn("00:12", ans.timestamps)
        self.assertIn("P01", ans.answer)
        self.assertGreater(len(ans.evidence), 0)

    def test_machine_stop_count(self):
        q = "How many times did the machine stop?"
        parsed = self.parser.parse(q)
        retrieved = self.retriever.retrieve(parsed)
        ans = self.generator.generate(parsed, retrieved)

        self.assertIn("2 times", ans.answer)
        self.assertIn("02:10", ans.timestamps)
        self.assertIn("03:10", ans.timestamps)

    def test_what_happened_immediately_before_alarm(self):
        q = "What happened immediately before the alarm?"
        parsed = self.parser.parse(q)
        retrieved = self.retriever.retrieve(parsed)
        ans = self.generator.generate(parsed, retrieved)

        self.assertIn("00:47", ans.timestamps)
        self.assertIn("00:35", ans.timestamps)
        self.assertIn("P01", ans.answer)

    def test_first_event(self):
        q = "What happened first?"
        parsed = self.parser.parse(q)
        retrieved = self.retriever.retrieve(parsed)
        ans = self.generator.generate(parsed, retrieved)

        self.assertIn("00:05", ans.timestamps)
        self.assertIn("truck", ans.answer.lower())

if __name__ == "__main__":
    unittest.main()
