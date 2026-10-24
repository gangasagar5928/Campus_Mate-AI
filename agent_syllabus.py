"""
agent_syllabus.py - Departmental Syllabus Agent (Worker Node)
Lead: Member 2 (Syllabus Engine & Balancing Algorithm Lead)
Platform: Fetch.ai uAgents Framework
Port: 8002
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional

# Ensure event loop exists on Python 3.12/3.14+
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from uagents import Agent, Context
from schemas import (
    PlanRequest,
    PlanResponse,
    SyllabusRequest,
    DailyActionPlan,
    StudyTask,
    StudentProfile,
    ExamSchedule,
    InterviewEvaluation,
    CurriculumQueryRequest,
    CurriculumQueryResponse,
    AllocationMode
)
from load_balancer import balancer_engine

# Configuration
AGENT_NAME = os.getenv("SYLLABUS_AGENT_NAME", "campusmate_syllabus_agent")
AGENT_SEED = os.getenv("SYLLABUS_AGENT_SEED", "campusmate_syllabus_seed_gcet_2026")
PORT = int(os.getenv("SYLLABUS_PORT", "8002"))

syllabus_agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    endpoint=[f"http://127.0.0.1:{PORT}/submit"],
    mailbox=False,
    loop=loop
)


@syllabus_agent.on_event("startup")
async def handle_startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info("[CampusMate] Departmental Syllabus Agent Active")
    ctx.logger.info(f"Agent Name    : {syllabus_agent.name}")
    ctx.logger.info(f"Agent Address : {syllabus_agent.address}")
    ctx.logger.info(f"Listening Port: {PORT}")
    ctx.logger.info("=" * 60)


@syllabus_agent.on_message(model=PlanRequest)
async def handle_plan_request(ctx: Context, sender: str, req: PlanRequest):
    """Primary handler for Member 2 PlanRequest contract."""
    ctx.logger.info(f"[Syllabus] Received PlanRequest from {sender} for {req.student_profile.name}")
    try:
        plan = balancer_engine.generate_daily_action_plan(
            profile=req.student_profile,
            evaluations=req.recent_evaluations,
            target_date=req.requested_date
        )
        resp = PlanResponse(request_id=req.request_id, success=True, plan=plan)
    except Exception as exc:
        ctx.logger.error(f"[Syllabus] Error generating plan: {exc}")
        resp = PlanResponse(request_id=req.request_id, success=False, error_message=str(exc))

    await ctx.send(sender, resp)


@syllabus_agent.on_message(model=SyllabusRequest)
async def handle_legacy_syllabus_request(ctx: Context, sender: str, req: SyllabusRequest):
    """Compatibility handler for StudentTwinAgent's SyllabusRequest."""
    ctx.logger.info(f"[Syllabus] Received SyllabusRequest for {req.branch} (Sem {req.semester}) from {sender}")
    
    profile = StudentProfile(
        student_id=req.student_id,
        name="Campus Student",
        branch=req.branch.upper(),
        semester=req.semester,
        daily_available_hours=req.daily_available_hours,
        target_companies=[req.target_company],
        upcoming_exams=[
            ExamSchedule(
                subject_code="CORE-SEM",
                subject_name=f"{req.branch} Core Theory",
                exam_date="2026-10-27",
                days_to_exam=req.days_to_midterm,
                credit_weight=4.0
            )
        ]
    )

    plan = balancer_engine.generate_daily_action_plan(profile)
    plan.academic_ratio = plan.syllabus_revision_ratio
    plan.placement_ratio = plan.placement_prep_ratio
    plan.notes = plan.summary_notes
    for t in plan.tasks:
        t.task_name = t.title
        t.category = "Syllabus Revision" if t.task_type.value == "syllabus_revision" else "Placement Prep"

    ctx.logger.info(f"[Syllabus] Dispatching DailyActionPlan ({plan.mode.value}) to {sender}...")
    await ctx.send(sender, plan)


@syllabus_agent.on_message(model=CurriculumQueryRequest)
async def handle_curriculum_query(ctx: Context, sender: str, query: CurriculumQueryRequest):
    """Responds with prioritized curriculum units for a branch."""
    ctx.logger.info(f"[Syllabus] Curriculum query for branch {query.branch}")
    profile = StudentProfile(
        student_id="QUERY-CALLER",
        name="Query Profile",
        branch=query.branch.upper(),
        upcoming_exams=[
            ExamSchedule(
                subject_code=query.subject_code or "QUERY",
                subject_name="Query Subject",
                exam_date="2026-10-30",
                days_to_exam=query.days_to_exam if query.days_to_exam is not None else 10,
                credit_weight=4.0
            )
        ] if query.days_to_exam is not None else []
    )
    priorities = balancer_engine.calculate_priorities_for_profile(profile)
    resp = CurriculumQueryResponse(branch=query.branch, priorities=priorities)
    await ctx.send(sender, resp)


@syllabus_agent.on_message(model=InterviewEvaluation)
async def handle_interview_eval(ctx: Context, sender: str, msg: InterviewEvaluation):
    """Direct evaluation ingestion from Member 3 Interview Agent."""
    ctx.logger.info(f"[Syllabus] Received evaluation from {sender}: Topic={msg.topic}, Score={msg.score}")


if __name__ == "__main__":
    print("[CampusMate] Starting Departmental Syllabus Agent on Port 8002...")
    syllabus_agent.run()
