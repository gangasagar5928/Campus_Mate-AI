"""
schemas.py - Shared Data Contracts for Multi-Agent Student Copilot.
Owned by Member 2 (Syllabus Engine & Balancing Algorithm Lead).

This module defines all Pydantic/uAgents data schemas shared across:
  - Member 1: StudentTwinAgent (Profile Manager, Daily Orchestrator)
  - Member 2: Syllabus Engine & Load Balancer Agent
  - Member 3: Technical Interview & Evaluation Agent
"""

from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any

# Fetch.ai uAgents uses Pydantic v1 internally for message hashing and backwards compatibility
try:
    from uagents import Model
    from pydantic.v1 import Field
except ImportError:
    try:
        from pydantic.v1 import BaseModel as Model, Field
    except ImportError:
        from pydantic import BaseModel as Model, Field  # type: ignore


# ==============================================================================
# Enumerations & Literals
# ==============================================================================

class TaskType(str, Enum):
    """Categorization of daily study tasks."""
    PLACEMENT_PREP = "placement_prep"
    SYLLABUS_REVISION = "syllabus_revision"
    REMEDIAL = "remedial"
    MOCK_INTERVIEW = "mock_interview"


class TimeBlock(str, Enum):
    """Daily scheduling time slots."""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class AllocationMode(str, Enum):
    """Dynamic allocation modes dictated by exam proximity."""
    NORMAL = "NORMAL"                          # > 7 days to midterm: 60% Placement / 40% Syllabus
    APPROACHING_MIDTERM = "APPROACHING_MIDTERM" # 3 <= days <= 7: 50% Placement / 50% Syllabus
    URGENT_EXAM = "URGENT_EXAM"                # < 3 days: 10% Placement / 90% High-Weightage Syllabus


# ==============================================================================
# Atomic Models
# ==============================================================================

class ExamSchedule(Model):
    """Details of an upcoming university/college midterm or end-sem exam."""
    subject_code: str = Field(..., description="Course code, e.g. KEC-502 or KCS-501")
    subject_name: str = Field(..., description="Course title, e.g. Digital Electronics or Operating Systems")
    exam_date: str = Field(..., description="Exam date in YYYY-MM-DD format")
    days_to_exam: int = Field(..., ge=0, description="Deterministic count of days remaining until exam")
    credit_weight: float = Field(default=4.0, ge=1.0, le=5.0, description="AKTU credit weight (typically 3.0 to 4.0)")


class StudyTask(Model):
    """Individual unit of work scheduled in the daily action plan."""
    task_id: str = Field(default="TASK-001", description="Unique deterministic identifier for the task, e.g. TASK-20261024-001")
    title: str = Field(default="", description="Descriptive task summary")
    task_name: Optional[str] = Field(default=None, description="Task name for backwards compatibility")
    subject: str = Field(default="Core Technical", description="Related academic subject or technical domain")
    topic: str = Field(default="Concepts", description="Specific syllabus topic or placement concept, e.g. Flip-Flops")
    task_type: TaskType = Field(default=TaskType.SYLLABUS_REVISION, description="Task classification")
    category: Optional[str] = Field(default=None, description="Category string for compatibility with legacy models")
    duration_minutes: int = Field(default=45, gt=0, le=240, description="Allocated time block in minutes")
    priority: Any = Field(default=5, description="Priority score (10 = highest / critical) or label")
    time_block: TimeBlock = Field(default=TimeBlock.MORNING, description="Assigned time slot in the day")
    completed: bool = Field(default=False, description="Completion toggle")
    is_remedial: bool = Field(default=False, description="Whether this task was dynamically injected by a mutation hook")
    mutation_source: Optional[str] = Field(
        default=None,
        description="Reason or evaluation ID that triggered remedial injection"
    )


# ==============================================================================
# Shared Contract 1: StudentProfile (Member 1 <-> Member 2)
# ==============================================================================

