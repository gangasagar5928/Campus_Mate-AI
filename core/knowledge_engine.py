"""
core/knowledge_engine.py - Zero-Hallucination Retrieval & Academic Engine.
Grounds student inquiries in official AKTU curricula and company question banks.
"""

import re
import os
import json
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CURRICULUM_PATH = os.path.join(DATA_DIR, "curriculum.json")
INTERVIEW_BANK_PATH = os.path.join(DATA_DIR, "interview_bank.json")

# Fallback loaders
if not os.path.exists(CURRICULUM_PATH):
    CURRICULUM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "curriculum.json")
if not os.path.exists(INTERVIEW_BANK_PATH):
    INTERVIEW_BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "interview_bank.json")

with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
    CURRICULUM_DATA = json.load(f)

with open(INTERVIEW_BANK_PATH, "r", encoding="utf-8") as f:
    INTERVIEW_BANK = json.load(f)

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


def format_balancing_strategy_markdown() -> str:
    return "\n".join([
        "## ⚖️ CampusMate Dynamic Load-Balancing Algorithm",
        "CampusMate AI eliminates **Academic Debt** by continuously harmonizing your college semester exams with tier-1 recruitment goals using a 3-tier deterministic allocation model:",
        "",
        "### 📊 The 3 Dynamic Workload Modes:",
        "1. **Normal Preparation Mode (> 7 Days to Midterm):**",
        "   - **Allocation:** `60% Placement Prep (144m)` / `40% Syllabus Revision (96m)` (based on 4 hrs)",
        "   - **Focus:** Heavy coding drills, system design, LeetCode/Verilog, while maintaining steady syllabus momentum.",
        "",
        "2. **Approaching Midterm Mode (3 to 7 Days to Midterm):**",
        "   - **Allocation:** `50% Placement Prep (120m)` / `50% Syllabus Revision (120m)`",
        "   - **Focus:** Balanced split to prevent last-minute cramming without pausing competitive problem solving.",
        "",
        "3. **Urgent Exam Revision Mode (< 3 Days to Midterm):**",
        "   - **Allocation:** `10% Placement Prep (24m)` / `90% High-Yield Syllabus Units (216m)`",
        "   - **Focus:** Emergency academic triage. Dynamically filters out low-weight syllabus units and drills exclusively on `🔥 High-Yield` numerical derivations and diagrams to secure CGPA.",
        "",
        "---",
        "### ⚡ Evening Remedial Mutation Hook:",
        "If you score `< 6.0 / 10.0` on any technical interview drill, the engine automatically injects a **30-minute remedial session** into tonight's Evening Block, guaranteeing knowledge gaps are eliminated before sleep.",
        "",
        "👉 *To generate your customized plan, send: **\"Create study plan for ECE Sem 6 with 4 hours daily\"***"
    ])


def format_branches_coverage_markdown() -> str:
    return "\n".join([
        "## 🎓 AKTU / AICTE Comprehensive Academic Coverage",
        "CampusMate AI includes official course structures, high-yield tags, and placement mappings for all 4 major engineering departments across **Semesters 1 through 8**:",
        "",
        "| Department | Branch Code | Supported Semesters | Placement Recruitment Targets |",
        "| :--- | :--- | :--- | :--- |",
        "| **Electronics & Communication** | `ECE` | Semesters 1 to 8 | Qualcomm, Intel, Texas Instruments, Nvidia, Embedded & Signal Processing |",
        "| **Computer Science & Engg** | `CSE` | Semesters 1 to 8 | Google, Amazon, Microsoft, Systems Architecture, Distributed Cloud |",
        "| **Information Technology** | `IT` | Semesters 1 to 8 | Cloud Computing, Full-Stack Architecture, TCS Prime, Amazon AWS |",
        "| **Mechanical Engineering** | `MECH` | Semesters 1 to 8 | Robotics, CAD/CAM, Thermal Systems, Core Engineering Operations |",
        "",
        "---",
        "### 🔍 What you can ask:",
        "- *\"Tell me the topics for CSE semester 5\"*",
        "- *\"What is KEC-601?\"*",
        "- *\"Show MECH semester 4 subjects\"*",
        "- *\"Which units in KCS-502 are high yield?\"*"
    ])


