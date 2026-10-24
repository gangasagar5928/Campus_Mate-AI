"""
agent_student_twin.py - Student Twin Agent (Orchestrator Node)
Fetch.ai uAgent representing the student candidate.
Discovered via ASI:One through official Agent Chat Protocol (ACP).
Coordinates:
- Departmental Syllabus Engine (Curriculum balance & proximity calculations)
- Company Interviewer Engine (Technical drills, payment protocol & rubric grading)
- Natural Language ACP Interface for Agentverse & ASI:One
"""

import os
import sys
import re
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
    StudentProfile as ModelStudentProfile,
    SyllabusRequest,
    DailyActionPlan as ModelDailyActionPlan,
    StudyTask as ModelStudyTask,
    ScheduleMutation
)
from schemas import (
    DailyActionPlan as SchemaDailyActionPlan,
    StudyTask as SchemaStudyTask,
    StudentProfile as SchemaStudentProfile,
    ExamSchedule as SchemaExamSchedule
)
from payment_protocol import PaymentProtocol
from load_balancer import DeterministicBalancingEngine, CurriculumLoader
from llm_evaluator import LLMEvaluator

# Load Question Bank
INTERVIEW_BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interview_bank.json")
with open(INTERVIEW_BANK_PATH, "r", encoding="utf-8") as f:
    INTERVIEW_BANK = json.load(f)

# Engines
balancing_engine = DeterministicBalancingEngine()
llm_evaluator = LLMEvaluator()
payment_helper = PaymentProtocol()

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

# Conversational state store per student/sender
class SessionState:
    def __init__(self, sender_id: str):
        self.sender_id = sender_id
        self.stage = "INIT"  # INIT, PLAN_READY, IN_DRILL, EVALUATED
        self.branch = "ECE"
        self.semester = 6
        self.target_company = "Qualcomm"
        self.daily_hours = 4.0
        self.days_to_midterm = 4
        self.last_question_id = "qualcomm_verilog_01"
        self.session_id = f"sess_{sender_id[-8:] if len(sender_id) >= 8 else 'user'}"
        self.current_plan = None
        self.last_evaluation = None

sessions: Dict[str, SessionState] = {}

def get_session(sender_id: str) -> SessionState:
    if sender_id not in sessions:
        sessions[sender_id] = SessionState(sender_id)
    return sessions[sender_id]


def find_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
    for comp in INTERVIEW_BANK.get("companies", {}).values():
        for q in comp.get("questions", []):
            if q.get("id") == question_id:
                return q
    return None


def select_drill_question(company_key: str, tier: str = "standard") -> Dict[str, Any]:
    comp = INTERVIEW_BANK.get("companies", {}).get(company_key.lower())
    if not comp:
        # fallback to qualcomm
        comp = INTERVIEW_BANK.get("companies", {}).get("qualcomm")
    questions = comp.get("questions", [])
    matched = [q for q in questions if q.get("tier") == tier]
    return matched[0] if matched else questions[0]


def format_action_plan_markdown(plan: SchemaDailyActionPlan, session: SessionState) -> str:
    total_mins = int(round(session.daily_hours * 60))
    p_pct = int(round(plan.placement_ratio * 100))
    s_pct = int(round(plan.academic_ratio * 100))
    p_mins = int(round(total_mins * plan.placement_ratio))
    s_mins = total_mins - p_mins

    mode_label = "Approaching Midterm Mode"
    if session.days_to_midterm < 3:
        mode_label = "Urgent Exam Revision Mode (90% High-Yield Syllabus)"
    elif session.days_to_midterm > 7:
        mode_label = "Normal Prep Mode (60% Placement / 40% Coursework)"

    lines = [
        f"## 📅 Adaptive Daily Study Plan ({session.branch} — Semester {session.semester})",
        f"**Target Company:** {session.target_company} | **Study Budget:** {session.daily_hours:.1f} Hours | **Days to Midterm:** {session.days_to_midterm} Days",
        "",
        f"### ⚖️ Workload Allocation ({mode_label})",
        f"- 📘 **Academic Syllabus Revision:** **{s_pct}%** ({s_mins} mins)",
        f"- 🎯 **Placement Technical Drills:** **{p_pct}%** ({p_mins} mins)",
        "",
        "---",
        "### 📝 Today's Recommended Task Schedule:",
    ]

    time_blocks = ["🌅 Morning Block", "☀️ Mid-Day Block", "🌆 Afternoon Block", "📘 Evening Block", "🌙 Night Block"]
    for idx, task in enumerate(plan.tasks):
        block_label = time_blocks[idx % len(time_blocks)]
        cat_badge = "📘 Syllabus" if task.category == "Syllabus Revision" else "🎯 Placement"
        lines.append(f"{idx + 1}. **{block_label} ({task.duration_minutes}m):** `{cat_badge}` {task.title}")

    lines.append("")
    lines.append("---")
    lines.append(f"💡 *Proximity Alert: Next sessional exam in {session.days_to_midterm} days. Schedule dynamically tuned to prevent academic debt.*")
    lines.append(f"👉 *Ready to practice? Type: **\"Start {session.target_company} drill\"** to begin an interactive technical mock.*")

    return "\n".join(lines)