class StudentProfile(Model):
    """
    Primary student persona and academic profile owned by Member 1's StudentTwinAgent
    and consumed by Member 2's Syllabus Engine.
    """
    student_id: str = Field(default="GCET-STUDENT-001", description="Unique student ID or roll number")
    name: str = Field(default="Campus Candidate", description="Student full name")
    branch: str = Field(default="ECE", description="Academic branch: 'ECE' or 'CSE'")
    year: int = Field(default=3, ge=1, le=4, description="Current academic year (e.g. 3rd year)")
    semester: int = Field(default=5, ge=1, le=8, description="Current semester (5 or 6 for 3rd year)")
    college: str = Field(default="GCET (AKTU)", description="Affiliated institution")
    daily_available_hours: float = Field(
        default=4.0, ge=1.0, le=12.0,
        description="Available daily self-study hours outside regular college lectures"
    )
    target_company: Optional[str] = Field(default="Qualcomm", description="Primary target company")
    target_companies: List[str] = Field(
        default_factory=list,
        description="Target companies for placement preparation"
    )
    weak_topics: List[str] = Field(
        default_factory=list,
        description="List of self-identified or interview-identified weak topics"
    )
    upcoming_exams: List[ExamSchedule] = Field(
        default_factory=list,
        description="Sorted schedule of upcoming midterm/semester examinations"
    )
    days_to_midterm: Optional[int] = Field(
        default=None,
        description="Days remaining to midterm for compatibility with intake forms"
    )


# ==============================================================================
# Shared Contract 2: DailyActionPlan (Member 2 -> Member 1)
# ==============================================================================

class DailyActionPlan(Model):
    """
    The deterministic schedule output produced by Member 2's Balancing Engine
    and delivered to Member 1's StudentTwinAgent.
    """
    plan_id: str = Field(default="PLAN-001", description="Unique plan ID, e.g. PLAN-20261024-ECE-042")
    student_id: str = Field(default="GCET-STUDENT-001", description="Target student roll number")
    date: str = Field(default="2026-10-24", description="Date of the plan in YYYY-MM-DD format")
    mode: AllocationMode = Field(default=AllocationMode.NORMAL, description="Dynamic allocation mode based on exam proximity")
    days_to_nearest_exam: Optional[int] = Field(None, description="Days to closest upcoming exam (if scheduled)")
    nearest_exam_subject: Optional[str] = Field(None, description="Subject of the closest exam")
    placement_prep_ratio: float = Field(default=0.60, ge=0.0, le=1.0, description="Percentage of time allocated to placement")
    syllabus_revision_ratio: float = Field(default=0.40, ge=0.0, le=1.0, description="Percentage of time allocated to syllabus")
    academic_ratio: Optional[float] = Field(default=None, description="Alias for syllabus_revision_ratio")
    placement_ratio: Optional[float] = Field(default=None, description="Alias for placement_prep_ratio")
    total_allocated_minutes: int = Field(default=240, gt=0, description="Total minutes distributed across all tasks")
    tasks: List[StudyTask] = Field(default_factory=list, description="Ordered schedule of study blocks")
    remedial_sessions_count: int = Field(default=0, description="Number of remedial sessions injected into plan")
    summary_notes: str = Field(default="", description="Executive summary of the day's strategy and focus areas")
    notes: Optional[str] = Field(default=None, description="Compatibility alias for summary_notes")


# ==============================================================================
# Shared Contracts 3 & 4: InterviewQuery & InterviewEvaluation (Member 1/2 <-> Member 3)
# ==============================================================================

class InterviewQuery(Model):
    """
    Query contract sent to Member 3's Interview Agent to trigger a mock interview session.
    """
    query_id: str = Field(default="QUERY-001", description="Unique session request ID")
    session_id: Optional[str] = Field(default=None, description="Session ID for compatibility")
    student_id: str = Field(default="GCET-STUDENT-001", description="Candidate roll number")
    branch: str = Field(default="ECE", description="Candidate branch: 'ECE' or 'CSE'")
    company: str = Field(default="qualcomm", description="Target company")
    tier: str = Field(default="standard", description="standard (free) or tier-1 (1 FET)")
    question_id: Optional[str] = Field(default=None, description="Question ID")
    payment_tx_hash: Optional[str] = Field(default=None, description="FET payment tx hash")
    subject: str = Field(default="Digital Electronics", description="Subject domain, e.g. Digital Electronics or Operating Systems")
    topic: str = Field(default="Sequential Logic", description="Focal topic, e.g. Sequential Logic / Flip-Flops")
    question_count: int = Field(default=5, ge=1, le=15, description="Number of questions in the interview")
    difficulty: str = Field(default="intermediate", description="Difficulty: easy, intermediate, hard")
    target_role: Optional[str] = Field(default="Hardware / Firmware Engineer", description="Target job title")


