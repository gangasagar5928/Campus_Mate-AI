"""
agent_student_twin.py - Student Twin Agent (Orchestrator Node)
Fetch.ai uAgent representing the student candidate.
Discovered via ASI:One through official Agent Chat Protocol (ACP).

Combines all 3 team members' work:
- Member 1: Agent Chat Protocol (ACP 0.3.0) orchestration, natural language intent parser & interactive UI cards
- Member 2: Departmental Syllabus Engine (AKTU/GCET 3rd year curriculum, dynamic 60/40, 50/50, 10/90 ratio balancing & evening remedial mutation hook)
- Member 3: Company Interviewer Engine (Qualcomm/TCS/Amazon question bank, 1.0 testnet FET Dorado payment verification, Bar Raiser rubric grading)
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
curriculum_loader = CurriculumLoader()
balancing_engine = DeterministicBalancingEngine(curriculum_loader=curriculum_loader)
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
        self.days_to_midterm = 18  # Default AKTU/GCET Academic Calendar sessional buffer
        self.days_specified_by_user = False
        self.last_question_id = "qualcomm_verilog_01"
        self.session_id = f"sess_{sender_id[-8:] if len(sender_id) >= 8 else 'user'}"
        self.current_plan = None
        self.last_evaluation = None
        self.evening_remedial_mutation = None

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

    # Determine allocation mode explanation
    if session.days_to_midterm < 3:
        mode_label = "Urgent Exam Revision Mode (90% High-Yield Syllabus / 10% Placement)"
    elif session.days_to_midterm <= 7:
        mode_label = "Approaching Midterm Mode (50% Placement / 50% Syllabus)"
    else:
        mode_label = "Normal Prep Mode (60% Placement Prep / 40% Academic Coursework)"

    # Syllabus subjects for branch & semester
    branch_subjects = curriculum_loader.get_branch_subjects(session.branch, session.semester)

    lines = [
        f"## 📅 Adaptive Daily Study Plan ({session.branch} — Semester {session.semester})",
        f"**Target Company:** {session.target_company} | **Study Budget:** {session.daily_hours:.1f} Hours/Day",
        "",
        "### ⏳ Exam Proximity & Calendar Synchronization:",
    ]

    if session.days_specified_by_user:
        lines.append(f"- 📌 **User-Specified Exam Date:** Midterm in **{session.days_to_midterm} Days**.")
    else:
        lines.append(
            f"- 📌 **College Academic Calendar Synced (AKTU/GCET):** Sessional Midterms start in **{session.days_to_midterm} Days** "
            "(no immediate exam debt, operating in Normal Placement Focus)."
        )
        lines.append("  *(💡 If your college announced a different date, simply message e.g. **\"my exam is in 3 days\"** to adapt!)*")

    lines.append("")
    lines.append(f"### ⚖️ Deterministic Workload Allocation ({mode_label})")
    lines.append(f"- 🎯 **Target Placement Drills:** **{p_pct}%** ({p_mins} mins)")
    lines.append(f"- 📘 **Academic Syllabus Revision:** **{s_pct}%** ({s_mins} mins)")
    lines.append("")
    lines.append("---")

    # Syllabus overview
    lines.append(f"### 📚 Active Academic Syllabus ({session.branch} — Semester {session.semester}):")
    for subj in branch_subjects:
        code = subj.get("subject_code", "")
        name = subj.get("subject_name", "")
        relevance = subj.get("placement_relevance", "Core Technical Value")
        units = subj.get("units", [])
        unit_titles = [u.get("unit_title", "") for u in units[:2]]
        units_text = " • ".join(unit_titles) if unit_titles else "Core Units"
        lines.append(f"- **{code} — {name}:** {units_text}")
        lines.append(f"  *Recruitment Value:* _{relevance}_")

    lines.append("")
    lines.append("---")
    lines.append("### 📝 Today's Recommended Task Schedule:")

    time_blocks = ["🌅 Morning Block", "☀️ Mid-Day Block", "🌆 Afternoon Block", "📘 Evening Block", "🌙 Night Block"]
    for idx, task in enumerate(plan.tasks):
        block_label = time_blocks[idx % len(time_blocks)]
        cat_badge = "📘 Syllabus" if task.category == "Syllabus Revision" else "🎯 Placement"
        lines.append(f"{idx + 1}. **{block_label} ({task.duration_minutes}m):** `{cat_badge}` {task.title}")

    # Evening remedial mutation note if present
    if session.evening_remedial_mutation:
        lines.append("")
        lines.append(f"⚠️ **Evening Remedial Hook Injected:** {session.evening_remedial_mutation}")

    lines.append("")
    lines.append("---")
    lines.append(f"👉 *Next Step: Type **\"Start {session.target_company} drill\"** to begin your interactive technical interview mock!*")

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
        "Reply directly with your technical explanation, architecture, or code. CampusMate will run instant rubric evaluation and generate your scoring badge.",
    ]
    return "\n".join(lines)


def format_scorecard_markdown(eval_res: Dict[str, Any], q: Dict[str, Any], has_mutation: bool = False, mutated_topic: str = "") -> str:
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
        lines.append(
            f"⚠️ **Member 2 Remedial Mutation Hook Triggered:** Score fell below the 6.0/10 threshold. "
            f"The balancer engine dynamically injected a 30-minute remedial review (*'{mutated_topic}'*) into tonight's Evening Study Block."
        )

    lines.append("")
    lines.append("👉 *Next step: Type **\"Show my daily study plan\"** to see the updated schedule, or **\"Start Amazon Bar Raiser drill\"** for next drill.*")

    return "\n".join(lines)


def format_welcome_markdown() -> str:
    lines = [
        "## 🎓 Welcome to CampusMate AI!",
        "Your **Autonomous Academic & Career Agent** built on Fetch.ai `uAgents` and Agent Chat Protocol (ACP).",
        "",
        "Combines all 3 team members' work into one seamless workflow:",
        "- **Member 1 (Orchestration):** Agent Chat Protocol (ACP 0.3.0) discovery on ASI:One.",
        "- **Member 2 (Syllabus Balancing):** AKTU/GCET 3rd-year curriculum, dynamic ratio balancing (60/40, 50/50, 10/90) & evening remedial mutation hook.",
        "- **Member 3 (Interviewer & Web3):** Qualcomm/TCS/Amazon interview packs, 1.0 testnet FET Dorado micropayments & 10.0 Bar Raiser rubric grading.",
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
                if "days_to_exam" in payload:
                    session.days_to_midterm = int(payload.get("days_to_exam"))
                    session.days_specified_by_user = True
                lower = "schedule"
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # INTENT 1: Submit Answer & Evaluation (Member 3 Rubric Engine)
    # --------------------------------------------------------------------------
    is_answer = (
        session.stage == "IN_DRILL" and len(user_text) > 30 and
        not any(cmd in lower for cmd in ["schedule", "plan", "start", "unlock", "check", "hello", "hi"])
    ) or any(k in lower for k in [
        "blocking", "non-blocking", "pointer", "unique_ptr", "shared_ptr", "weak_ptr",
        "cache stampede", "consistent hashing", "raii", "vtable", "vptr", "setup time",
        "hold time", "delta cycle", "metastability", "nba region"
    ])

    if is_answer:
        ctx.logger.info(f"[Intent] Candidate Answer Submission for '{session.last_question_id}'")
        q = find_question_by_id(session.last_question_id) or find_question_by_id("qualcomm_verilog_01")
        eval_result = llm_evaluator._evaluate_with_rubric_engine(q, user_text)

        score = eval_result.get("score", 7.0)
        has_mutation = score < 6.0
        session.stage = "EVALUATED"
        session.last_evaluation = eval_result

        mutated_topic = ""
        if has_mutation:
            remedial_topics = eval_result.get("remedial_topics", ["RTL Simulation & Race Hazards"])
            mutated_topic = remedial_topics[0]
            session.evening_remedial_mutation = f"30m Remedial Drill: {mutated_topic} (Score was {score:.1f}/10)"

        scorecard_md = format_scorecard_markdown(eval_result, q, has_mutation=has_mutation, mutated_topic=mutated_topic)
        reply = ACPChatMessage(content=[TextContent(text=scorecard_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 2: Start Technical Interview Drill / Mock Pack (Member 3 Track Bank)
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
    # INTENT 3: Generate Daily Action Plan / Schedule / Exam Proximity (Member 2 Engine)
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

        # Check if user explicitly specified days left
        d_match = re.search(r"(?:midterm|exam|in)\s*(\d+)\s*days?", lower)
        if d_match:
            session.days_to_midterm = int(d_match.group(1))
            session.days_specified_by_user = True
        else:
            # Default to AKTU / GCET college academic calendar sessional buffer
            session.days_to_midterm = 18
            session.days_specified_by_user = False

        # Extract Target Company
        if "amazon" in lower:
            session.target_company = "Amazon"
        elif "tcs" in lower:
            session.target_company = "TCS Prime"
        elif "qualcomm" in lower:
            session.target_company = "Qualcomm"

        # Lookup actual syllabus subjects for this semester
        subjs = curriculum_loader.get_branch_subjects(session.branch, session.semester)
        upcoming_exams = [
            SchemaExamSchedule(
                subject_code=s.get("subject_code", "SEM-CORE"),
                subject_name=s.get("subject_name", "Core Subject"),
                exam_date="2026-11-11",
                days_to_exam=session.days_to_midterm,
                credit_weight=float(s.get("credit_weight", 4.0))
            ) for s in subjs
        ]

        # Generate Deterministic Plan via Member 2 Balancer Engine
        prof = SchemaStudentProfile(
            student_id=sender,
            branch=session.branch,
            semester=session.semester,
            target_company=session.target_company,
            daily_available_hours=session.daily_hours,
            days_to_midterm=session.days_to_midterm,
            upcoming_exams=upcoming_exams
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
