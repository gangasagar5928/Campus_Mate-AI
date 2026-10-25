"""
models.py - Message Schemas for Company Interviewer Agent and Student Twin Agent.
Built on Fetch.ai uAgents Model framework.
"""

from typing import Optional, List, Dict, Any
from uagents import Model


class InterviewQuery(Model):
    """
    Sent by StudentTwinAgent to request an interview question or pack.
    """
    student_id: str
    company: str  # e.g., 'qualcomm', 'tcs_prime', 'amazon', 'google', 'nvidia'
    tier: str = "standard"
    question_id: Optional[str] = None
    session_id: Optional[str] = None


class InterviewQuestionResponse(Model):
    """
    Returned by CompanyInterviewerAgent with the selected drill question.
    """
    session_id: str
    question_id: str
    company: str
    track: str
    tier: str
    topic: str
    difficulty: str
    question_text: str
    is_unlocked: bool = True
    required_fee_fet: float = 0.0
    interviewer_wallet_address: str = ""
    payment_instructions: Optional[str] = None


class InterviewAnswerSubmission(Model):
    """
    Sent by StudentTwinAgent containing the candidate's technical response.
    """
    session_id: str
    question_id: str
    student_id: str
    student_answer: str


class InterviewEvaluation(Model):
    """
    Returned by CompanyInterviewerAgent with the numerical score out of 10.0,
    score badge, strengths, synthesis risks, and remedial topics.
    """
    session_id: str
    question_id: str
    student_id: str
    company: str
    score: float
    score_badge: str
    rubric_breakdown: Dict[str, float]
    strengths: List[str]
    synthesis_risks: List[str]
    remedial_topics: List[str]
    feedback_summary: str
    timestamp: str



# ==========================================
# ACP (Agent Chat Protocol) / ASI:One Models
# ==========================================
class ChatMessage(Model):
    """Raw text or JSON card payload from ASI:One."""
    text: str


# ==========================================
# Student Profile & Intake Models
# ==========================================
class StudentProfile(Model):
    """Intake form data representing the student's academic standing and target company."""
    branch: str = "ECE"
    semester: int = 6
    target_company: str = "Qualcomm"
    daily_available_hours: float = 3.0
    days_to_midterm: int = 4


# ==========================================
# Departmental Syllabus & Schedule Models
# ==========================================
class SyllabusRequest(Model):
    """Sent by StudentTwinAgent to DepartmentalSyllabusAgent to calculate study split."""
    student_id: str
    branch: str
    semester: int
    target_company: str
    daily_available_hours: float
    days_to_midterm: int


class StudyTask(Model):
    """Individual task item inside the DailyActionPlan."""
    task_name: str
    duration_minutes: int
    category: str  # "Syllabus Revision" or "Placement Prep"
    priority: str  # "High", "Medium", "Urgent"


class DailyActionPlan(Model):
    """Returned by DepartmentalSyllabusAgent with mathematically computed time allocation."""
    student_id: str = "default_student"
    academic_ratio: float  # e.g., 0.40
    placement_ratio: float # e.g., 0.60
    tasks: List[StudyTask]
    notes: Optional[str] = None


class ScheduleMutation(Model):
    """Event emitted to add remedial study blocks following interview drill evaluation."""
    student_id: str
    remedial_topic: str
    additional_minutes: int = 30


# Forward exports from canonical schemas.py for backwards compatibility
try:
    from models.schemas import (
        TaskType,
        TimeBlock,
        AllocationMode,
        ExamSchedule,
        PlanRequest,
        PlanResponse,
        CurriculumQueryRequest,
        CurriculumQueryResponse,
        UnitPriorityItem
    )
except ImportError:
    from schemas import (
        TaskType,
        TimeBlock,
        AllocationMode,
        ExamSchedule,
        PlanRequest,
        PlanResponse,
        CurriculumQueryRequest,
        CurriculumQueryResponse,
        UnitPriorityItem
    )
