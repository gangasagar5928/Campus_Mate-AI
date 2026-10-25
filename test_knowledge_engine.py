import unittest
from agent_student_twin import match_query, format_subject_markdown, format_topic_markdown, format_interview_concept_markdown

class TestKnowledgeEngine(unittest.TestCase):
    def test_subject_code_match(self):
        res = match_query("What is KEC-601?")
        self.assertEqual(res["type"], "SUBJECT")
        self.assertEqual(res["data"]["subject_code"], "KEC-601")
        self.assertEqual(res["branch"], "ECE")

    def test_cse_subject_code_match(self):
        res = match_query("Tell me about KCS-502")
        self.assertEqual(res["type"], "SUBJECT")
        self.assertEqual(res["data"]["subject_code"], "KCS-502")
        self.assertEqual(res["branch"], "CSE")

    def test_topic_match(self):
        res = match_query("Explain Pulse Modulation")
        self.assertIn(res["type"], ("CURRICULUM_UNIT", "CURRICULUM_TOPIC"))
        self.assertEqual(res["subject"]["subject_code"], "KEC-601")

    def test_interview_concept_match(self):
        res = match_query("Explain setup and hold time in Qualcomm")
        self.assertEqual(res["type"], "INTERVIEW_QUESTION")
        self.assertEqual(res["data"]["company"], "Qualcomm")
        self.assertIn("Setup and Hold Time", res["data"]["topic"])

    def test_nvidia_warp_match(self):
        res = match_query("What is warp divergence in Nvidia?")
        self.assertEqual(res["type"], "INTERVIEW_QUESTION")
        self.assertEqual(res["data"]["company"], "Nvidia")

    def test_google_sharding_match(self):
        res = match_query("What is consistent hashing?")
        self.assertEqual(res["type"], "INTERVIEW_QUESTION")
        self.assertEqual(res["data"]["company"], "Google")

if __name__ == "__main__":
    unittest.main()
