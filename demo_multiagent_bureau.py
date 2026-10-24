"""
demo_multiagent_bureau.py - 1-Click Multi-Agent Demonstration.
Uses Fetch.ai uAgents Bureau to run both CompanyInterviewerAgent and StudentTwinAgent
concurrently in a single event loop, demonstrating end-to-end messaging, 1 FET payment gating,
and Bar Raiser LLM grading.
"""

import os
import sys
import asyncio

# Ensure safe UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uagents import Bureau, Context
from agent_interviewer import interviewer_agent, payment_protocol
from agent_student_twin import student_agent, payment_helper
from models import InterviewQuery

# Match student's payment helper with interviewer's ledger for synchronized sandbox demo
payment_helper._simulated_ledger = payment_protocol._simulated_ledger
payment_helper.processed_transactions = payment_protocol.processed_transactions
payment_helper.agent_address = payment_protocol.agent_address


@student_agent.on_interval(period=10.0)
async def run_scheduled_drill_flow(ctx: Context):
    """Fires initial drill query from StudentTwinAgent to CompanyInterviewerAgent."""
    # Only run once at startup
    if getattr(ctx, "_has_run", False):
        return
    ctx._has_run = True

    ctx.logger.info("\n" + "=" * 65)
    ctx.logger.info("🎬 HACKATHON LIVE DEMO: STUDENT TWIN -> INTERVIEWER AGENT")
    ctx.logger.info("=" * 65)

    # Demo 1: Free Standard Qualcomm Verilog Question
    ctx.logger.info("📍 STEP 1: Requesting Standard Qualcomm Verilog Drill...")
    query = InterviewQuery(
        student_id=str(student_agent.address),
        company="qualcomm",
        tier="standard",
        question_id="qualcomm_verilog_01"
    )
    await ctx.send(interviewer_agent.address, query)

    # Delay before triggering Tier-1 demonstration
    await asyncio.sleep(4)

    # Demo 2: Tier-1 Amazon Bar Raiser Drill (Locked without payment)
    ctx.logger.info("\n📍 STEP 2: Requesting Tier-1 Amazon Bar Raiser Mock Pack (Unpaid)...")
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
    print("🚀 Initializing Fetch.ai uAgents Bureau for Multi-Agent Demo")
    print(f"Company Interviewer Agent: {interviewer_agent.address}")
    print(f"Student Twin Agent:        {student_agent.address}")
    print(f"Interviewer FET Wallet:    {payment_protocol.agent_address}")
    print("=" * 70)

    bureau = Bureau(port=8000)
    bureau.add(interviewer_agent)
    bureau.add(student_agent)
    bureau.run()


if __name__ == "__main__":
    main()
