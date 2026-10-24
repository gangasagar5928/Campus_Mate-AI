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