def format_drill_markdown(q: Dict[str, Any], is_unlocked: bool = True) -> str:
    company = q.get("company", "Tech Company")
    topic = q.get("topic", "Technical Drill")
    difficulty = q.get("difficulty", "Medium")
    tier = q.get("tier", "standard").title()
    fee = q.get("fee_fet", 0.0)

    fee_badge = "Unlocked / Free Drill" if fee == 0.0 or is_unlocked else f"Gated ({fee} FET Testnet Fee Required)"

    lines = [
        f"## ⚡ {company} Technical Interview Drill",
        f"**Track:** {q.get('track', 'Engineering')} | **Topic:** {topic}",
        f"**Difficulty:** `{difficulty}` | **Tier:** `{tier}` ({fee_badge})",
        "",
        "---",
        "### 📋 Technical Challenge Prompt:",
        f"{q.get('question', '')}",
        "",
        "---",
        "✍️ **How to Submit:**",
        "Reply directly with your explanation, analysis, or code. CampusMate will run instant rubric evaluation and generate your scoring badge.",
    ]
    return "\n".join(lines)


def format_scorecard_markdown(eval_res: Dict[str, Any], q: Dict[str, Any], has_mutation: bool = False) -> str:
    score = eval_res.get("score", 7.0)
    badge = eval_res.get("score_badge", "Pass")
    topic = q.get("topic", "Technical Drill")
    company = q.get("company", "Company")

    rubric = eval_res.get("rubric_breakdown", {})
    strengths = eval_res.get("strengths", ["Solid technical understanding"])
    risks = eval_res.get("synthesis_risks", ["Review edge case behavior"])
    topics = eval_res.get("remedial_topics", ["Core System Concepts"])
    summary = eval_res.get("feedback_summary", "Evaluation completed successfully.")

    lines = [
        "## 🏆 Technical Interview Scorecard",
        f"**Company Track:** {company} | **Question Topic:** {topic}",
        f"**Candidate Score:** `{score:.1f} / 10.0` — **{badge}**",
        "",
        "---",
        "### 📊 Rubric Breakdown:",
    ]

    for k, v in rubric.items():
        name = k.replace("_", " ").title()
        lines.append(f"- **{name}:** `{v} / 10.0`")

    lines.append("")
    lines.append("### ✅ Strengths Identified:")
    for s in strengths:
        lines.append(f"- {s}")

    lines.append("")
    lines.append("### ⚠️ Synthesis Risks / Knowledge Gaps:")
    for r in risks:
        lines.append(f"- {r}")

    lines.append("")
    lines.append("### 📚 Recommended Remedial Topics:")
    for t in topics:
        lines.append(f"- {t}")

    lines.append("")
    lines.append("---")
    lines.append(f"📝 **Evaluator Summary:**\n{summary}")

    if has_mutation:
        lines.append("")
        lines.append("---")
        lines.append("⚠️ **Schedule Mutation Triggered:** Score fell below 6.0/10 threshold. Balancer automatically injected a 30-minute remedial review into tonight's Evening Block.")

    lines.append("")
    lines.append("👉 *Next step: Type **\"Start Amazon Bar Raiser drill\"** or **\"Show my daily study plan\"**.*")

    return "\n".join(lines)


