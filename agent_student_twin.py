"""
agent_student_twin.py - Student Twin Agent (Orchestrator Node)
Fetch.ai uAgent representing the student candidate.
Discovered via ASI:One through official Agent Chat Protocol (ACP).
Coordinates:
- Departmental Syllabus Agent (Curriculum balance & proximity calculations)
- Company Interviewer Agent (Technical drills, payment protocol & rubric grading)
- Emits ASI1 Interactive UI cards (Intake Form, Action Plan, Scorecard)
"""

import os
import sys
import time
import json
import urllib.parse
import asyncio
from typing import Dict, Any, List, Optional

# Ensure safe UTF-8 output on all operating systems
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure event loop exists on Python 3.12/3.14+
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage as ACPChatMessage,
    ChatAcknowledgement,
    TextContent
)
from models import (
    InterviewQuery,
    InterviewQuestionResponse,
    InterviewAnswerSubmission,
    InterviewEvaluation,
    ChatMessage as LegacyChatMessage,
    StudentProfile,
    SyllabusRequest,
    DailyActionPlan as ModelDailyActionPlan,
    StudyTask as ModelStudyTask,
    ScheduleMutation
)
from schemas import (
    DailyActionPlan as SchemaDailyActionPlan,
    StudyTask as SchemaStudyTask
)
from payment_protocol import PaymentProtocol
from cards_templates import (
    create_intake_form_card,
    create_action_plan_card,
    create_interview_drill_card,
    create_evaluation_scorecard,
    card_to_message_payload
)

# Configuration
STUDENT_AGENT_NAME = os.getenv("AGENT_NAME", "campusmate_student_twin")
STUDENT_PORT = int(os.getenv("PORT", "8000"))
STUDENT_SEED = os.getenv("AGENT_SEED", "campusmate_student_twin_secret_seed_gcet_2026")
USE_MAILBOX = os.getenv("AGENT_MAILBOX", "false").lower() in ("true", "1", "yes")
MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY", None)
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "")

INTERVIEWER_ADDRESS = os.getenv("INTERVIEWER_AGENT_ADDRESS", "")
SYLLABUS_ADDRESS = os.getenv("SYLLABUS_AGENT_ADDRESS", "")

agent_kwargs = {
    "name": STUDENT_AGENT_NAME,
    "port": STUDENT_PORT,
    "seed": STUDENT_SEED,
    "mailbox": USE_MAILBOX,
    "loop": loop
}
if AGENT_ENDPOINT:
    agent_kwargs["endpoint"] = [AGENT_ENDPOINT]
if MAILBOX_KEY and USE_MAILBOX:
    agent_kwargs["agentverse"] = {"key": MAILBOX_KEY}

student_agent = Agent(**agent_kwargs)
student_protocol = Protocol(name="StudentTwinProtocol", version="1.0.0")

# Official Agent Chat Protocol (ACP) for Agentverse & ASI:One
chat_proto = Protocol(spec=chat_protocol_spec)
payment_helper = PaymentProtocol()

# Pre-formulated high-quality candidate answers for automated Bureau demo
SAMPLE_ANSWERS = {
    "qualcomm_verilog_01": (
        "In Verilog, blocking assignments (=) execute sequentially and block execution of subsequent statements "
        "within the procedural block. Non-blocking assignments (<=) evaluate the right-hand side in the active event queue "
        "and schedule the assignment update in the Non-Blocking Assignment (NBA) region. In clocked sequential always blocks, "
        "mixing (=) and (<=) causes non-deterministic simulation-synthesis race mismatches across flip-flops."
    ),
    "tcs_prime_cpp_01": (
        "In C++, raw pointers require manual memory management with delete, creating leak vulnerabilities. Smart pointers "
        "automate lifetime via RAII: std::unique_ptr provides exclusive zero-overhead ownership, while std::shared_ptr maintains "
        "a reference-counted control block. Cyclic shared_ptr references prevent ref-count from reaching zero; std::weak_ptr "
        "breaks cyclical dependencies by acting as a non-owning observer."
    ),
    "amazon_bst_01": (
        "Validating BST requires validating range bounds (min, max) recursively for every subtree rather than just local "
        "node.left.val < node.val < node.right.val. LCA in a BST runs in O(h) time by iteratively traversing: if both targets "
        "are smaller, go left; if larger, go right; the point of divergence is the LCA."
    ),
    "amazon_bar_raiser_01": (
        "For Part A (Distributed Cache Architecture): Implement consistent hashing with virtual nodes to avoid hot spots, "
        "LRU eviction via hashmap and doubly-linked list, and distributed lease locks with probabilistic early expiration "
        "to prevent cache stampede.\n\n"
        "For Part B (Leadership Principles): On Prime Day, a cache stampede spiked P99 latency. Demonstrating Customer Obsession "
        "and Dive Deep, I identified TTL synchronization across shards, applied a two-way door patch introducing 15% random jitter, "
        "and restored sub-15ms latency within 5 minutes."
    )
}

