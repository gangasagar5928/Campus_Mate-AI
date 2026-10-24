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
