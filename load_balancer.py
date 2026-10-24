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


class DeterministicBalancingEngine:
    """Core deterministic scheduling and dynamic ratio allocation engine."""
    def __init__(self, curriculum_loader: Optional[CurriculumLoader] = None):
        self.curriculum_loader = curriculum_loader or CurriculumLoader()

    @staticmethod
    def get_nearest_exam(upcoming_exams: List[ExamSchedule]) -> Optional[ExamSchedule]:
        if not upcoming_exams:
            return None
        return min(upcoming_exams, key=lambda e: e.days_to_exam)

    def calculate_priorities_for_profile(
        self, profile: StudentProfile
    ) -> List[UnitPriorityItem]:
        """Calculates deterministic unit priorities using credit weights and exam proximity."""
        subjects = self.curriculum_loader.get_branch_subjects(profile.branch)
        exam_map = {e.subject_code.upper(): e for e in profile.upcoming_exams}
        exam_name_map = {e.subject_name.lower(): e for e in profile.upcoming_exams}
        weak_topics_lower = [w.lower() for w in profile.weak_topics]
        priority_items: List[UnitPriorityItem] = []

        for subj in subjects:
            code = subj.get("subject_code", "")
            name = subj.get("subject_name", "")
            credits = float(subj.get("credit_weight", 4.0))

            matched_exam = exam_map.get(code.upper())
            if not matched_exam:
                for k, v in exam_name_map.items():
                    if k in name.lower() or name.lower() in k:
                        matched_exam = v
                        break

            days_to_exam = matched_exam.days_to_exam if matched_exam else None

            for unit in subj.get("units", []):
                u_num = unit.get("unit_number", 1)
                u_title = unit.get("title", f"Unit {u_num}")
                weight_pct = float(unit.get("weightage_percent", 20.0))
                is_hy = bool(unit.get("is_high_yield", False))
                topics = unit.get("topics", [])
                rec_minutes = int(unit.get("recommended_study_minutes", 60))

                base_priority = (weight_pct / 100.0) * credits
                if is_hy:
                    base_priority *= 1.35

                if days_to_exam is not None:
                    proximity_factor = 1.0 + (10.0 / (days_to_exam + 1.0))
                    calculated_p = base_priority * proximity_factor
                else:
                    calculated_p = base_priority * 1.0

                for t in topics:
                    if any(w in t.lower() for w in weak_topics_lower):
                        calculated_p *= 1.25
                        break

                priority_items.append(
                    UnitPriorityItem(
                        subject_code=code,
                        subject_name=name,
                        unit_number=u_num,
                        unit_title=u_title,
                        weightage_percent=weight_pct,
                        credit_weight=credits,
                        is_high_yield=is_hy,
                        calculated_priority=round(calculated_p, 3),
                        recommended_study_minutes=rec_minutes,
                        topics=topics
                    )
                )

        priority_items.sort(key=lambda item: item.calculated_priority, reverse=True)
        return priority_items
