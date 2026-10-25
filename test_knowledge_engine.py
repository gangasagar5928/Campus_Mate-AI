import unittest
from agent_student_twin import (
    match_query,
    format_subject_markdown,
    format_topic_markdown,
    format_interview_concept_markdown,
    format_balancing_strategy_markdown,
    format_branches_coverage_markdown,
    format_company_guide_markdown,
    format_web3_guide_markdown,
    format_exam_strategy_markdown,
    format_remedial_hook_markdown,
    format_profile_status_markdown,
    SessionState
)

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

    def test_balancing_strategy_format(self):
        md = format_balancing_strategy_markdown()
        self.assertIn("Dynamic Load-Balancing Algorithm", md)
        self.assertIn("60% Placement Prep", md)
        self.assertIn("10% Placement Prep", md)

    def test_branches_coverage_format(self):
        md = format_branches_coverage_markdown()
        self.assertIn("ECE", md)
        self.assertIn("CSE", md)
        self.assertIn("MECH", md)

    def test_company_guide_format(self):
        for comp in ["Qualcomm", "Google", "Nvidia", "Amazon", "Microsoft", "TCS Prime"]:
            md = format_company_guide_markdown(comp)
            self.assertIn(comp, md)
            self.assertIn("Recruitment Preparation Guide", md)

    def test_web3_guide_format(self):
        md = format_web3_guide_markdown()
        self.assertIn("Fetch.ai CosmPy Dorado", md)
        self.assertIn("1.0 FET", md)

    def test_exam_strategy_format(self):
        md = format_exam_strategy_markdown()
        self.assertIn("AKTU Sessional & University Exam Excellence Guide", md)
        self.assertIn("High-Yield", md)

    def test_remedial_hook_format(self):
        md = format_remedial_hook_markdown()
        self.assertIn("Evening Remedial Mutation Hook", md)
        self.assertIn("6.0 / 10.0", md)

    def test_profile_status_format(self):
        sess = SessionState("test_sender")
        md = format_profile_status_markdown(sess)
        self.assertIn("Active Student Twin Profile", md)
        self.assertIn("ECE", md)

if __name__ == "__main__":
    unittest.main()
