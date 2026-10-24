"""
cards_templates.py - ASI:One Interactive UI Card Generators
Compliant with Agent Chat Protocol (ACP) specification.
Generates structured JSON payloads rendered by ASI:One.
"""

import json
from typing import Dict, Any, List, Optional


def create_intake_form_card() -> Dict[str, Any]:
    """
    Card 1: Student Intake Form (Initial Discovery).
    Emitted when student connects via ASI:One.
    """
    return {
        "type": "card",
        "card_type": "form",
        "title": "CampusMate AI: Profile Setup",
        "description": "Configure your academic semester and target company to balance university syllabus with placement prep.",
        "fields": [
            {
                "name": "branch",
                "label": "Engineering Branch",
                "type": "select",
                "options": ["ECE", "CSE", "IT", "MECH"],
                "default": "ECE"
            },
            {
                "name": "semester",
                "label": "Current Semester",
                "type": "select",
                "options": [1, 2, 3, 4, 5, 6, 7, 8],
                "default": 6
            },
            {
                "name": "target_company",
                "label": "Target Company",
                "type": "select",
                "options": ["Qualcomm", "Amazon", "TCS Prime"],
                "default": "Qualcomm"
            },
            {
                "name": "daily_hours",
                "label": "Free Study Hours Today",
                "type": "number",
                "default": 3
            },
            {
                "name": "days_to_exam",
                "label": "Days Until Next Sessional Exam",
                "type": "number",
                "default": 4
            }
        ],
        "submit_button": "Generate Adaptive Schedule",
        "post_back_action": "submit_profile"
    }


def create_action_plan_card(
    plan: Any,
    target_company: str = "Qualcomm"
) -> Dict[str, Any]:
    """
    Card 2: Generated Action Plan Card (Review Screen).
    Displays the dynamic split between University Syllabus and Placement Prep.
    Supports both schemas.py and models.py DailyActionPlan objects.
    """
    placement_ratio = getattr(plan, "placement_prep_ratio", getattr(plan, "placement_ratio", 0.50))
    academic_ratio = getattr(plan, "syllabus_revision_ratio", getattr(plan, "academic_ratio", 0.50))

    placement_pct = int(round(placement_ratio * 100))
    academic_pct = int(round(academic_ratio * 100))

    items = []
    task_list = getattr(plan, "study_tasks", getattr(plan, "tasks", []))
    for task in task_list:
        title = getattr(task, "task_description", getattr(task, "task_name", "Study Task"))
        duration = getattr(task, "allocated_minutes", getattr(task, "duration_minutes", 45))
        category = getattr(task, "task_type", getattr(task, "category", "Syllabus"))
        if hasattr(category, "value"):
            category = category.value
        priority = f"Weight {task.priority_weight}" if hasattr(task, "priority_weight") else getattr(task, "priority", "High")
        items.append({
            "title": str(title),
            "time": f"{duration} mins",
            "category": str(category),
            "status": str(priority)
        })

    notes_str = getattr(plan, "notes", getattr(plan, "plan_id", ""))
    desc = f"Dynamic schedule generated based on exam proximity ({notes_str})." if notes_str else "Dynamic schedule generated based on exam proximity."

    return {
        "type": "card",
        "card_type": "review_screen",
        "title": "Optimized Daily Action Plan",
        "description": desc,
        "metrics": [
            {"label": "Placement Focus", "value": f"{placement_pct}%"},
            {"label": "Syllabus Focus", "value": f"{academic_pct}%"}
        ],
        "items": items,
        "actions": [
            {
                "label": f"Start {target_company} Mock Interview",
                "action_type": "post_back",
                "payload": f"action=start_drill&company={target_company.lower()}"
            }
        ]
    }


def create_interview_drill_card(
    company: str,
    topic: str,
    question_text: str,
    tier: str = "standard"
) -> Dict[str, Any]:
    """
    Card: Technical Interview Drill Card.
    """
    return {
        "type": "card",
        "card_type": "form",
        "title": f"Technical Drill: {company.upper()} ({topic})",
        "description": question_text,
        "badge": tier.upper(),
        "fields": [
            {
                "name": "student_answer",
                "label": "Your Technical Explanation / RTL / Pseudocode",
                "type": "textarea",
                "placeholder": "Type your detailed explanation or code solution..."
            }
        ],
        "submit_button": "Submit Answer for Evaluation",
        "post_back_action": "submit_answer"
    }


def create_evaluation_scorecard(
    eval_result: Any
) -> Dict[str, Any]:
    """
    Card 3: Real-Time Evaluation Scorecard (Detail View).
    Displays rubric breakdown, LLM critique, and schedule mutation confirmation.
    """
    breakdown_list = []
    rubric_dict = getattr(eval_result, "rubric_breakdown", {})
    if rubric_dict:
        for dim, score in rubric_dict.items():
            breakdown_list.append({"dimension": str(dim).replace("_", " ").title(), "rating": f"{float(score):.1f}/10"})
    else:
        breakdown_list = [
            {"dimension": "Concept Clarity", "rating": "Strong"},
            {"dimension": "Hardware Synthesis Timing", "rating": "Needs Review"}
        ]

    remedial_topics = getattr(eval_result, "remedial_topics", [])
    remedial_topic_str = ", ".join(remedial_topics) if remedial_topics else "Core Fundamentals"
    system_action_str = f"Schedule updated: 30m allocated this evening to '{remedial_topic_str}'."

    badge_str = getattr(eval_result, "score_badge", "Evaluated")
    summary_str = getattr(eval_result, "feedback_summary", "Review complete.")

    return {
        "type": "card",
        "card_type": "detail_view",
        "title": f"Interview Drill Result: {eval_result.company.upper()}",
        "score_badge": f"{eval_result.score:.1f} / 10 ({badge_str})",
        "breakdown": breakdown_list,
        "agent_feedback": summary_str,
        "system_action": system_action_str,
        "actions": [
            {
                "label": "View Mutated Daily Schedule",
                "action_type": "post_back",
                "payload": "action=view_updated_schedule"
            }
        ]
    }


def card_to_message_payload(card_dict: Dict[str, Any]) -> str:
    """
    Encodes card into ASI:One ACP markdown sentinel format.
    """
    json_str = json.dumps(card_dict, indent=2)
    return f"```json:asione-card\n{json_str}\n```"
