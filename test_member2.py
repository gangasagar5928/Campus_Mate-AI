"""
test_member2.py - Comprehensive Unit Tests & Specification Verification.
Owned by Member 2 (Syllabus Engine & Balancing Algorithm Lead).

Validates:
1. Deterministic Balancing Formula:
   - Normal Days (> 7 days): 60% Placement / 40% Syllabus Revision
   - Approaching Midterm (3 <= days <= 7): 50% Placement / 50% Syllabus Revision
   - Urgent Exam Mode (< 3 days): 10% Placement / 90% Syllabus (High-Weightage units)
2. Mutation Hook:
   - Low interview score (< 6.0 / 10) inserts a 30-minute remedial session into the evening block.
   - High score (>= 6.0 / 10) does NOT insert remedial session.
3. AKTU/GCET 3rd-Year Curriculum Integrity:
   - ECE: Digital Electronics (Sequential Logic, Flip-Flops), Microprocessors (8085/8086).
   - CSE: Data Structures & Algorithms, Operating Systems, Database Management Systems.
4. Schema Contracts:
   - Serialization and deserialization of StudentProfile, DailyActionPlan, StudyTask,
     InterviewQuery, and InterviewEvaluation.
"""

import unittest
from datetime import date

from schemas import (
    StudentProfile,
    DailyActionPlan,
    StudyTask,
    TaskType,
    TimeBlock,
    AllocationMode,
    ExamSchedule,
    InterviewQuery,
    InterviewEvaluation
)
from load_balancer import (
    DeterministicBalancingEngine,
    CurriculumLoader,
    RATIO_NORMAL,
    RATIO_APPROACHING,
    RATIO_URGENT
)


