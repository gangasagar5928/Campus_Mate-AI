"""
test_interviewer_suite.py - Comprehensive Unit & Integration Test Suite.
Validates all technical responsibilities for Member 3:
1. Question bank integrity (Qualcomm, TCS Prime, Amazon, Tier-1 packs)
2. Structured LLM evaluation prompts and rubric scoring (0-10.0, score badge, strengths, risks, remedial topics)
3. Payment Protocol gating (1.0 testnet FET requirement, replay attack prevention)
4. End-to-End message flow between StudentTwinAgent and CompanyInterviewerAgent.
"""

import os
import sys
import json
import unittest

# Ensure safe UTF-8 output on all systems
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from payment_protocol import PaymentProtocol
from llm_evaluator import LLMEvaluator
from prompts import get_score_badge, SCORE_BADGES
from models import (
    InterviewQuery,
    InterviewQuestionResponse,
    InterviewAnswerSubmission,
    InterviewEvaluation
)
from agent_interviewer import serve_interview_query, evaluate_student_submission, find_question, INTERVIEW_BANK


class TestInterviewerAgentSuite(unittest.TestCase):
    def setUp(self):
        self.payment = PaymentProtocol(wallet_file="test_interviewer_wallet.json")
        self.evaluator = LLMEvaluator()

    def tearDown(self):
        # Clean up test wallet file if present
        if os.path.exists("test_interviewer_wallet.json"):
            try:
                os.remove("test_interviewer_wallet.json")
            except Exception:
                pass

    # --- 1. Question Bank Integrity Tests ---
    def test_01_question_bank_structure(self):
        """Verifies target company recruitment tracks exist with all required schema fields."""
        self.assertIn("qualcomm", INTERVIEW_BANK)
        self.assertIn("tcs_prime", INTERVIEW_BANK)
        self.assertIn("amazon", INTERVIEW_BANK)

        # Check Qualcomm Verilog blocking vs non-blocking
        qualcomm_questions = INTERVIEW_BANK["qualcomm"]["questions"]
        verilog_q = next((q for q in qualcomm_questions if "blocking" in q["topic"].lower()), None)
        self.assertIsNotNone(verilog_q, "Qualcomm must have Verilog blocking vs non-blocking question.")
        self.assertEqual(verilog_q["tier"], "standard")

        # Check Qualcomm Tier-1 Advanced Pack
        qualcomm_tier1 = next((q for q in qualcomm_questions if q["tier"] == "tier-1"), None)
        self.assertIsNotNone(qualcomm_tier1, "Qualcomm must have Tier-1 VLSI Advanced Pack.")
        self.assertEqual(qualcomm_tier1["fee_fet"], 1.0)

        # Check TCS Prime C++ pointers and memory management
        tcs_questions = INTERVIEW_BANK["tcs_prime"]["questions"]
        cpp_q = next((q for q in tcs_questions if "pointer" in q["topic"].lower()), None)
        self.assertIsNotNone(cpp_q, "TCS Prime must have C++ pointers/memory management question.")

        # Check Amazon Binary Search Trees and Bar Raiser Drill
        amazon_questions = INTERVIEW_BANK["amazon"]["questions"]
        bst_q = next((q for q in amazon_questions if "binary search tree" in q["topic"].lower()), None)
        self.assertIsNotNone(bst_q, "Amazon must have Binary Search Tree question.")

        bar_raiser_q = next((q for q in amazon_questions if q["tier"] == "tier-1"), None)
        self.assertIsNotNone(bar_raiser_q, "Amazon must have Tier-1 Bar Raiser Drill.")
        self.assertEqual(bar_raiser_q["fee_fet"], 1.0)

        # Check rubric fields on all questions
        for c_key, c_data in INTERVIEW_BANK.items():
            for q in c_data["questions"]:
                self.assertIn("expected_rubric", q)
                self.assertIn("must_include", q["expected_rubric"])
                self.assertIn("ideal_sample_answer", q)
                self.assertTrue(len(q["expected_rubric"]["must_include"]) >= 3)

    # --- 2. Evaluation Prompts & Grading Rubric Tests ---
    def test_02_score_badge_mapping(self):
        """Verifies score badge mapping for various grade brackets."""
        self.assertIn("Outstanding", get_score_badge(9.5))
        self.assertIn("Outstanding", get_score_badge(9.0))
        self.assertIn("Strong Pass", get_score_badge(8.2))
        self.assertIn("Strong Pass", get_score_badge(7.5))
        self.assertIn("Borderline", get_score_badge(6.8))
        self.assertIn("Borderline", get_score_badge(6.0))
        self.assertIn("Remediation", get_score_badge(4.5))
        self.assertIn("Remediation", get_score_badge(1.0))

    def test_03_evaluator_strong_answer(self):
        """Verifies that an exhaustive, high-depth answer receives a strong pass or outstanding score."""
        q_data = find_question("qualcomm", question_id="qualcomm_verilog_01")
        self.assertIsNotNone(q_data)

        # Evaluate ideal sample answer
        result = self.evaluator.evaluate_answer(q_data, q_data["ideal_sample_answer"])
        self.assertGreaterEqual(result["score"], 7.5)
        self.assertTrue(len(result["strengths"]) > 0)
        self.assertIn("rubric_breakdown", result)
        self.assertIn("technical_correctness", result["rubric_breakdown"])
        self.assertIn("score_badge", result)

    def test_04_evaluator_weak_answer(self):
        """Verifies that a vague or incorrect answer receives low score and remedial topics."""
        q_data = find_question("tcs_prime", question_id="tcs_prime_cpp_01")
        weak_answer = "Pointers point to memory. C++ uses malloc sometimes."

        result = self.evaluator.evaluate_answer(q_data, weak_answer)
        self.assertLess(result["score"], 6.0)
        self.assertIn("Remediation Needed", result["score_badge"])
        self.assertTrue(len(result["synthesis_risks"]) > 0)
        self.assertTrue(len(result["remedial_topics"]) > 0)

    # --- 3. Payment Protocol & Testnet FET Monetization Tests ---
    def test_05_tier1_locked_without_payment(self):
        """Verifies that requesting a Tier-1 pack without valid payment returns is_unlocked=False."""
        query = InterviewQuery(
            student_id="test_candidate",
            company="amazon",
            tier="tier-1",
            question_id="amazon_bar_raiser_01",
            payment_tx_hash=None
        )
        response = serve_interview_query(query, sender="test_suite")
        self.assertFalse(response.is_unlocked)
        self.assertEqual(response.required_fee_fet, 1.0)
        self.assertIn("LOCKED", response.question_text)
        self.assertIsNotNone(response.payment_instructions)

    def test_06_tier1_unlocked_with_valid_fet_transfer(self):
        """Verifies that a valid 1.0 FET testnet transfer unlocks the Tier-1 mock pack."""
        from agent_interviewer import payment_protocol as agent_pay
        sender = "fetch1test_candidate_wallet"
        tx_hash = agent_pay.simulate_transfer(sender, amount_fet=1.0, memo="Amazon Bar Raiser Drill")

        query = InterviewQuery(
            student_id="test_candidate",
            company="amazon",
            tier="tier-1",
            question_id="amazon_bar_raiser_01",
            payment_tx_hash=tx_hash
        )

        response = serve_interview_query(query, sender="test_suite")
        self.assertTrue(response.is_unlocked)
        self.assertIn("BAR RAISER", response.question_text)
        self.assertEqual(response.tier, "tier-1")

    def test_07_payment_protocol_replay_attack_prevention(self):
        """Verifies that reusing the same tx_hash is rejected as a Replay Attack."""
        tx_hash = self.payment.simulate_transfer("fetch1student_wallet_x", amount_fet=1.0)

        # First verification must succeed
        ok1, msg1, meta1 = self.payment.verify_payment(tx_hash, expected_min_fet=1.0, student_id="student_1")
        self.assertTrue(ok1)

        # Second verification with identical tx_hash must be blocked
        ok2, msg2, meta2 = self.payment.verify_payment(tx_hash, expected_min_fet=1.0, student_id="student_2")
        self.assertFalse(ok2)
        self.assertIn("Replay Attack Detected", msg2)

    # --- 4. End-to-End Workflow Test ---
    def test_08_end_to_end_query_submission_evaluation(self):
        """Tests complete query -> response -> submission -> evaluation badge lifecycle."""
        # Step 1: Query standard question
        query = InterviewQuery(
            student_id="twin_007",
            company="qualcomm",
            tier="standard",
            question_id="qualcomm_verilog_01"
        )
        resp = serve_interview_query(query, sender="student_twin_agent")
        self.assertTrue(resp.is_unlocked)
        self.assertEqual(resp.company, "Qualcomm")

        # Step 2: Candidate submits answer
        submission = InterviewAnswerSubmission(
            session_id=resp.session_id,
            question_id=resp.question_id,
            student_id="twin_007",
            student_answer=(
                "In Verilog, blocking assignments (=) execute sequentially and evaluate immediately in the active region. "
                "Non-blocking assignments (<=) evaluate in the active region and schedule updates in the NBA region. "
                "Sequential logic always @(posedge clk) must use non-blocking (<=) to prevent race conditions across flip flops. "
                "Combinational always @(*) blocks should use blocking (=) to ensure immediate signal update and prevent latches."
            )
        )

        # Step 3: Interviewer Agent evaluates and produces score badge
        evaluation = evaluate_student_submission(submission)
        self.assertIsInstance(evaluation, InterviewEvaluation)
        self.assertEqual(evaluation.session_id, resp.session_id)
        self.assertEqual(evaluation.question_id, "qualcomm_verilog_01")
        self.assertGreater(evaluation.score, 6.5)
        self.assertTrue(any("blocking" in s.lower() or "nba" in s.lower() or "active" in s.lower() for s in evaluation.strengths))
        self.assertTrue(len(evaluation.remedial_topics) > 0)


if __name__ == "__main__":
    unittest.main()
