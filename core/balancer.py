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

try:
    from models.schemas import (
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
except ImportError:
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

def resolve_curriculum_path() -> str:
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "curriculum.json"),
        os.path.join(os.path.dirname(__file__), "curriculum.json"),
        os.path.join(os.getcwd(), "data", "curriculum.json"),
        os.path.join(os.getcwd(), "curriculum.json")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

DEFAULT_CURRICULUM_PATH = resolve_curriculum_path()


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

    def get_branch_subjects(self, branch: str, semester: Optional[int] = None) -> List[Dict[str, Any]]:
        data = self.load()
        branches = data.get("branches", {})
        branch_data = branches.get(branch.upper(), {})
        all_subjects = branch_data.get("subjects", [])
        if semester is not None:
            filtered = [s for s in all_subjects if s.get("semester") == semester]
            if filtered:
                return filtered
        return all_subjects


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
        subjects = self.curriculum_loader.get_branch_subjects(profile.branch, getattr(profile, 'semester', None))
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

    @classmethod
    def determine_allocation_mode(
        cls, days_to_exam: Optional[int]
    ) -> Tuple[AllocationMode, float, float]:
        """
        Dynamically allocates study ratios deterministically:
          - > 7 days (or no exams): Normal (60% Placement / 40% Syllabus)
          - 3 <= days <= 7: Approaching Midterm (50% Placement / 50% Syllabus)
          - < 3 days: Urgent Exam Mode (10% Placement / 90% High-Weightage Syllabus)
        """
        if days_to_exam is None or days_to_exam > 7:
            return AllocationMode.NORMAL, RATIO_NORMAL[0], RATIO_NORMAL[1]
        elif 3 <= days_to_exam <= 7:
            return AllocationMode.APPROACHING_MIDTERM, RATIO_APPROACHING[0], RATIO_APPROACHING[1]
        else:
            return AllocationMode.URGENT_EXAM, RATIO_URGENT[0], RATIO_URGENT[1]

    @staticmethod
    def calculate_time_budget(
        available_hours: float,
        placement_ratio: float,
        syllabus_ratio: float
    ) -> Tuple[int, int, int]:
        """Converts available hours into minutes and divides strictly by ratios."""
        total_minutes = int(round(available_hours * 60.0))
        placement_minutes = int(round(total_minutes * placement_ratio))
        syllabus_minutes = total_minutes - placement_minutes
        return total_minutes, placement_minutes, syllabus_minutes

    def generate_daily_action_plan(
        self,
        profile: StudentProfile,
        evaluations: Optional[List[InterviewEvaluation]] = None,
        target_date: Optional[str] = None
    ) -> DailyActionPlan:
        """Generates a complete deterministic daily action plan."""
        evaluations = evaluations or []
        today_str = target_date or date.today().isoformat()
        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d')}-{profile.student_id[-6:]}"

        # Nearest exam lookup
        nearest_exam = self.get_nearest_exam(profile.upcoming_exams)
        days_to_nearest = nearest_exam.days_to_exam if nearest_exam else profile.days_to_midterm
        nearest_subject = nearest_exam.subject_name if nearest_exam else None

        mode, p_ratio, s_ratio = self.determine_allocation_mode(days_to_nearest)
        total_mins, p_mins, s_mins = self.calculate_time_budget(
            profile.daily_available_hours, p_ratio, s_ratio
        )

        all_unit_priorities = self.calculate_priorities_for_profile(profile)
        tasks: List[StudyTask] = []
        task_seq = 1

        # High-weightage units for Urgent mode
        if mode == AllocationMode.URGENT_EXAM:
            filtered_units = [u for u in all_unit_priorities if u.is_high_yield]
            if not filtered_units:
                filtered_units = all_unit_priorities
        else:
            filtered_units = all_unit_priorities

        # 1. Placement Tasks
        remaining_p_mins = p_mins
        target_company = profile.target_company or (profile.target_companies[0] if profile.target_companies else "Tier-1 Tech")
        block_order = [TimeBlock.MORNING, TimeBlock.AFTERNOON, TimeBlock.EVENING, TimeBlock.NIGHT]
        
        while remaining_p_mins >= 30:
            duration = 45 if remaining_p_mins >= 45 else 30
            topic = "Core Problem Solving" if profile.branch == "CSE" else "Hardware Design & Timing"
            task = StudyTask(
                task_id=f"TASK-{today_str.replace('-', '')}-{task_seq:03d}",
                title=f"Placement Drill: {topic} ({target_company})",
                task_name=f"Placement Drill: {topic} ({target_company})",
                subject="Placement Preparation",
                topic=topic,
                task_type=TaskType.PLACEMENT_PREP,
                category="Placement Prep",
                duration_minutes=duration,
                priority=8 if mode == AllocationMode.NORMAL else 4,
                time_block=TimeBlock.MORNING if task_seq == 1 else TimeBlock.AFTERNOON
            )
            tasks.append(task)
            task_seq += 1
            remaining_p_mins -= duration

        # 2. Syllabus Revision Tasks
        remaining_s_mins = s_mins
        unit_idx = 0
        while remaining_s_mins >= 30 and filtered_units:
            unit = filtered_units[unit_idx % len(filtered_units)]
            unit_idx += 1
            duration = min(60, remaining_s_mins)
            if duration < 30:
                duration = 30
            topic_str = unit.topics[0] if unit.topics else unit.unit_title
            task = StudyTask(
                task_id=f"TASK-{today_str.replace('-', '')}-{task_seq:03d}",
                title=f"Syllabus Revision: {unit.subject_name} - {unit.unit_title}",
                task_name=f"Syllabus Revision: {unit.subject_name} - {unit.unit_title}",
                subject=unit.subject_name,
                topic=topic_str,
                task_type=TaskType.SYLLABUS_REVISION,
                category="Syllabus Revision",
                duration_minutes=duration,
                priority=10 if mode == AllocationMode.URGENT_EXAM else 6,
                time_block=TimeBlock.AFTERNOON if task_seq <= 2 else TimeBlock.NIGHT
            )
            tasks.append(task)
            task_seq += 1
            remaining_s_mins -= duration

        # Apply evening remedial mutation hook
        plan = DailyActionPlan(
            plan_id=plan_id,
            student_id=profile.student_id,
            date=today_str,
            mode=mode,
            days_to_nearest_exam=days_to_nearest,
            nearest_exam_subject=nearest_subject,
            placement_prep_ratio=p_ratio,
            syllabus_revision_ratio=s_ratio,
            academic_ratio=s_ratio,
            placement_ratio=p_ratio,
            total_allocated_minutes=sum(t.duration_minutes for t in tasks),
            tasks=tasks,
            remedial_sessions_count=0,
            summary_notes=f"Deterministic Mode: {mode.value}. Allocation: {int(p_ratio*100)}% Placement / {int(s_ratio*100)}% Syllabus."
        )

        for ev in evaluations:
            plan = self.apply_remedial_mutation(plan, ev)

        return plan

    def apply_remedial_mutation(
        self,
        plan: DailyActionPlan,
        evaluation: InterviewEvaluation
    ) -> DailyActionPlan:
        """
        Evening Remedial Mutation Hook:
        If Member 3's interview evaluation reports a low score (< 6.0/10),
        insert a 30-minute remedial session into the candidate's Evening Block (TimeBlock.EVENING).
        """
        if not evaluation.is_low_score(0.60):
            return plan

        remedial_topic = evaluation.topic
        if evaluation.weak_subtopics:
            remedial_topic = f"{evaluation.topic} ({evaluation.weak_subtopics[0]})"
        elif evaluation.remedial_topics:
            remedial_topic = f"{evaluation.topic} ({evaluation.remedial_topics[0]})"

        remedial_id = f"REMEDIAL-{plan.date.replace('-', '')}-{len(plan.tasks) + 1:03d}"
        remedial_task = StudyTask(
            task_id=remedial_id,
            title=f"Remedial Session: {remedial_topic}",
            task_name=f"Remedial Session: {remedial_topic}",
            subject=evaluation.subject,
            topic=remedial_topic,
            task_type=TaskType.REMEDIAL,
            category="Remedial Intervention",
            duration_minutes=30,
            priority=10,
            time_block=TimeBlock.EVENING,
            is_remedial=True,
            mutation_source=evaluation.evaluation_id or evaluation.session_id or "Low Mock Interview Score"
        )

        # Insert at top of Evening Block
        evening_indices = [i for i, t in enumerate(plan.tasks) if t.time_block == TimeBlock.EVENING]
        if evening_indices:
            insert_pos = evening_indices[0]
            plan.tasks.insert(insert_pos, remedial_task)
        else:
            plan.tasks.append(remedial_task)

        plan.remedial_sessions_count += 1
        plan.total_allocated_minutes += 30
        plan.summary_notes += f" [Remedial Inserted]: 30-min Evening drill on '{remedial_topic}' due to score {evaluation.score}/10."
        return plan


# Global singleton instance
balancer_engine = DeterministicBalancingEngine()
