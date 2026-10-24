"""
load_balancer.py - Deterministic Balancing Engine & Mutation Hook.
Owned by Member 2 (Syllabus Engine & Balancing Algorithm Lead).

Implements the dynamic study allocation formula and evening remedial mutation hook:
  - Normal Days (> 7 days to midterm): 60% Placement Prep / 40% Syllabus Revision
  - Approaching Midterm (3 <= days <= 7): 50% Placement Prep / 50% Syllabus Revision
  - Urgent Exam Mode (< 3 days): 10% Placement Prep / 90% High-Weightage Syllabus Units
  - Mutation Hook: low interview score (< 6.0/10) injects a 30-min remedial session
    into candidate's Evening Block (TimeBlock.EVENING).
"""

import json
import os
import uuid
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from schemas import (
    StudentProfile,
    DailyActionPlan,
    StudyTask,
    TaskType,
    TimeBlock,
    AllocationMode,
    ExamSchedule,
    InterviewEvaluation,
    UnitPriorityItem
)

RATIO_NORMAL = (0.60, 0.40)        # 60% Placement, 40% Syllabus
RATIO_APPROACHING = (0.50, 0.50)   # 50% Placement, 50% Syllabus
RATIO_URGENT = (0.10, 0.90)        # 10% Placement, 90% Syllabus (High-Weightage)

DEFAULT_CURRICULUM_PATH = os.path.join(os.path.dirname(__file__), "curriculum.json")


class CurriculumLoader:
    """Local loader and cached accessor for curriculum.json."""
    def __init__(self, json_path: str = DEFAULT_CURRICULUM_PATH):
        self.json_path = json_path
        self._curriculum_cache: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        if self._curriculum_cache is None:
            if not os.path.exists(self.json_path):
                raise FileNotFoundError(f"Curriculum database not found at {self.json_path}")
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._curriculum_cache = json.load(f)
        return self._curriculum_cache

    def get_branch_subjects(self, branch: str) -> List[Dict[str, Any]]:
        data = self.load()
        branches = data.get("branches", {})
        branch_data = branches.get(branch.upper())
        if not branch_data:
            return []
        return branch_data.get("subjects", [])
