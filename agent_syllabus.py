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
