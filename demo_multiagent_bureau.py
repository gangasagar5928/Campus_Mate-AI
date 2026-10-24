"""
demo_multiagent_bureau.py - 1-Click Multi-Agent Demonstration.
Uses Fetch.ai uAgents Bureau to run all 3 agents:
1. StudentTwinAgent (Orchestrator Node)
2. DepartmentalSyllabusAgent (Syllabus & Proximity Engine)
3. CompanyInterviewerAgent (Technical Drills & Payment Protocol)
concurrently in a single event loop.
"""

import os
import sys
import asyncio

# Ensure safe UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure event loop exists on Python 3.12/3.14+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from uagents import Bureau, Context
from agent_interviewer import interviewer_agent, payment_protocol
from agent_student_twin import student_agent, payment_helper
from agent_syllabus import syllabus_agent
from models import InterviewQuery, SyllabusRequest

# Match student's payment helper with interviewer's ledger for synchronized sandbox demo
payment_helper._simulated_ledger = payment_protocol._simulated_ledger
payment_helper.processed_transactions = payment_protocol.processed_transactions
payment_helper.agent_address = payment_protocol.agent_address


@student_agent.on_interval(period=10.0)
async def run_scheduled_drill_flow(ctx: Context):
    """Fires initial multi-agent queries across Syllabus and Interviewer agents."""
    if getattr(ctx, "_has_run", False):
        return
    ctx._has_run = True

    ctx.logger.info("\n" + "=" * 65)
    ctx.logger.info("🎬 HACKATHON LIVE DEMO: CAMPUSMATE AI MULTI-AGENT WORKFLOW")
    ctx.logger.info("=" * 65)

    # Demo 1: Syllabus Allocation Query to Syllabus Agent
    ctx.logger.info("📍 STEP 1: Querying Departmental Syllabus Agent for ECE Midterm Proximity...")
    syl_req = SyllabusRequest(
        student_id=str(student_agent.address),
        branch="ECE",
        semester=6,
        target_company="Qualcomm",
        daily_available_hours=3.0,
        days_to_midterm=4
    )
    await ctx.send(syllabus_agent.address, syl_req)

    await asyncio.sleep(3)

    # Demo 2: Free Standard Qualcomm Verilog Question to Interviewer Agent
    ctx.logger.info("\n📍 STEP 2: Requesting Standard Qualcomm Verilog Drill from Interviewer Agent...")
    query = InterviewQuery(
        student_id=str(student_agent.address),
        company="qualcomm",
        tier="standard",
        question_id="qualcomm_verilog_01"
    )
    await ctx.send(interviewer_agent.address, query)

    await asyncio.sleep(4)

    # Demo 3: Tier-1 Amazon Bar Raiser Drill (Locked without payment)
    ctx.logger.info("\n📍 STEP 3: Requesting Tier-1 Amazon Bar Raiser Mock Pack (Unpaid -> 1 FET Gating)...")
    tier1_query = InterviewQuery(
        student_id=str(student_agent.address),
        company="amazon",
        tier="tier-1",
        question_id="amazon_bar_raiser_01",
        payment_tx_hash=None
    )
    await ctx.send(interviewer_agent.address, tier1_query)


def main():
    print("=" * 70)
    print("🚀 Initializing Fetch.ai uAgents Bureau for CampusMate AI")
    print(f"1. Student Twin Agent:        {student_agent.address}")
    print(f"2. Departmental Syllabus:     {syllabus_agent.address}")
    print(f"3. Company Interviewer Agent: {interviewer_agent.address}")
    print(f"Interviewer FET Wallet:       {payment_protocol.agent_address}")
    print("=" * 70)

    bureau = Bureau(port=8000)
    bureau.add(student_agent)
    bureau.add(syllabus_agent)
    bureau.add(interviewer_agent)
    bureau.run()


if __name__ == "__main__":
    main()
