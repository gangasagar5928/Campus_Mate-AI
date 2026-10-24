"""
prompts.py - Structured LLM Evaluation Prompts & Grading Rubrics for Company Interview Drills.
"""
from typing import Dict, List, Any

SCORE_BADGES = {
    "outstanding": {"min_score": 9.0, "badge": "🏆 Outstanding - Interviewer Strong Hire (9.0 - 10.0)", "level": "Tier-1 Production Ready / Lead Caliber", "verdict": "STRONG_HIRE"},
    "strong_pass": {"min_score": 7.5, "badge": "✅ Strong Pass - Recommended for Next Round (7.5 - 8.9)", "level": "Solid Core Competence / Minor Nuances Missed", "verdict": "HIRE"},
    "borderline": {"min_score": 6.0, "badge": "⚠️ Borderline - Potential with Specific Deficits (6.0 - 7.4)", "level": "Partial Comprehension / Technical Gaps Present", "verdict": "LEAN_NO_HIRE"},
    "needs_remediation": {"min_score": 0.0, "badge": "❌ Remediation Needed - Below Technical Bar (< 6.0)", "level": "Foundational Misconceptions / Unsafe Assumptions", "verdict": "NO_HIRE"}
}

def get_score_badge(score: float) -> str:
    score = max(0.0, min(10.0, float(score)))
    if score >= 9.0: return SCORE_BADGES["outstanding"]["badge"]
    elif score >= 7.5: return SCORE_BADGES["strong_pass"]["badge"]
    elif score >= 6.0: return SCORE_BADGES["borderline"]["badge"]
    else: return SCORE_BADGES["needs_remediation"]["badge"]
