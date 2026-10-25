"""
llm_evaluator.py - LLM Evaluation Engine for Company Technical Drills.
Handles prompt synthesis, LLM API calls (Gemini/OpenAI/OmniRoute), JSON response validation,
and a deterministic semantic rubric fallback for reliable testing and offline evaluation.
"""

import os
import json
import re
import requests
from typing import Dict, Any, List, Optional
try:
    from core.prompts import (
        EVALUATION_SYSTEM_PROMPT,
        EVALUATION_USER_TEMPLATE,
        get_score_badge,
        SCORE_BADGES
    )
except ImportError:
    from prompts import (
        EVALUATION_SYSTEM_PROMPT,
        EVALUATION_USER_TEMPLATE,
        get_score_badge,
        SCORE_BADGES
    )


class LLMEvaluator:
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        omniroute_url: Optional[str] = None,
        model_name: str = "gemini-1.5-flash"
    ):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.omniroute_url = omniroute_url or os.getenv("OMNIROUTE_URL")
        self.model_name = model_name

    def evaluate_answer(
        self,
        question_data: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """
        Main entry point to evaluate a candidate's answer against the target company's question rubric.
        Returns a structured dictionary with score, score_badge, strengths, synthesis_risks, and remedial_topics.
        """
        # Format checkpoints for the prompt
        rubric = question_data.get("expected_rubric", {})
        must_include_str = "\n".join(f"- {item}" for item in rubric.get("must_include", []))
        bonus_points_str = "\n".join(f"- {item}" for item in rubric.get("bonus_points", []))
        pitfalls_str = "\n".join(f"- {item}" for item in rubric.get("common_pitfalls", []))

        user_prompt = EVALUATION_USER_TEMPLATE.format(
            company=question_data.get("company", "Tech Company"),
            track=question_data.get("track", "Engineering"),
            tier=question_data.get("tier", "standard").upper(),
            topic=question_data.get("topic", "System Concepts"),
            difficulty=question_data.get("difficulty", "Medium"),
            question=question_data.get("question", ""),
            must_include=must_include_str or "Standard technical correctness.",
            bonus_points=bonus_points_str or "Advanced optimization and deep mechanics.",
            pitfalls_str=pitfalls_str or "Vagueness or inaccuracies.",
            common_pitfalls=pitfalls_str or "Vagueness or inaccuracies.",
            ideal_sample_answer=question_data.get("ideal_sample_answer", "N/A"),
            student_answer=student_answer.strip()
        )

        # Attempt API evaluation if keys or gateway are configured
        llm_response = None
        if self.omniroute_url:
            llm_response = self._call_omniroute(user_prompt)
        elif self.gemini_api_key:
            llm_response = self._call_gemini(user_prompt)
        elif self.openai_api_key:
            llm_response = self._call_openai(user_prompt)

        # If LLM returned a valid response, parse and validate it
        if llm_response:
            parsed = self._extract_and_validate_json(llm_response)
            if parsed:
                # Ensure score badge is synchronized with numerical score
                parsed["score_badge"] = get_score_badge(parsed["score"])
                return parsed

        # Otherwise, fall back to high-fidelity deterministic semantic evaluator
        return self._evaluate_with_rubric_engine(question_data, student_answer)

    def _call_gemini(self, user_prompt: str) -> Optional[str]:
        """Calls Google Gemini API."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.gemini_api_key}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"{EVALUATION_SYSTEM_PROMPT}\n\n{user_prompt}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
        except Exception as e:
            print(f"[LLMEvaluator] Gemini API error: {e}")
        return None

    def _call_openai(self, user_prompt: str) -> Optional[str]:
        """Calls OpenAI / compatible Chat Completion API."""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLMEvaluator] OpenAI API error: {e}")
        return None

    def _call_omniroute(self, user_prompt: str) -> Optional[str]:
        """Calls local OmniRoute gateway router."""
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2
            }
            resp = requests.post(f"{self.omniroute_url}/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLMEvaluator] OmniRoute call error: {e}")
        return None

    def _extract_and_validate_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON object from response string."""
        try:
            # Strip markdown fences if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned)
                cleaned = re.sub(r"\n?```$", "", cleaned)
            data = json.loads(cleaned)

            # Validate required fields
            if "score" in data and "strengths" in data and "synthesis_risks" in data:
                data["score"] = round(float(data["score"]), 1)
                data["score"] = max(0.0, min(10.0, data["score"]))
                return data
        except Exception:
            pass
        return None

    def _evaluate_with_rubric_engine(
        self,
        question_data: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """
        High-fidelity semantic grading engine for deterministic offline evaluation.
        Verifies answer length, concept coverage, must-include keywords, and detects common pitfalls.
        """
        ans_lower = student_answer.lower()
        rubric = question_data.get("expected_rubric", {})
        must_includes = rubric.get("must_include", [])
        bonus_points = rubric.get("bonus_points", [])
        pitfalls = rubric.get("common_pitfalls", [])

        # Check keyword matches
        covered_points = []
        missed_points = []
        for checkpoint in must_includes:
            # extract key identifiers from checkpoint string
            keywords = [w.lower().strip("(),.:;\"'`$") for w in checkpoint.split() if len(w) > 4]
            # test if at least half of the key words appear or distinctive phrases
            matches = sum(1 for kw in keywords if kw in ans_lower)
            if matches >= max(1, len(keywords) // 2):
                covered_points.append(checkpoint)
            else:
                missed_points.append(checkpoint)

        covered_bonus = []
        for bonus in bonus_points:
            b_keywords = [w.lower().strip("(),.:;\"'`$") for w in bonus.split() if len(w) > 4]
            matches = sum(1 for kw in b_keywords if kw in ans_lower)
            if matches >= max(1, len(b_keywords) // 2):
                covered_bonus.append(bonus)

        triggered_pitfalls = []
        for pitfall in pitfalls:
            p_keywords = [w.lower().strip("(),.:;\"'`$") for w in pitfall.split() if len(w) > 4]
            matches = sum(1 for kw in p_keywords if kw in ans_lower)
            if matches >= max(2, len(p_keywords) // 2):
                triggered_pitfalls.append(pitfall)

        # Baseline Scoring calculations
        total_must = max(1, len(must_includes))
        must_ratio = len(covered_points) / total_must
        word_count = len(student_answer.split())

        # Sub-score calculations
        tech_score = round(min(4.0, must_ratio * 4.0), 1)
        depth_score = round(min(3.0, (word_count / 140.0) * 2.0 + (len(covered_bonus) * 0.5)), 1)
        edge_score = round(max(0.0, 2.0 - (len(triggered_pitfalls) * 0.8)), 1)
        clarity_score = round(min(1.0, 0.4 + (0.6 if word_count >= 50 else (word_count / 50.0) * 0.6)), 1)

        total_score = round(tech_score + depth_score + edge_score + clarity_score, 1)
        total_score = max(1.5, min(10.0, total_score))

        # Build strengths
        strengths = []
        if covered_points:
            for p in covered_points[:3]:
                strengths.append(f"Accurately addressed: {p}")
        else:
            strengths.append("Attempted the question with initial structural thoughts.")

        if covered_bonus:
            strengths.append(f"Demonstrated advanced depth: {covered_bonus[0]}")

        # Build synthesis risks
        synthesis_risks = []
        if missed_points:
            for m in missed_points[:2]:
                synthesis_risks.append(f"Omission / Partial Depth: Missed critical analysis on '{m}'")
        if triggered_pitfalls:
            for pf in triggered_pitfalls[:2]:
                synthesis_risks.append(f"Critical Technical Pitfall: Risk associated with '{pf}'")
        if word_count < 60:
            synthesis_risks.append("Brevity Risk: Explanation is too brief to demonstrate full engineering mastery.")
        if not synthesis_risks:
            synthesis_risks.append("Minor: Could elaborate further on empirical benchmarks or hardware telemetry.")

        # Remedial topics
        remedial_topics = []
        topic = question_data.get("topic", "System Design")
        if missed_points:
            for m in missed_points[:3]:
                remedial_topics.append(f"Review: {m}")
        else:
            remedial_topics.append(f"Mastery Drills on {topic} edge cases and architectural variations.")
            remedial_topics.append("Production profiling, memory barrier analysis, and concurrency stress tests.")

        badge = get_score_badge(total_score)

        feedback_summary = (
            f"Candidate achieved a score of {total_score}/10.0 ({badge}). "
            f"Demonstrated solid grasp of {len(covered_points)} key rubric requirements. "
            f"Identified {len(synthesis_risks)} synthesis risks requiring targeted study prior to technical interviews."
        )

        return {
            "score": total_score,
            "score_badge": badge,
            "rubric_breakdown": {
                "technical_correctness": tech_score,
                "depth_and_mechanics": depth_score,
                "edge_cases_and_risks": edge_score,
                "clarity_and_precision": clarity_score
            },
            "strengths": strengths,
            "synthesis_risks": synthesis_risks,
            "remedial_topics": remedial_topics,
            "feedback_summary": feedback_summary
        }