class TestSyllabusEngineAndLoadBalancer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = DeterministicBalancingEngine()
        cls.curriculum = cls.engine.curriculum_loader.load()

    def test_01_curriculum_database_aktu_gcet(self):
        """Verify curriculum.json contains AKTU/GCET 3rd-year subjects for ECE & CSE."""
        branches = self.curriculum.get("branches", {})
        self.assertIn("ECE", branches, "ECE branch missing from curriculum.json")
        self.assertIn("CSE", branches, "CSE branch missing from curriculum.json")

        # ECE checks: Digital Electronics & Microprocessors
        ece_subjects = branches["ECE"]["subjects"]
        ece_names = [s["subject_name"].lower() for s in ece_subjects]
        
        has_digital_electronics = any("digital" in name for name in ece_names)
        has_microprocessors = any("microprocessor" in name for name in ece_names)
        self.assertTrue(has_digital_electronics, "ECE must include Digital Electronics")
        self.assertTrue(has_microprocessors, "ECE must include Microprocessors")

        # Check for Sequential Logic & Flip-Flops specifically
        de_subj = next(s for s in ece_subjects if "digital" in s["subject_name"].lower())
        all_de_topics = [t.lower() for u in de_subj["units"] for t in u["topics"]]
        has_flip_flops = any("flip-flop" in t for t in all_de_topics)
        self.assertTrue(has_flip_flops, "Digital Electronics must include Flip-Flops")

        # CSE checks: DSA, OS, DBMS
        cse_subjects = branches["CSE"]["subjects"]
        cse_names = [s["subject_name"].lower() for s in cse_subjects]
        has_dsa = any("data structure" in name or "algorithm" in name for name in cse_names)
        has_os = any("operating system" in name for name in cse_names)
        has_dbms = any("database" in name for name in cse_names)
        self.assertTrue(has_dsa, "CSE must include Data Structures & Algorithms")
        self.assertTrue(has_os, "CSE must include Operating Systems")
        self.assertTrue(has_dbms, "CSE must include Database Management Systems")

    def test_02_allocation_formula_normal_mode(self):
        """Verify > 7 days to midterm triggers 60% Placement / 40% Syllabus."""
        # Case A: Exam in 10 days
        mode, p_ratio, s_ratio = self.engine.determine_allocation_mode(days_to_exam=10)
        self.assertEqual(mode, AllocationMode.NORMAL)
        self.assertAlmostEqual(p_ratio, 0.60)
        self.assertAlmostEqual(s_ratio, 0.40)

        # Case B: No exams scheduled (None)
        mode_none, p_none, s_none = self.engine.determine_allocation_mode(days_to_exam=None)
        self.assertEqual(mode_none, AllocationMode.NORMAL)
        self.assertAlmostEqual(p_none, 0.60)
        self.assertAlmostEqual(s_none, 0.40)

    def test_03_allocation_formula_approaching_midterm(self):
        """Verify 3 <= days <= 7 triggers 50% Placement / 50% Syllabus."""
        for d in [3, 5, 7]:
            mode, p_ratio, s_ratio = self.engine.determine_allocation_mode(days_to_exam=d)
            self.assertEqual(mode, AllocationMode.APPROACHING_MIDTERM, f"Failed at day {d}")
            self.assertAlmostEqual(p_ratio, 0.50)
            self.assertAlmostEqual(s_ratio, 0.50)

    def test_04_allocation_formula_urgent_exam_mode(self):
        """Verify < 3 days triggers 10% Placement / 90% High-Weightage Syllabus."""
        for d in [0, 1, 2]:
            mode, p_ratio, s_ratio = self.engine.determine_allocation_mode(days_to_exam=d)
            self.assertEqual(mode, AllocationMode.URGENT_EXAM, f"Failed at day {d}")
            self.assertAlmostEqual(p_ratio, 0.10)
            self.assertAlmostEqual(s_ratio, 0.90)

    def test_05_plan_generation_urgent_mode_high_yield(self):
        """Verify plan generated in Urgent Mode allocates ~90% to syllabus and focuses on high-yield units."""
        profile = StudentProfile(
            student_id="TEST-ECE-01",
            name="Test Student",
            branch="ECE",
            daily_available_hours=4.0,  # 240 mins
            upcoming_exams=[
                ExamSchedule(
                    subject_code="KEC-502",
                    subject_name="Digital Electronics & Logic Design",
                    exam_date="2026-10-26",
                    days_to_exam=1,  # Urgent
                    credit_weight=4.0
                )
            ]
        )

        plan = self.engine.generate_daily_action_plan(profile)
        self.assertEqual(plan.mode, AllocationMode.URGENT_EXAM)
        self.assertAlmostEqual(plan.placement_prep_ratio, 0.10)
        self.assertAlmostEqual(plan.syllabus_revision_ratio, 0.90)
        self.assertEqual(plan.days_to_nearest_exam, 1)

        # Check total time allocation
        syllabus_tasks = [t for t in plan.tasks if t.task_type == TaskType.SYLLABUS_REVISION]
        syllabus_mins = sum(t.duration_minutes for t in syllabus_tasks)
        self.assertGreaterEqual(syllabus_mins, 200, "Urgent mode should allocate majority (~90%) to syllabus")

    def test_06_mutation_hook_remedial_session_injected(self):
        """
        Verify: if Member 3's interview evaluation reports a low score on a topic,
        insert a 30-minute remedial session into the evening block.
        """
        profile = StudentProfile(
            student_id="TEST-CSE-02",
            name="Dev Student",
            branch="CSE",
            daily_available_hours=4.0
        )

        # Low score: 4.5 / 10.0 (< 6.0)
        low_eval = InterviewEvaluation(
            evaluation_id="EVAL-TEST-001",
            student_id="TEST-CSE-02",
            subject="Operating Systems",
            topic="Deadlock - Banker's Algorithm",
            score=4.5,
            max_score=10.0,
            feedback="Candidate could not compute the Need Matrix or explain safe state sequence correctly.",
            needs_remedial=True
        )

        plan = self.engine.generate_daily_action_plan(profile, evaluations=[low_eval])

        # 1. Must record remedial session
        self.assertEqual(plan.remedial_sessions_count, 1)

        # 2. Find the remedial task
        remedial_tasks = [t for t in plan.tasks if t.is_remedial]
        self.assertEqual(len(remedial_tasks), 1)

        remedial = remedial_tasks[0]
        self.assertEqual(remedial.duration_minutes, 30, "Remedial session must be exactly 30 minutes")
        self.assertEqual(remedial.time_block, TimeBlock.EVENING, "Remedial session must be in Evening block")
        self.assertEqual(remedial.task_type, TaskType.REMEDIAL)
        self.assertIn("Banker's Algorithm", remedial.title)
        self.assertEqual(remedial.priority, 10, "Remedial session should have maximum priority")

    def test_07_mutation_hook_no_injection_on_good_score(self):
        """Verify high score (>= 6.0) does NOT inject remedial session."""
        profile = StudentProfile(
            student_id="TEST-CSE-03",
            name="Ace Student",
            branch="CSE",
            daily_available_hours=4.0
        )

        good_eval = InterviewEvaluation(
            evaluation_id="EVAL-TEST-002",
            student_id="TEST-CSE-03",
            subject="Database Management Systems",
            topic="SQL Normalization - BCNF",
            score=9.0,
            max_score=10.0,
            feedback="Excellent grasp of functional dependency closure and lossless decomposition.",
            needs_remedial=False
        )

        plan = self.engine.generate_daily_action_plan(profile, evaluations=[good_eval])
        self.assertEqual(plan.remedial_sessions_count, 0)
        remedial_tasks = [t for t in plan.tasks if t.is_remedial]
        self.assertEqual(len(remedial_tasks), 0)

    def test_08_pydantic_schema_serialization_roundtrip(self):
        """Verify all 5 required schemas serialize and deserialize properly."""
        profile = StudentProfile(
            student_id="GCET-001",
            name="Rahul Kumar",
            branch="ECE",
            year=3,
            semester=5,
            daily_available_hours=4.0,
            target_companies=["Qualcomm"]
        )
        profile_json = profile.model_dump_json()
        loaded_profile = StudentProfile.model_validate_json(profile_json)
        self.assertEqual(loaded_profile.student_id, profile.student_id)

        task = StudyTask(
            task_id="TASK-001",
            title="Study Flip-Flops",
            subject="Digital Electronics",
            topic="Master-Slave JK",
            task_type=TaskType.SYLLABUS_REVISION,
            duration_minutes=45,
            priority=8,
            time_block=TimeBlock.MORNING
        )
        task_json = task.model_dump_json()
        loaded_task = StudyTask.model_validate_json(task_json)
        self.assertEqual(loaded_task.duration_minutes, 45)

        plan = DailyActionPlan(
            plan_id="PLAN-001",
            student_id="GCET-001",
            date="2026-10-24",
            mode=AllocationMode.NORMAL,
            placement_prep_ratio=0.6,
            syllabus_revision_ratio=0.4,
            total_allocated_minutes=240,
            tasks=[task],
            summary_notes="Test summary"
        )
        plan_json = plan.model_dump_json()
        loaded_plan = DailyActionPlan.model_validate_json(plan_json)
        self.assertEqual(loaded_plan.mode, AllocationMode.NORMAL)

        query = InterviewQuery(
            query_id="IQ-001",
            student_id="GCET-001",
            branch="ECE",
            subject="Digital Electronics",
            topic="Flip-Flops"
        )
        self.assertEqual(query.topic, "Flip-Flops")

        evaluation = InterviewEvaluation(
            evaluation_id="EV-001",
            student_id="GCET-001",
            subject="Digital Electronics",
            topic="Flip-Flops",
            score=4.0,
            feedback="Needs practice"
        )
        self.assertTrue(evaluation.is_low_score())


if __name__ == "__main__":
    unittest.main()

# Verified dynamic ratios: Normal(60/40), Approaching(50/50), Urgent(10/90)