class InterviewEvaluation(Model):
    """
    Evaluation feedback emitted by Member 3's Interview Agent.
    If score is low (< 6.0), Member 2's mutation hook intercepts this and inserts
    a 30-minute evening remedial session.
    """
    evaluation_id: Optional[str] = Field(default="EVAL-001", description="Unique evaluation ID, e.g. EVAL-20261024-001")
    session_id: Optional[str] = Field(default=None, description="Session ID from Member 3")
    question_id: Optional[str] = Field(default=None, description="Question ID assessed")
    student_id: str = Field(default="GCET-STUDENT-001", description="Candidate roll number")
    company: Optional[str] = Field(default=None, description="Target company assessed")
    subject: str = Field(default="Technical Core", description="Subject assessed")
    topic: str = Field(default="Concepts", description="Topic assessed, e.g. Flip-Flops, Deadlocks, SQL Normalization")
    score: float = Field(..., ge=0.0, le=10.0, description="Overall score out of 10.0")
    score_badge: Optional[str] = Field(default=None, description="Score badge label (e.g., Bronze, Silver, Gold)")
    max_score: float = Field(default=10.0, description="Maximum scale (defaults to 10.0)")
    feedback: Optional[str] = Field(default="", description="Detailed textual feedback and conceptual gaps identified")
    feedback_summary: Optional[str] = Field(default="", description="Summary feedback from Member 3")
    rubric_breakdown: Dict[str, float] = Field(default_factory=dict, description="Rubric criteria breakdown")
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths")
    synthesis_risks: List[str] = Field(default_factory=list, description="Synthesis risks identified")
    weak_subtopics: List[str] = Field(default_factory=list, description="Specific subtopics where candidate struggled")
    remedial_topics: List[str] = Field(default_factory=list, description="Recommended remedial topics from Member 3")
    needs_remedial: bool = Field(
        default=False,
        description="Flag indicating performance was subpar (automatically set if score < 6.0)"
    )
    timestamp: str = Field(
        default="2026-10-24T12:00:00",
        description="ISO timestamp of evaluation"
    )

    def is_low_score(self, threshold_percentage: float = 0.60) -> bool:
        """Determines if the score falls below the remedial threshold (default: 60%)."""
        if self.max_score <= 0:
            return False
        return (self.score / self.max_score) < threshold_percentage or self.needs_remedial


# ==============================================================================
# Inter-Agent Messaging Envelopes (for Fetch.ai uAgents Protocol)
# ==============================================================================

class PlanRequest(Model):
    """Message sent by StudentTwinAgent to Departmental Syllabus Agent to request a schedule."""
    request_id: str
    student_profile: StudentProfile
    recent_evaluations: List[InterviewEvaluation] = Field(default_factory=list)
    requested_date: Optional[str] = None


class PlanResponse(Model):
    """Message returned by Departmental Syllabus Agent containing the finalized plan."""
    request_id: str
    success: bool
    plan: Optional[DailyActionPlan] = None
    error_message: Optional[str] = None


class SyllabusRequest(Model):
    """Sent by StudentTwinAgent to DepartmentalSyllabusAgent to calculate study split."""
    student_id: str
    branch: str
    semester: int
    target_company: str
    daily_available_hours: float
    days_to_midterm: int


class CurriculumQueryRequest(Model):
    """Query message to inspect unit priorities for a subject or branch."""
    branch: str
    subject_code: Optional[str] = None
    days_to_exam: Optional[int] = None


class UnitPriorityItem(Model):
    """Item representing a unit with calculated priority."""
    subject_code: str
    subject_name: str
    unit_number: int
    unit_title: str
    weightage_percent: float
    credit_weight: float
    is_high_yield: bool
    calculated_priority: float
    recommended_study_minutes: int
    topics: List[str]


class CurriculumQueryResponse(Model):
    """Response containing calculated unit priorities."""
    branch: str
    priorities: List[UnitPriorityItem] = Field(default_factory=list)
    timestamp: str = Field(default="2026-10-24T12:00:00")