def format_company_guide_markdown(company_name: str) -> str:
    comp = company_name.title()
    dossiers = {
        "Qualcomm": {
            "track": "Hardware & Embedded Systems / VLSI",
            "topics": "Verilog RTL, Blocking vs Non-Blocking Assignments, Setup & Hold Time Violations, Clock Domain Crossing (CDC), ARM Cortex Interfacing (I2C/SPI).",
            "pitfall": "Mixing blocking (=) and non-blocking (<=) statements in sequential always blocks; ignoring clock skew in hold-time analysis.",
            "command": "Start Qualcomm Verilog mock technical interview drill"
        },
        "Google": {
            "track": "Systems Architecture & Algorithmic Scalability",
            "topics": "Consistent Hashing with Virtual Nodes, Distributed Sharding, High-Capacity Tree-DP, Cache Invalidation at Planet Scale.",
            "pitfall": "Failing to account for non-uniform node distribution; ignoring hotspot churn when scaling server clusters.",
            "command": "Start Google drill"
        },
        "Nvidia": {
            "track": "GPU Architecture, Parallel Computing & CUDA Systems",
            "topics": "SIMT Execution Models, 32-Thread Warp Divergence, Shared Memory Bank Conflicts (32 banks), Coalesced Global Memory Access.",
            "pitfall": "Allowing thread branch divergence inside a single warp; ignoring stride patterns that cause memory serialization.",
            "command": "Start Nvidia drill"
        },
        "Microsoft": {
            "track": "Cloud Platforms, High-Throughput Concurrency & Async I/O",
            "topics": "Worker Thread Pools, Asynchronous I/O Completion Ports (IOCP), Lock-Free Ring Buffers, Semaphore vs Mutex contention.",
            "pitfall": "Blocking thread pool worker threads with synchronous calls; deadlocks caused by priority inversions.",
            "command": "Start Microsoft drill"
        },
        "Amazon": {
            "track": "Data Structures, Distributed Caching & Bar Raiser",
            "topics": "Cache Stampede (Thundering Herd) Prevention, Probabilistic Early Expiration (XFetch), Distributed Locks, Bar Raiser Leadership Principles.",
            "pitfall": "Relying on standard TTL without mutex/probabilistic recompute; missing graceful degradation during downstream cache failure.",
            "command": "Unlock Amazon Bar Raiser mock interview pack"
        },
        "Tcs Prime": {
            "track": "Systems Engineering, Modern C++ & Advanced Algorithms",
            "topics": "Modern C++ (C++17/20), Smart Pointers (`std::unique_ptr`, `std::shared_ptr`, `std::weak_ptr`), RAII, Exception Safety, Virtual Dispatch.",
            "pitfall": "Creating cyclic references with `shared_ptr` instead of `weak_ptr`; raw memory leaks when exceptions are thrown.",
            "command": "Start TCS Prime drill"
        }
    }
    d = dossiers.get(comp, dossiers["Qualcomm"])
    return "\n".join([
        f"## 🏢 {comp} Recruitment Preparation Guide",
        f"**Track:** {d['track']}",
        "",
        "---",
        "### 🎯 High-Frequency Technical Topics Tested:",
        f"{d['topics']}",
        "",
        "### ⚠️ Senior Bar Raiser Pitfall to Avoid:",
        f"_{d['pitfall']}_",
        "",
        "---",
        f"👉 *Launch an interactive technical mock drill: Send **\"{d['command']}\"***"
    ])


def format_interview_tracks_markdown() -> str:
    return "\n".join([
        "## 🎯 CampusMate Interview Preparation Hub",
        "Tailored technical drill tracks aligned with tier-1 engineering recruitment:",
        "",
        "| Company | Recruitment Track | Quick Launch Command |",
        "| :--- | :--- | :--- |",
        "| **Qualcomm** | Hardware / VLSI RTL / STA | `Start Qualcomm Verilog drill` |",
        "| **Google** | Distributed Systems & Dynamic Programming | `Start Google drill` |",
        "| **Nvidia** | GPU CUDA, SIMT & Shared Memory | `Start Nvidia drill` |",
        "| **Microsoft** | High-Throughput Concurrency & Async I/O | `Start Microsoft drill` |",
        "| **Amazon** | System Design & Bar Raiser Cache | `Start Amazon Bar Raiser drill` |",
        "| **TCS Prime** | Modern C++ Smart Pointers & RAII | `Start TCS Prime drill` |",
        "",
        "---",
        "💡 *All drills include instant Senior Bar Raiser 10.0 rubric evaluation and automatic evening schedule mutation if score < 6.0/10.*",
        "👉 *Send any command from the table above to start drilling immediately.*"
    ])