# Conversational state store per student/sender
class SessionState:
    def __init__(self, sender_id: str):
        self.sender_id = sender_id
        self.stage = "INIT"
        self.profile = StudentProfile()
        self.current_plan = None
        self.last_question_id = None
        self.session_id = None
        self.last_evaluation = None
        self.mutated_plan = None

sessions = {}

def get_session(sender_id: str) -> SessionState:
    if sender_id not in sessions:
        sessions[sender_id] = SessionState(sender_id)
    return sessions[sender_id]


def parse_payload(raw_text: str):
    raw_text = raw_text.strip()
    if (raw_text.startswith("{") and raw_text.endswith("}")) or raw_text.startswith("```json"):
        clean = raw_text
        if clean.startswith("```json"):
            clean = clean.replace("```json", "", 1).rstrip("`").strip()
        try:
            return json.loads(clean)
        except Exception:
            pass
    if "=" in raw_text and ("&" in raw_text or raw_text.startswith("action=")):
        try:
            parsed = urllib.parse.parse_qs(raw_text)
            return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        except Exception:
            pass
    lower = raw_text.lower()
    if "start" in lower and ("drill" in lower or "interview" in lower or "qualcomm" in lower):
        company = "qualcomm"
        if "amazon" in lower:
            company = "amazon"
        elif "tcs" in lower:
            company = "tcs_prime"
        return {"action": "start_drill", "company": company}
    return {"raw_text": raw_text}


@student_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"Student Twin Agent Online: {STUDENT_AGENT_NAME}")
    ctx.logger.info(f"Student Agent Address: {student_agent.address}")
    ctx.logger.info(f"Endpoint: {AGENT_ENDPOINT or 'None'}")
    ctx.logger.info(f"Agentverse Mailbox: {'ENABLED' if USE_MAILBOX else 'DISABLED'}")
    ctx.logger.info(f"Agent Chat Protocol (ACP): PUBLISHED (0.3.0)")
    ctx.logger.info("=" * 60)


