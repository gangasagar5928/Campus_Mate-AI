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