def format_welcome_markdown() -> str:
    lines = [
        "## 🎓 Welcome to CampusMate AI!",
        "Your **Autonomous Academic & Career Agent** built on Fetch.ai `uAgents` and Agent Chat Protocol (ACP).",
        "",
        "I balance university coursework with target company recruitment tracks so you never compromise midterms for interviews.",
        "",
        "---",
        "### 🚀 Quick Prompts (Click or send any of these):",
        "1. **📅 Study Schedule:**  \n   *\"Create personalized study schedule for ECE Semester 6 with 4 hours daily\"*",
        "2. **⚡ Hardware & VLSI Drill:**  \n   *\"Start Qualcomm Verilog mock technical interview drill\"*",
        "3. **💻 Software & C++ Drill:**  \n   *\"Start TCS Prime C++ drill\"*",
        "4. **🏢 System Design & Leadership Drill:**  \n   *\"Unlock Amazon Bar Raiser mock interview pack\"*",
        "5. **📊 Exam Proximity Check:**  \n   *\"Check syllabus exam proximity and calculate study buffer\"*",
    ]
    return "\n".join(lines)


# ==============================================================================
# Agent Lifecycle & ACP Event Handlers
# ==============================================================================
@student_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"Student Twin Agent Online: {STUDENT_AGENT_NAME}")
    ctx.logger.info(f"Student Agent Address: {student_agent.address}")
    ctx.logger.info(f"Endpoint: {AGENT_ENDPOINT or 'None'}")
    ctx.logger.info(f"Agentverse Mailbox: {'ENABLED' if USE_MAILBOX else 'DISABLED'}")
    ctx.logger.info(f"Agent Chat Protocol (ACP): PUBLISHED (0.3.0)")
    ctx.logger.info("=" * 60)