# ==============================================================================
# Official Agent Chat Protocol (ACP) Handlers for Agentverse & ASI:One
# ==============================================================================
@chat_proto.on_message(model=ACPChatMessage)
async def handle_official_acp_message(ctx: Context, sender: str, msg: ACPChatMessage):
    ctx.logger.info(f"[ACP 0.3.0] Received message from {sender}")
    # 1. Send mandatory acknowledgement
    ack = ChatAcknowledgement(acknowledged_msg_id=msg.msg_id)
    await ctx.send(sender, ack)

    session = get_session(sender)
    user_text = msg.text()
    parsed = parse_payload(user_text)

    # A. Profile setup postback (Card 1)
    if "branch" in parsed or parsed.get("action") == "submit_profile":
        branch = parsed.get("branch", session.profile.branch)
        sem = int(parsed.get("semester", session.profile.semester))
        comp = parsed.get("target_company", session.profile.target_company)
        hrs = float(parsed.get("daily_hours", session.profile.daily_available_hours))
        days = int(parsed.get("days_to_exam", session.profile.days_to_midterm))

        session.profile = StudentProfile(
            branch=branch, semester=sem, target_company=comp,
            daily_available_hours=hrs, days_to_midterm=days
        )
        session.stage = "PROFILE_SET"

        if SYLLABUS_ADDRESS:
            req = SyllabusRequest(
                student_id=sender, branch=branch, semester=sem,
                target_company=comp, daily_available_hours=hrs, days_to_midterm=days
            )
            await ctx.send(SYLLABUS_ADDRESS, req)
            return
        else:
            p_ratio = 0.50 if days >= 3 else 0.10
            a_ratio = 1.0 - p_ratio
            plan = ModelDailyActionPlan(
                student_id=sender,
                academic_ratio=a_ratio,
                placement_ratio=p_ratio,
                tasks=[
                    ModelStudyTask(task_name=f"Digital Electronics Unit 3 (Exam in {days} days)", duration_minutes=45, category="Syllabus Revision", priority="Urgent"),
                    ModelStudyTask(task_name=f"{comp} Drill: Technical Problem Solving", duration_minutes=45, category="Placement Prep", priority="High")
                ],
                notes=f"Proximity: {days} days"
            )
            session.current_plan = plan
            card = create_action_plan_card(plan, comp)
            reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(card))])
            await ctx.send(sender, reply)
            return

    # B. Start drill action (Card 2)
    if parsed.get("action") == "start_drill":
        comp = parsed.get("company", session.profile.target_company).lower()
        if INTERVIEWER_ADDRESS:
            q = InterviewQuery(student_id=sender, company=comp, tier="standard")
            await ctx.send(INTERVIEWER_ADDRESS, q)
            return
        else:
            drill_card = create_interview_drill_card(
                company=comp,
                topic="Verilog HDL Blocking Assignments",
                question_text="Explain the difference between blocking (=) and non-blocking (<=) procedural assignments in Verilog."
            )
            session.stage = "IN_DRILL"
            reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(drill_card))])
            await ctx.send(sender, reply)
            return

    # C. Submit answer (Drill Card)
    if "student_answer" in parsed or session.stage == "IN_DRILL":
        ans = parsed.get("student_answer") or parsed.get("raw_text") or user_text
        if INTERVIEWER_ADDRESS:
            sub = InterviewAnswerSubmission(
                session_id=session.session_id or "demo_session",
                question_id=session.last_question_id or "qualcomm_verilog_01",
                student_id=sender,
                student_answer=ans
            )
            await ctx.send(INTERVIEWER_ADDRESS, sub)
            return
        else:
            eval_mock = InterviewEvaluation(
                session_id="mock",
                question_id="qualcomm_verilog_01",
                student_id=sender,
                company=session.profile.target_company,
                score=8.5,
                score_badge="Hire / Strong Technical Fit",
                rubric_breakdown={"concept_correctness": 9.0, "synthesis_timing_awareness": 8.0},
                strengths=["Accurate explanation of NBA evaluation queue"],
                synthesis_risks=["Potential race condition when mixing assignments"],
                remedial_topics=["Verilog Synthesis & Race Hazards"],
                feedback_summary="Excellent technical depth on procedural assignments.",
                timestamp="2026-10-24T12:00:00Z"
            )
            card = create_evaluation_scorecard(eval_mock)
            reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(card))])
            await ctx.send(sender, reply)
            return

    # D. Default Discovery / Probe
    welcome = (
        "Welcome to **CampusMate AI** — Your Autonomous Academic & Career Agent.\n\n"
        "Balancing university coursework with target company recruitment tracks."
    )
    intake_card = create_intake_form_card()
    combined_payload = welcome + "\n\n" + card_to_message_payload(intake_card)
    reply = ACPChatMessage(content=[TextContent(text=combined_payload)])
    await ctx.send(sender, reply)


@chat_proto.on_message(model=ChatAcknowledgement)
async def handle_official_acp_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"[ACP 0.3.0] Acknowledged by {sender}: {msg.acknowledged_msg_id}")