def format_web3_guide_markdown() -> str:
    return format_interview_tracks_markdown()


def format_exam_strategy_markdown() -> str:
    return "\n".join([
        "## 📝 AKTU Sessional & University Exam Excellence Guide",
        "How to secure 8.5+ CGPA while cracking Tier-1 off-campus placements:",
        "",
        "### 💡 Top 4 Tactical Rules for AKTU Students:",
        "1. **Master the `🔥 High-Yield` Units First:**",
        "   - In AKTU curricula, Units 1, 2, and 3 typically account for **70% of numerical derivations and theory** in Section B and C.",
        "",
        "2. **Step-Marking & Diagram Formatting:**",
        "   - AKTU evaluators award up to 40% of marks for clear block diagrams, timing waveforms, and circuit schematics before reading text derivations.",
        "",
        "3. **Never Zero Out Coding:**",
        "   - Even in exam week, dedicate 30 minutes daily to technical drills. Algorithmic thinking atrophies fast if paused completely.",
        "",
        "4. **Synchronize Sessional Buffer with CampusMate:**",
        "   - College announced midterms? Simply tell CampusMate: *\"my exam is in 3 days\"* — the balancer engine instantly recalculates your daily routine to 90% exam focus.",
        "",
        "👉 *To generate your exam timetable, send: **\"Create study plan for ECE Sem 6 with 4 hours daily\"***"
    ])


def format_remedial_hook_markdown() -> str:
    return "\n".join([
        "## 🔄 Autonomous Evening Remedial Mutation Hook",
        "The proprietary feedback loop between Syllabus Balancer and Technical Interviewer:",
        "",
        "### ⚙️ How the Mutation Mechanism Works:",
        "1. **Interactive Evaluation:** Candidate submits explanation or code to a company drill prompt.",
        "2. **Rubric Grading:** Evaluated on a 10.0 scale against expected architectural checkpoints and pitfalls.",
        "3. **Threshold Trigger:** If score is **`< 6.0 / 10.0`**, the balancer intercepts tonight's schedule.",
        "4. **Dynamic Mutation:** Injects a targeted **30-minute remedial review block** on your exact weak topic into your Evening Block.",
        "5. **Schedule Regeneration:** Eliminates knowledge debt before campus recruitment season.",
        "",
        "👉 *Test the mutation hook: Send **\"Start Qualcomm drill\"** and submit an incomplete answer to watch tonight's schedule mutate dynamically!*"
    ])


def format_profile_status_markdown(session: Any) -> str:
    exam_status = f"Midterm in **{session.days_to_midterm} Days** (User-Specified)" if session.days_specified_by_user else f"Midterm in **{session.days_to_midterm} Days** (Synced to AKTU/GCET Calendar)"
    mode_label = "Urgent Exam Revision (10/90)" if session.days_to_midterm < 3 else ("Approaching Midterm (50/50)" if session.days_to_midterm <= 7 else "Normal Prep (60/40)")

    return "\n".join([
        "## 👤 Active Student Twin Profile",
        f"- 🎓 **Engineering Branch:** `{session.branch}`",
        f"- 📚 **Current Semester:** `Semester {session.semester}`",
        f"- 🏢 **Target Company:** `{session.target_company}`",
        f"- ⏱️ **Daily Study Budget:** `{session.daily_hours:.1f} Hours/Day`",
        f"- ⏳ **Exam Proximity:** {exam_status}",
        f"- ⚖️ **Current Balancer Mode:** `{mode_label}`",
        f"- 🔄 **Remedial Hook Status:** `{'Active (' + session.evening_remedial_mutation + ')' if session.evening_remedial_mutation else 'Clear (No Academic Debt)'}`",
        "",
        "---",
        "💡 *To update your profile anytime, send e.g.:*  \n*\"Switch to CSE Semester 5 with 3 hours daily targeting Google, exam in 4 days\"*",
        "",
        "👉 *To view your study timetable, send: **\"Show my daily study plan\"***"
    ])
