"""
agent_syllabus.py - Departmental Syllabus Agent (Worker Node)
Lead: Member 2 (Syllabus Engine & Balancing Algorithm Lead)
Platform: Fetch.ai uAgents

Responsibilities:
1. Houses structured university curriculum (AKTU/GCET curriculum.json).
2. Calculates exam proximity and allocates daily study buffers dynamically:
   - T_exam > 7 days  => Placement: 70%, Syllabus: 30%
   - 3 <= T_exam <= 7 => Placement: 50%, Syllabus: 50%
   - T_exam < 3 days  => Placement: 10%, Syllabus: 90% (Cram Mode)
3. Replies with DailyActionPlan to StudentTwinAgent.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Tuple

# Ensure event loop exists on Python 3.12/3.14+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from uagents import Agent, Context
from models import SyllabusRequest, DailyActionPlan, StudyTask

# Configuration
AGENT_NAME = os.getenv("SYLLABUS_AGENT_NAME", "campusmate_syllabus_agent")
AGENT_SEED = os.getenv("SYLLABUS_AGENT_SEED", "campusmate_syllabus_seed_gcet_2026")
PORT = int(os.getenv("SYLLABUS_PORT", "8002"))

syllabus_agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    mailbox=False
)

CURRICULUM_PATH = os.path.join(os.path.dirname(__file__), "curriculum.json")

def load_curriculum() -> Dict[str, Any]:
    if os.path.exists(CURRICULUM_PATH):
        with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

curriculum_db = load_curriculum()


def compute_schedule(req: SyllabusRequest) -> DailyActionPlan:
    """
    Deterministic Study Allocation Formula:
    T_exam > 7 days  => Placement: 70%, Syllabus: 30%
    3 <= T_exam <= 7 => Placement: 50%, Syllabus: 50%
    T_exam < 3 days  => Placement: 10%, Syllabus: 90% (Cram Mode)
    """
    t_exam = req.days_to_midterm
    total_minutes = int(req.daily_available_hours * 60)

    if t_exam > 7:
        p_ratio, a_ratio = 0.70, 0.30
    elif 3 <= t_exam <= 7:
        p_ratio, a_ratio = 0.50, 0.50
    else:
        p_ratio, a_ratio = 0.10, 0.90

    acad_mins = int(total_minutes * a_ratio)
    place_mins = int(total_minutes * p_ratio)
    is_cram = t_exam < 3

    tasks: List[StudyTask] = []

    # 1. Academic Task from curriculum DB
    branch = req.branch.upper()
    sem_str = str(req.semester)
    branch_data = curriculum_db.get(branch, {}).get(sem_str, {})
    subjects = branch_data.get("subjects", [])

    if subjects:
        # Pick highest difficulty unit for highest yield revision
        highest_unit = None
        for sub in subjects:
            for u in sub.get("units", []):
                if not highest_unit or u.get("difficulty", 0) > highest_unit.get("difficulty", 0):
                    highest_unit = {
                        "subject": sub.get("name"),
                        "unit": u.get("unit_num"),
                        "title": u.get("title")
                    }

        acad_title = f"{highest_unit['subject']} - Unit {highest_unit['unit']}: {highest_unit['title']}"
    else:
        acad_title = f"{branch} Core Theoretical Modules"

    tasks.append(StudyTask(
        task_name=f"{acad_title} (Exam in {t_exam} days)",
        duration_minutes=min(60, acad_mins) if is_cram else min(45, acad_mins),
        category="Syllabus Revision",
        priority="Urgent" if is_cram or t_exam <= 4 else "High"
    ))

    if acad_mins > 60:
        tasks.append(StudyTask(
            task_name="Departmental Sessional PYQs & Lab Practical Revision",
            duration_minutes=acad_mins - 60,
            category="Syllabus Revision",
            priority="High" if is_cram else "Medium"
        ))

    # 2. Placement Task based on target company
    company = req.target_company.title()
    if "qualcomm" in company.lower():
        drill_title = "Qualcomm Drill: Verilog HDL & Static Timing Analysis"
    elif "amazon" in company.lower():
        drill_title = "Amazon Drill: Distributed Caching & BST Algorithms"
    elif "tcs" in company.lower():
        drill_title = "TCS Prime Drill: C++ Vtables, Pointers & Ring Buffer"
    else:
        drill_title = f"{company} Technical Mock Drill: Core Problem Solving"

    if place_mins > 0:
        tasks.append(StudyTask(
            task_name=drill_title,
            duration_minutes=min(45, place_mins),
            category="Placement Prep",
            priority="Low" if is_cram else "High"
        ))

    if place_mins > 45:
        tasks.append(StudyTask(
            task_name=f"{company} Quantitative Aptitude & Speed Drills",
            duration_minutes=place_mins - 45,
            category="Placement Prep",
            priority="Medium"
        ))

    return DailyActionPlan(
        student_id=req.student_id,
        academic_ratio=a_ratio,
        placement_ratio=p_ratio,
        tasks=tasks,
        notes=f"AKTU/GCET {branch} Sem {req.semester} | T_exam={t_exam} days | Cram={is_cram}"
    )


@syllabus_agent.on_event("startup")
async def handle_startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info("[CampusMate] Departmental Syllabus Agent Active")
    ctx.logger.info(f"Agent Name    : {syllabus_agent.name}")
    ctx.logger.info(f"Agent Address : {syllabus_agent.address}")
    ctx.logger.info(f"Listening Port: {PORT}")
    ctx.logger.info("=" * 60)


@syllabus_agent.on_message(model=SyllabusRequest)
async def handle_syllabus_request(ctx: Context, sender: str, req: SyllabusRequest):
    ctx.logger.info(f"[Syllabus] Received request for {req.branch} (Sem {req.semester}) from {sender}")
    plan = compute_schedule(req)
    ctx.logger.info(f"[Syllabus] Dispatching computed DailyActionPlan to {sender}...")
    await ctx.send(sender, plan)


if __name__ == "__main__":
    print("[CampusMate] Starting Departmental Syllabus Agent...")
    syllabus_agent.run()