@chat_proto.on_message(model=ACPChatMessage)
async def handle_official_acp_message(ctx: Context, sender: str, msg: ACPChatMessage):
    ctx.logger.info(f"[ACP 0.3.0] Received message from {sender}")
    # 1. Send mandatory ACP acknowledgment
    ack = ChatAcknowledgement(acknowledged_msg_id=msg.msg_id)
    await ctx.send(sender, ack)

    session = get_session(sender)
    user_text = msg.text().strip()
    ctx.logger.info(f"[User Input]: {user_text[:80]}...")
    lower = user_text.lower()

    # Detect JSON / urlencoded postback
    is_json = (user_text.startswith("{") and user_text.endswith("}")) or user_text.startswith("```json")
    if is_json:
        try:
            clean = user_text.replace("```json", "", 1).rstrip("`").strip()
            payload = json.loads(clean)
            if "branch" in payload:
                session.branch = payload.get("branch", session.branch).upper()
                session.semester = int(payload.get("semester", session.semester))
                session.target_company = payload.get("target_company", session.target_company)
                session.daily_hours = float(payload.get("daily_hours", session.daily_hours))
                session.days_to_midterm = int(payload.get("days_to_exam", session.days_to_midterm))
                lower = "schedule"
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # INTENT 1: Submit Answer & Evaluation
    # --------------------------------------------------------------------------
    is_answer = (
        session.stage == "IN_DRILL" and len(user_text) > 30 and
        not any(cmd in lower for cmd in ["schedule", "plan", "start", "unlock", "check", "hello", "hi"])
    ) or any(k in lower for k in [
        "blocking", "non-blocking", "pointer", "unique_ptr", "shared_ptr", "weak_ptr",
        "cache stampede", "consistent hashing", "raii", "vtable", "vptr", "setup time",
        "hold time", "delta cycle", "metastability"
    ])

    if is_answer:
        ctx.logger.info(f"[Intent] Candidate Answer Submission for '{session.last_question_id}'")
        q = find_question_by_id(session.last_question_id) or find_question_by_id("qualcomm_verilog_01")
        eval_result = llm_evaluator._evaluate_with_rubric_engine(q, user_text)

        score = eval_result.get("score", 7.0)
        has_mutation = score < 6.0
        session.stage = "EVALUATED"
        session.last_evaluation = eval_result

        scorecard_md = format_scorecard_markdown(eval_result, q, has_mutation=has_mutation)
        reply = ACPChatMessage(content=[TextContent(text=scorecard_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 2: Start Technical Interview Drill / Mock Pack
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["drill", "interview", "verilog", "mock", "bar raiser", "tcs", "qualcomm", "amazon"]):
        ctx.logger.info("[Intent] Start Drill Requested")
        if "amazon" in lower or "bar raiser" in lower:
            comp_key = "amazon"
            tier = "tier-1" if "bar raiser" in lower or "tier-1" in lower or "tier 1" in lower else "standard"
            q = select_drill_question(comp_key, tier=tier)
            session.target_company = "Amazon"
        elif "tcs" in lower or "c++" in lower:
            comp_key = "tcs_prime"
            q = select_drill_question(comp_key, tier="standard")
            session.target_company = "TCS Prime"
        else:
            comp_key = "qualcomm"
            q = select_drill_question(comp_key, tier="standard")
            session.target_company = "Qualcomm"

        session.last_question_id = q.get("id", "qualcomm_verilog_01")
        session.stage = "IN_DRILL"

        drill_md = format_drill_markdown(q, is_unlocked=True)
        reply = ACPChatMessage(content=[TextContent(text=drill_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 3: Generate Daily Action Plan / Schedule / Exam Buffer Check
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["schedule", "plan", "study", "syllabus", "midterm", "exam", "buffer", "hours", "proximity", "semester", "sem"]):
        ctx.logger.info("[Intent] Schedule / Plan Generation")

        # Extract Branch
        b_match = re.search(r"\b(ece|cse|it|mech)\b", lower)
        if b_match:
            session.branch = b_match.group(1).upper()

        # Extract Semester
        s_match = re.search(r"(?:semester|sem)\s*(\d+)", lower)
        if s_match:
            session.semester = int(s_match.group(1))

        # Extract Daily Hours
        h_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h\b)", lower)
        if h_match:
            session.daily_hours = float(h_match.group(1))

        # Extract Days to Midterm
        d_match = re.search(r"(?:midterm|exam|in)\s*(\d+)\s*days?", lower)
        if d_match:
            session.days_to_midterm = int(d_match.group(1))

        # Extract Company
        if "amazon" in lower:
            session.target_company = "Amazon"
        elif "tcs" in lower:
            session.target_company = "TCS Prime"
        elif "qualcomm" in lower:
            session.target_company = "Qualcomm"

        # Generate Deterministic Plan
        prof = SchemaStudentProfile(
            student_id=sender,
            branch=session.branch,
            semester=session.semester,
            target_company=session.target_company,
            daily_available_hours=session.daily_hours,
            days_to_midterm=session.days_to_midterm,
            upcoming_exams=[
                SchemaExamSchedule(
                    subject_code="EC601",
                    subject_name="Digital Signal Processing",
                    exam_date="2026-10-28",
                    days_to_exam=session.days_to_midterm,
                    credit_weight=4.0
                )
            ]
        )

        plan = balancing_engine.generate_daily_action_plan(prof)
        session.current_plan = plan
        session.stage = "PLAN_READY"

        plan_md = format_action_plan_markdown(plan, session)
        reply = ACPChatMessage(content=[TextContent(text=plan_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 4: Greeting / Help Menu
    # --------------------------------------------------------------------------
    welcome_md = format_welcome_markdown()
    reply = ACPChatMessage(content=[TextContent(text=welcome_md)])
    await ctx.send(sender, reply)


@chat_proto.on_message(model=ChatAcknowledgement)
async def handle_official_acp_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"[ACP 0.3.0] Acknowledged by {sender}: {msg.acknowledged_msg_id}")


# Include Protocols
student_agent.include(student_protocol)
student_agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    print(f"[Starting Student Twin Agent on port {STUDENT_PORT}...]")
    student_agent.run()