# ==============================================================================
# Inter-Agent Handlers (Responses from Syllabus Agent)
# ==============================================================================
@student_agent.on_message(model=SchemaDailyActionPlan)
async def handle_schema_syllabus_plan(ctx: Context, sender: str, plan: SchemaDailyActionPlan):
    ctx.logger.info(f"📥 Received DailyActionPlan from Syllabus Agent ({sender})")
    session = get_session(plan.student_id)
    session.current_plan = plan
    session.stage = "PLAN_READY"

    if plan.student_id.startswith("agent1") and plan.student_id != str(student_agent.address):
        card = create_action_plan_card(plan, session.profile.target_company)
        reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(card))])
        await ctx.send(plan.student_id, reply)


@student_agent.on_message(model=ModelDailyActionPlan)
async def handle_model_syllabus_plan(ctx: Context, sender: str, plan: ModelDailyActionPlan):
    ctx.logger.info(f"📥 Received DailyActionPlan from Syllabus Agent ({sender})")
    session = get_session(plan.student_id)
    session.current_plan = plan
    session.stage = "PLAN_READY"

    if plan.student_id.startswith("agent1") and plan.student_id != str(student_agent.address):
        card = create_action_plan_card(plan, session.profile.target_company)
        reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(card))])
        await ctx.send(plan.student_id, reply)


# ==============================================================================
# Inter-Agent Handlers (Responses from Interviewer Agent)
# ==============================================================================
@student_protocol.on_message(model=InterviewQuestionResponse)
async def handle_question_response(ctx: Context, sender: str, msg: InterviewQuestionResponse):
    ctx.logger.info(f"📩 Received Interview Response from Company Interviewer ({sender}): {msg.question_id}")
    session = get_session(msg.session_id)
    session.last_question_id = msg.question_id
    session.session_id = msg.session_id
    session.stage = "IN_DRILL"

    if not msg.is_unlocked:
        ctx.logger.warning(f"⚠️ Pack Locked! Required fee: {msg.required_fee_fet} FET")
        tx_hash = payment_helper.simulate_transfer(
            sender_address=str(student_agent.address),
            amount_fet=1.0,
            memo=f"Unlock {msg.company} {msg.track}"
        )
        ctx.logger.info(f"✅ Payment Broadcast! Tx Hash: {tx_hash}")

        retry_query = InterviewQuery(
            student_id=str(student_agent.address),
            company=msg.company,
            tier="tier-1",
            question_id=msg.question_id,
            payment_tx_hash=tx_hash,
            session_id=msg.session_id
        )
        await ctx.send(sender, retry_query)
        return

    # Question is unlocked
    if session.sender_id and session.sender_id.startswith("agent1") and session.sender_id != str(student_agent.address):
        card = create_interview_drill_card(
            company=msg.company,
            topic=msg.topic,
            question_text=msg.question_text,
            tier=msg.tier
        )
        reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(card))])
        await ctx.send(session.sender_id, reply)
        return

    # Automated Bureau Demo: formulate answer and submit to interviewer
    answer_text = SAMPLE_ANSWERS.get(
        msg.question_id,
        "A comprehensive technical analysis detailing system architecture, syntax nuances, and synthesis implications."
    )
    submission = InterviewAnswerSubmission(
        session_id=msg.session_id,
        question_id=msg.question_id,
        student_id=str(student_agent.address),
        student_answer=answer_text
    )
    await ctx.send(sender, submission)


@student_protocol.on_message(model=InterviewEvaluation)
async def handle_evaluation_result(ctx: Context, sender: str, msg: InterviewEvaluation):
    ctx.logger.info(f"🏆 RECEIVED INTERVIEW EVALUATION: Score {msg.score} / 10.0 ({msg.score_badge})")
    session = get_session(msg.session_id)
    session.last_evaluation = msg
    session.stage = "EVALUATED"

    if session.sender_id and session.sender_id.startswith("agent1") and session.sender_id != str(student_agent.address):
        card = create_evaluation_scorecard(msg)
        reply = ACPChatMessage(content=[TextContent(text=card_to_message_payload(card))])
        await ctx.send(session.sender_id, reply)


# Include Protocols
student_agent.include(student_protocol)
student_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"[Starting Student Twin Agent on port {STUDENT_PORT}...]")
    student_agent.run()
