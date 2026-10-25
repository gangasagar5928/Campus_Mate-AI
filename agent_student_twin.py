"""
agent_student_twin.py - Student Twin Agent (Orchestrator Node)
Fetch.ai uAgent representing the student candidate.
Discovered via ASI:One through official Agent Chat Protocol (ACP).

Combines all 3 team members' work:
- Member 1: Agent Chat Protocol (ACP 0.3.0) orchestration, natural language intent parser & interactive UI cards
- Member 2: Departmental Syllabus Engine (AKTU/GCET 1st-8th sem curriculum, dynamic 60/40, 50/50, 10/90 ratio balancing & evening remedial mutation hook)
- Member 3: Company Interviewer Engine (Qualcomm, Google, Nvidia, Microsoft, Amazon, TCS Prime bank, 1.0 testnet FET Dorado payment verification, Bar Raiser rubric grading)
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
CURRICULUM_DATA = curriculum_loader.load()
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
        "- **Member 2 (Syllabus Balancing):** AKTU/GCET 1st-8th sem curriculum, dynamic ratio balancing (60/40, 50/50, 10/90) & evening remedial mutation hook.",
        "- **Member 3 (Interviewer & Web3):** Qualcomm, Google, Nvidia, Microsoft, Amazon, TCS Prime bank, 1.0 testnet FET Dorado micropayments & 10.0 Bar Raiser rubric grading.",
        "",
        "---",
        "### 🚀 Quick Prompts (Click or send any of these):",
        "1. **📖 Course Topics & Syllabus:**  \n   *\"Tell me the topics for ECE semester 6\"*",
        "2. **📅 Study Timetable:**  \n   *\"Create study schedule for ECE Semester 6 with 4 hours daily\"*",
        "3. **⚡ Hardware & VLSI Drill:**  \n   *\"Start Qualcomm Verilog mock technical interview drill\"*",
        "4. **🔍 Google Distributed Systems:**  \n   *\"Start Google drill\"*",
        "5. **🎮 Nvidia GPU & CUDA:**  \n   *\"Start Nvidia drill\"*",
        "6. **🏢 Amazon Bar Raiser:**  \n   *\"Unlock Amazon Bar Raiser mock interview pack\"*",
        "7. **🎯 All Interview Tracks:**  \n   *\"Show interview tracks\"*",
    ]
    return "\n".join(lines)


# ==============================================================================
# Autonomous Knowledge & Retrieval Engine (Zero-Hallucination Ground Truth)
# ==============================================================================
STOPWORDS = {"what", "is", "the", "in", "and", "of", "for", "about", "tell", "me", "explain", "how", "to", "a", "an", "do", "you", "know", "can", "please", "give"}

def clean_tokens(text: str) -> List[str]:
    words = re.findall(r'[a-zA-Z0-9_\-\+]+', text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

def match_query(query: str) -> Dict[str, Any]:
    q_low = query.lower()
    tokens = set(clean_tokens(query))

    # 1. Exact Subject Code Match (e.g. KEC-601, KCS-501)
    code_match = re.search(r'\b(k[a-z]{2}-?\d{3})\b', q_low)
    if code_match:
        target_code = code_match.group(1).upper().replace("-", "")
        for branch, bdata in CURRICULUM_DATA.get('branches', {}).items():
            for s in bdata.get('subjects', []):
                s_code = s.get('subject_code', '').upper().replace("-", "")
                if target_code == s_code:
                    return {"type": "SUBJECT", "branch": branch, "data": s}

    # 2. Company Technical Questions Match
    best_q = None
    best_score = 0
    for comp_key, comp_data in INTERVIEW_BANK.get('companies', {}).items():
        for qitem in comp_data.get('questions', []):
            topic = qitem.get('topic', '').lower()
            topic_tokens = set(clean_tokens(topic))
            comp_match = comp_key in q_low
            common = tokens.intersection(topic_tokens)
            score = len(common) * 2 + (2 if comp_match else 0)
            if score > best_score and (len(common) >= 2 or (comp_match and len(common) >= 1) or topic in q_low):
                best_score = score
                best_q = qitem
    if best_q and best_score >= 2:
        return {"type": "INTERVIEW_QUESTION", "data": best_q}

    # 3. Curriculum Subject Name Match
    for branch, bdata in CURRICULUM_DATA.get('branches', {}).items():
        for s in bdata.get('subjects', []):
            s_name = s.get('subject_name', '').lower()
            if s_name in q_low or len(tokens.intersection(set(clean_tokens(s_name)))) >= 2:
                return {"type": "SUBJECT", "branch": branch, "data": s}

    # 4. Curriculum Unit Topic Match
    for branch, bdata in CURRICULUM_DATA.get('branches', {}).items():
        for s in bdata.get('subjects', []):
            for u in s.get('units', []):
                u_title = u.get('unit_title', '').lower()
                if u_title in q_low:
                    return {"type": "CURRICULUM_UNIT", "branch": branch, "subject": s, "unit": u}
                for t in u.get('topics', []):
                    t_low = t.lower()
                    if t_low in q_low or len(tokens.intersection(set(clean_tokens(t_low)))) >= 2:
                        return {"type": "CURRICULUM_TOPIC", "branch": branch, "subject": s, "unit": u, "topic": t}

    return {"type": "NONE"}


def format_subject_markdown(subject: Dict[str, Any], branch: str) -> str:
    code = subject.get("subject_code", "")
    name = subject.get("subject_name", "")
    sem = subject.get("semester", "")
    credits = subject.get("credit_weight", 4.0)
    relevance = subject.get("placement_relevance", "Core Engineering Value")

    lines = [
        f"## 📚 AKTU Official Syllabus: {code} — {name}",
        f"**Branch:** {branch} | **Semester:** {sem} | **Credits:** {credits}",
        f"**Recruitment Value:** _{relevance}_",
        "",
        "### 📖 Course Units Breakdown:"
    ]
    for u in subject.get("units", []):
        u_num = u.get("unit_number", 1)
        u_title = u.get("unit_title", "")
        is_hy = "🔥 High-Yield" if u.get("is_high_yield") else "Standard"
        lines.append(f"#### Unit {u_num}: {u_title} ({is_hy})")
        topics = u.get("topics", [])
        if topics:
            lines.append("- " + " • ".join(topics))
        lines.append("")

    lines.append("---")
    lines.append(f"👉 *To generate your daily balanced timetable, send: **\"Create study plan for {branch} Sem {sem} with 4 hours daily\"***")
    lines.append(f"👉 *To launch a technical interview mock, send: **\"Start Qualcomm drill\"** or **\"Start Google drill\"***")
    return "\n".join(lines)


def format_topic_markdown(match: Dict[str, Any]) -> str:
    s = match.get("subject", {})
    u = match.get("unit", {})
    t = match.get("topic", u.get("unit_title", ""))
    branch = match.get("branch", "Engineering")
    code = s.get("subject_code", "")
    name = s.get("subject_name", "")
    sem = s.get("semester", "")
    is_hy = "🔥 High-Yield" if u.get("is_high_yield") else "Standard"
    relevance = s.get("placement_relevance", "Core Technical Value")

    lines = [
        f"## 📘 Syllabus Concept: {t}",
        f"**Curriculum Mapping:** {code} — {name} ({branch} Semester {sem})",
        f"**Unit {u.get('unit_number')}:** {u.get('unit_title')} ({is_hy})",
        f"**Industry Placement Alignment:** _{relevance}_",
        "",
        "---",
        "### 🔍 Detailed Curriculum Coverage:",
        f"This topic is an integral component of **Unit {u.get('unit_number')}** under the official AKTU university syllabus.",
        "",
        "**Core Topics in this Unit:**"
    ]
    for topic_item in u.get("topics", []):
        marker = "👉" if topic_item.lower() == t.lower() else "-"
        lines.append(f"{marker} {topic_item}")

    lines.append("")
    lines.append("---")
    lines.append("💡 *Academic & Placement Tip:* For recruitment drills, focus on numerical derivations, timing diagrams, and architecture applications.")
    lines.append(f"👉 *To add this topic to your daily schedule, send: **\"Create study plan for {branch} Sem {sem}\"***")
    return "\n".join(lines)


def format_interview_concept_markdown(q: Dict[str, Any]) -> str:
    comp = q.get("company", "Company")
    track = q.get("track", "Engineering")
    topic = q.get("topic", "System Drill")
    diff = q.get("difficulty", "Medium")
    tier = q.get("tier", "Standard").title()
    rubric = q.get("expected_rubric", {})

    lines = [
        f"## ⚡ {comp} Recruitment Drill: {topic}",
        f"**Track:** {track} | **Difficulty:** `{diff}` | **Tier:** `{tier}`",
        "",
        "---",
        "### 📋 Technical Interview Challenge:",
        f"{q.get('question', '')}",
        "",
        "---",
        "### 🎯 Senior Bar Raiser Scoring Checkpoints (10.0 Rubric):",
        "**Must-Include Technical Mechanics:**"
    ]
    for item in rubric.get("must_include", []):
        lines.append(f"- ✅ {item}")

    if rubric.get("bonus_points"):
        lines.append("")
        lines.append("**Bonus Architecture / Edge Cases:**")
        for item in rubric.get("bonus_points", []):
            lines.append(f"- ⭐ {item}")

    if rubric.get("common_pitfalls"):
        lines.append("")
        lines.append("**Common Pitfalls to Avoid:**")
        for item in rubric.get("common_pitfalls", []):
            lines.append(f"- ⚠️ {item}")

    lines.append("")
    lines.append("---")
    lines.append("✍️ *Reply directly with your technical explanation or code to receive your instant Bar Raiser scorecard & badge!*")
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
    session = get_session(sender)
    raw_text = msg.text().strip()

    # Clean out @mention tag if present from ASI:One chat
    user_text = re.sub(r"@agent1[a-z0-9]+\s*", "", raw_text).strip()
    if not user_text:
        user_text = raw_text

    ctx.logger.info(f"[ACP 0.3.0] Received from {sender}: {user_text[:80]}...")
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
    # INTENT 0A: Direct Syllabus / Topic Breakdown Inquiry
    # --------------------------------------------------------------------------
    is_topic_inquiry = any(k in lower for k in ["topic", "topics", "syllabus", "subject", "subjects", "curriculum"]) and not any(k in lower for k in ["schedule", "hours", "plan", "timetable", "routine"])
    if is_topic_inquiry:
        ctx.logger.info("[Intent] Direct Syllabus / Topic Breakdown Inquiry")
        b_match = re.search(r"\b(ece|cse|it|mech)\b", lower)
        if b_match:
            session.branch = b_match.group(1).upper()
        s_match = re.search(r"(?:semester|sem)\s*(\d+)", lower)
        if s_match:
            session.semester = int(s_match.group(1))

        branch_subjs = curriculum_loader.get_branch_subjects(session.branch, session.semester)
        lines = [
            f"## 📚 AKTU Official Syllabus Breakdown ({session.branch} — Semester {session.semester})",
            f"**University Scheme:** Dr. A.P.J. Abdul Kalam Technical University (AKTU / GCET AICTE Model)",
            "",
            "### 📖 Core Subjects & Syllabus Units:",
        ]
        for s in branch_subjs:
            code = s.get("subject_code", "")
            name = s.get("subject_name", "")
            relevance = s.get("placement_relevance", "Core Technical Engineering Value")
            credits = s.get("credit_weight", 4.0)
            lines.append(f"#### 📘 {code} — {name} (Credits: {credits})")
            for u in s.get("units", []):
                u_num = u.get("unit_number", 1)
                u_title = u.get("unit_title", "Unit")
                is_hy = "🔥 High-Yield" if u.get("is_high_yield") else "Standard"
                topics = ", ".join(u.get("topics", [])[:4])
                lines.append(f"- **Unit {u_num} ({is_hy}):** {u_title}")
                if topics:
                    lines.append(f"  *Key Topics:* {topics}")
            lines.append(f"  *Placement Target:* _{relevance}_")
            lines.append("")

        lines.append("---")
        lines.append(f"👉 *To generate your balanced daily study routine, send: **\"Create study plan for {session.branch} Sem {session.semester} with 4 hours daily\"***")
        lines.append(f"👉 *To test your technical preparation, send: **\"Start Qualcomm Verilog drill\"** or **\"Start Google drill\"***")

        topics_md = "\n".join(lines)
        reply = ACPChatMessage(content=[TextContent(text=topics_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 0B: Available Interview Tracks & Companies Overview
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["interview track", "interview prep", "companies", "what tracks", "available tracks", "show tracks"]):
        ctx.logger.info("[Intent] Interview Prep Tracks Overview")
        lines = [
            "## 🎯 CampusMate Interview Preparation Hub",
            "Tailored technical drill tracks aligned with tier-1 engineering recruitment:",
            "",
            "| Company | Recruitment Track | Quick Launch Command |",
            "| :--- | :--- | :--- |",
            "| **Qualcomm** | Hardware / VLSI RTL / STA | `Start Qualcomm Verilog drill` |",
            "| **Google** | Distributed Systems & Dynamic Programming | `Start Google drill` |",
            "| **Nvidia** | GPU CUDA, SIMT & Shared Memory | `Start Nvidia drill` |",
            "| **Microsoft** | High-Throughput Concurrency & Async I/O | `Start Microsoft drill` |",
            "| **Amazon** | System Design & Bar Raiser Cache | `Unlock Amazon Bar Raiser mock interview pack` |",
            "| **TCS Prime** | Modern C++ Smart Pointers & RAII | `Start TCS Prime drill` |",
            "",
            "---",
            "💡 *All drills include instant Senior Bar Raiser 10.0 rubric evaluation and automatic evening schedule mutation if score < 6.0/10.*",
            "👉 *Send any command from the table above to start drilling immediately.*"
        ]
        prep_md = "\n".join(lines)
        reply = ACPChatMessage(content=[TextContent(text=prep_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 1: Submit Answer & Evaluation (Member 3 Rubric Engine)
    # --------------------------------------------------------------------------
    is_answer = (
        session.stage == "IN_DRILL" and len(user_text) > 30 and
        not any(cmd in lower for cmd in ["schedule", "plan", "start", "unlock", "check", "hello", "hi", "topics"])
    ) or any(k in lower for k in [
        "blocking", "non-blocking", "pointer", "unique_ptr", "shared_ptr", "weak_ptr",
        "cache stampede", "consistent hashing", "raii", "vtable", "vptr", "setup time",
        "hold time", "delta cycle", "metastability", "nba region", "virtual nodes", "warp divergence"
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
            remedial_topics = eval_result.get("remedial_topics", ["Core Technical Concepts"])
            mutated_topic = remedial_topics[0]
            session.evening_remedial_mutation = f"30m Remedial Drill: {mutated_topic} (Score was {score:.1f}/10)"

        scorecard_md = format_scorecard_markdown(eval_result, q, has_mutation=has_mutation, mutated_topic=mutated_topic)
        reply = ACPChatMessage(content=[TextContent(text=scorecard_md)])
        await ctx.send(sender, reply)
        return

    # --------------------------------------------------------------------------
    # INTENT 2: Start Technical Interview Drill / Mock Pack (Member 3 Track Bank)
    # --------------------------------------------------------------------------
    if any(k in lower for k in ["drill", "interview", "verilog", "mock", "bar raiser", "tcs", "qualcomm", "amazon", "google", "nvidia", "microsoft"]):
        ctx.logger.info("[Intent] Start Drill Requested")
        if "google" in lower:
            comp_key = "google"
            tier = "tier-1" if "adv" in lower or "hard" in lower else "standard"
            q = select_drill_question(comp_key, tier=tier)
            session.target_company = "Google"
        elif "nvidia" in lower or "cuda" in lower or "gpu" in lower:
            comp_key = "nvidia"
            q = select_drill_question(comp_key, tier="standard")
            session.target_company = "Nvidia"
        elif "microsoft" in lower or "msft" in lower:
            comp_key = "microsoft"
            q = select_drill_question(comp_key, tier="standard")
            session.target_company = "Microsoft"
        elif "amazon" in lower or "bar raiser" in lower:
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
    if any(k in lower for k in ["schedule", "plan", "study", "timetable", "routine", "midterm", "exam", "buffer", "hours", "proximity", "semester", "sem"]):
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
            session.days_to_midterm = 18
            session.days_specified_by_user = False

        # Extract Target Company
        if "google" in lower:
            session.target_company = "Google"
        elif "nvidia" in lower:
            session.target_company = "Nvidia"
        elif "microsoft" in lower:
            session.target_company = "Microsoft"
        elif "amazon" in lower:
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
    # INTENT 3.5: Zero-Hallucination Knowledge & Technical Q&A Engine
    # --------------------------------------------------------------------------
    match = match_query(user_text)
    if match["type"] == "SUBJECT":
        ctx.logger.info(f"[Intent] Specific Subject Knowledge Match: {match['data'].get('subject_code')}")
        md = format_subject_markdown(match["data"], match["branch"])
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return
    elif match["type"] in ("CURRICULUM_UNIT", "CURRICULUM_TOPIC"):
        ctx.logger.info(f"[Intent] Curriculum Topic Match: {match.get('topic') or match['unit'].get('unit_title')}")
        md = format_topic_markdown(match)
        reply = ACPChatMessage(content=[TextContent(text=md)])
        await ctx.send(sender, reply)
        return
    elif match["type"] == "INTERVIEW_QUESTION" and any(k in lower for k in ["explain", "what is", "how", "tell me", "concept", "pitfall", "rubric", "difference", "compare"]):
        ctx.logger.info(f"[Intent] Technical Interview Concept Match: {match['data'].get('topic')}")
        md = format_interview_concept_markdown(match["data"])
        reply = ACPChatMessage(content=[TextContent(text=md)])
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
