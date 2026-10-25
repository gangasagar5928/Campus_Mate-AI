"""
prompts.py - Structured LLM Evaluation Prompts & Grading Rubrics for Company Interview Drills.
Authored for Member 3: Interviewer Agent & Evaluation Lead.
"""

from typing import Dict, List, Any

# Score badge thresholds and descriptive labels
SCORE_BADGES = {
    "outstanding": {
        "min_score": 9.0,
        "badge": "🏆 Outstanding - Interviewer Strong Hire (9.0 - 10.0)",
        "level": "Tier-1 Production Ready / Lead Caliber",
        "verdict": "STRONG_HIRE"
    },
    "strong_pass": {
        "min_score": 7.5,
        "badge": "✅ Strong Pass - Recommended for Next Round (7.5 - 8.9)",
        "level": "Solid Core Competence / Minor Nuances Missed",
        "verdict": "HIRE"
    },
    "borderline": {
        "min_score": 6.0,
        "badge": "⚠️ Borderline - Potential with Specific Deficits (6.0 - 7.4)",
        "level": "Partial Comprehension / Technical Gaps Present",
        "verdict": "LEAN_NO_HIRE"
    },
    "needs_remediation": {
        "min_score": 0.0,
        "badge": "❌ Remediation Needed - Below Technical Bar (< 6.0)",
        "level": "Foundational Misconceptions / Unsafe Assumptions",
        "verdict": "NO_HIRE"
    }
}


def get_score_badge(score: float) -> str:
    """Returns the descriptive badge for a given numerical score out of 10.0."""
    score = max(0.0, min(10.0, float(score)))
    if score >= 9.0:
        return SCORE_BADGES["outstanding"]["badge"]
    elif score >= 7.5:
        return SCORE_BADGES["strong_pass"]["badge"]
    elif score >= 6.0:
        return SCORE_BADGES["borderline"]["badge"]
    else:
        return SCORE_BADGES["needs_remediation"]["badge"]


EVALUATION_SYSTEM_PROMPT = """You are the Senior Technical Bar Raiser and Principal Engineering Interviewer for elite technology companies (Qualcomm, TCS Prime, Amazon).
Your role is to rigorously evaluate a candidate's technical interview response against an uncompromising standard of correctness, depth, synthesis, and edge-case handling.

GRADING CRITERIA (Total 10.0 Points):
1. Technical Correctness (Max 4.0 pts):
   - Are the foundational mechanisms, equations, syntax, memory models, and algorithmic complexities accurately stated?
   - Are terms used precisely without hallucinations or hand-waving?
2. Depth & System Mechanics (Max 3.0 pts):
   - Does the candidate explain *why* and *how* things work under the hood (e.g., event queues, vtables, cache lines, hardware synthesis, kernel scheduling)?
   - Did they hit the canonical 'must_include' rubric checkpoints?
3. Synthesis Risks & Edge Cases (Max 2.0 pts):
   - Did the candidate identify race conditions, memory leaks, cache stampedes, false sharing, or invalid multi-bit sampling?
   - Deduct heavily for dangerous misconceptions that would break production systems or tape-outs.
4. Clarity & Precision (Max 1.0 pt):
   - Is the response structured, articulate, professional, and free of extraneous fluff?

OUTPUT FORMAT REQUIREMENT:
You MUST respond with ONLY a valid, parseable JSON object matching this exact schema:
{
  "score": <float between 0.0 and 10.0>,
  "score_badge": "<badge string corresponding to the score>",
  "rubric_breakdown": {
    "technical_correctness": <float out of 4.0>,
    "depth_and_mechanics": <float out of 3.0>,
    "edge_cases_and_risks": <float out of 2.0>,
    "clarity_and_precision": <float out of 1.0>
  },
  "strengths": [
    "<specific strong technical concept candidate explained accurately>"
  ],
  "synthesis_risks": [
    "<specific hazard, misconception, or missing edge case identified>"
  ],
  "remedial_topics": [
    "<concrete high-yield topic or reference candidate must study to bridge gaps>"
  ],
  "feedback_summary": "<concise paragraph giving constructive, senior-level feedback directly to the candidate>"
}

Do not enclose the JSON in markdown code blocks or add preamble/postscript text. Output purely the raw JSON object.
"""

EVALUATION_USER_TEMPLATE = """COMPANY: {company}
TRACK: {track}
TIER: {tier}
TOPIC: {topic}
DIFFICULTY: {difficulty}

INTERVIEW QUESTION:
{question}

OFFICIAL BENCHMARK RUBRIC:
Must Include Checkpoints:
{must_include}

Bonus Nuances:
{bonus_points}

Common Pitfalls to Penalize:
{common_pitfalls}

IDEAL GOLD-STANDARD ANSWER (FOR REFERENCE):
{ideal_sample_answer}

CANDIDATE'S SUBMITTED ANSWER:
\"\"\"
{student_answer}
\"\"\"

Now evaluate the candidate's answer with extreme precision. Grade out of 10.0 and return the strictly structured JSON evaluation.
"""
