"""
interactive_chat.py - Interactive Chat Interface for Company Interview Drills.
Serves questions, enforces testnet FET payment for Tier-1 mock packs,
and renders real-time LLM grading rubric evaluations with score badges.
Supports both Interactive Terminal CLI mode and Modern Web UI mode.
"""

import os
import sys
import json
import time
import argparse

# Ensure safe UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent_interviewer import serve_interview_query, evaluate_student_submission, payment_protocol
from models import InterviewQuery, InterviewAnswerSubmission

MENU_OPTIONS = [
    {
        "key": "1",
        "company": "qualcomm",
        "tier": "standard",
        "question_id": "qualcomm_verilog_01",
        "label": "Qualcomm: Verilog Blocking vs Non-Blocking (Standard - FREE)"
    },
    {
        "key": "2",
        "company": "qualcomm",
        "tier": "tier-1",
        "question_id": "qualcomm_vlsi_adv_01",
        "label": "Qualcomm: VLSI Advanced Pack - CDC & UPF (Tier-1 - 1.0 FET)"
    },
    {
        "key": "3",
        "company": "tcs_prime",
        "tier": "standard",
        "question_id": "tcs_prime_cpp_01",
        "label": "TCS Prime: C++ Pointers, Memory Leaks & RAII (Standard - FREE)"
    },
    {
        "key": "4",
        "company": "tcs_prime",
        "tier": "tier-1",
        "question_id": "tcs_prime_adv_01",
        "label": "TCS Prime: Advanced Lock-Free Concurrency (Tier-1 - 1.0 FET)"
    },
    {
        "key": "5",
        "company": "amazon",
        "tier": "standard",
        "question_id": "amazon_bst_01",
        "label": "Amazon: Binary Search Trees & LCA (Standard - FREE)"
    },
    {
        "key": "6",
        "company": "amazon",
        "tier": "tier-1",
        "question_id": "amazon_bar_raiser_01",
        "label": "Amazon: Bar Raiser Cache & Leadership Principles (Tier-1 - 1.0 FET)"
    }
]


def print_banner():
    print("=" * 75)
    print("   🎙️  COMPANY-TAILORED INTERVIEW DRILL & PAYMENT PROTOCOL ENGINE")
    print("      Qualcomm  |  TCS Prime  |  Amazon  |  Fetch.ai Testnet FET")
    print("=" * 75)
    print(f"Interviewer FET Wallet: {payment_protocol.agent_address}")
    print("=" * 75)


def run_cli_chat():
    print_banner()
    while True:
        print("\nSelect a recruitment drill track:")
        for opt in MENU_OPTIONS:
            print(f"  [{opt['key']}] {opt['label']}")
        print("  [q] Quit")

        choice = input("\nEnter selection (1-6 or q): ").strip()
        if choice.lower() == 'q':
            print("\nExiting Interview Drill Engine. Best of luck with technical interviews!")
            break

        selected = next((o for o in MENU_OPTIONS if o["key"] == choice), None)
        if not selected:
            print("Invalid selection. Please choose 1-6 or q.")
            continue

        tx_hash = None
        if selected["tier"] == "tier-1":
            print("\n" + "!" * 75)
            print(f"🔒 TIER-1 SPECIALIZED PACK LOCKED: {selected['label']}")
            print("This premium track requires 1.0 TESTNET FET on Fetch.ai Dorado network.")
            print(f"Send 1.0 FET to Interviewer Address: {payment_protocol.agent_address}")
            print("!" * 75)

            pay_choice = input(
                "\nPayment options:\n"
                "  [1] Enter existing Dorado testnet tx_hash\n"
                "  [2] Simulate 1.0 FET testnet transfer (Instant Voucher)\n"
                "  [3] Attempt bypass without payment (test security)\n"
                "Choose payment option (1/2/3): "
            ).strip()

            if pay_choice == "1":
                tx_hash = input("Enter Fetch.ai tx_hash: ").strip()
            elif pay_choice == "2":
                sim_sender = "fetch1student_demo_wallet_address"
                tx_hash = payment_protocol.simulate_transfer(sim_sender, amount_fet=1.0, memo=selected["label"])
                print(f"✅ Generated simulated testnet payment voucher: {tx_hash}")
            else:
                print("Proceeding without payment...")
                tx_hash = None

        # Build and send InterviewQuery
        query = InterviewQuery(
            student_id="student_cli_user",
            company=selected["company"],
            tier=selected["tier"],
            question_id=selected["question_id"],
            payment_tx_hash=tx_hash
        )

        response = serve_interview_query(query, sender="cli_chat_interface")

        if not response.is_unlocked:
            print("\n" + "❌ ACCESS DENIED")
            print(response.question_text)
            if response.payment_instructions:
                print(f"\n{response.payment_instructions}")
            continue

        # Question Unlocked!
        print("\n" + "=" * 75)
        print(f"🎯 COMPANY: {response.company.upper()} | TRACK: {response.track}")
        print(f"📌 TOPIC: {response.topic} | DIFFICULTY: {response.difficulty}")
        print("=" * 75)
        print("\nINTERVIEW QUESTION:")
        print(response.question_text)
        print("\n" + "-" * 75)

        print("\nEnter your technical response below. (Type 'END' on a new line when done):")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        student_answer = "\n".join(lines).strip()

        if not student_answer:
            print("Answer was empty. Skipping evaluation.")
            continue

        print("\n⏳ Submitting to Senior Bar Raiser LLM Evaluation Engine...")
        time.sleep(0.5)

        submission = InterviewAnswerSubmission(
            session_id=response.session_id,
            question_id=response.question_id,
            student_id="student_cli_user",
            student_answer=student_answer
        )

        evaluation = evaluate_student_submission(submission)

        print("\n" + "=" * 75)
        print("                 📋 OFFICIAL INTERVIEW EVALUATION REPORT")
        print("=" * 75)
        print(f"COMPANY: {evaluation.company} | QUESTION ID: {evaluation.question_id}")
        print(f"OVERALL SCORE: {evaluation.score} / 10.0")
        print(f"SCORE BADGE:   {evaluation.score_badge}")
        print("-" * 75)

        print("\n📊 CRITERIA BREAKDOWN:")
        for criterion, pts in evaluation.rubric_breakdown.items():
            print(f"  • {criterion.replace('_', ' ').title():<25} : {pts:>4.1f} pts")

        print("\n💪 TECHNICAL STRENGTHS IDENTIFIED:")
        for s in evaluation.strengths:
            print(f"  + {s}")

        print("\n⚠️ SYNTHESIS RISKS / DANGEROUS GAPS:")
        for r in evaluation.synthesis_risks:
            print(f"  - {r}")

        print("\n📚 HIGH-YIELD REMEDIAL STUDY TOPICS:")
        for t in evaluation.remedial_topics:
            print(f"  * {t}")

        print("\n📝 COACHING SUMMARY:")
        print(f"  {evaluation.feedback_summary}")
        print("=" * 75)

        input("\nPress Enter to return to main menu...")


def run_web_server(port: int = 5000):
    """Launches a lightweight Web interface for live hackathon video demo."""
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel

    app = FastAPI(title="Interviewer Agent & Payment Protocol")

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OmniRoute Interviewer Agent & FET Payment Protocol</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
    <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50 py-4 px-6">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">AI</div>
                <div>
                    <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-indigo-400">OmniRoute Interviewer Agent</h1>
                    <p class="text-xs text-slate-400">Qualcomm • TCS Prime • Amazon • Fetch.ai Payment Protocol</p>
                </div>
            </div>
            <div class="flex items-center gap-3 bg-slate-800/80 border border-slate-700 rounded-full px-4 py-1.5 text-xs">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span class="text-slate-300">Testnet FET Wallet:</span>
                <code class="text-cyan-300 font-mono" id="wallet-badge">""" + payment_protocol.agent_address[:18] + """...</code>
            </div>
        </div>
    </header>

    <main class="max-w-6xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Sidebar Track Selector -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h2 class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">Target Recruitment Tracks</h2>
            <div class="space-y-3">
                <button onclick="selectTrack('qualcomm', 'standard', 'qualcomm_verilog_01')" class="track-btn w-full text-left p-3.5 rounded-xl border border-slate-800 hover:border-cyan-500/50 bg-slate-800/50 hover:bg-slate-800 transition active:scale-[0.98]">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-cyan-400">Qualcomm VLSI</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Standard FREE</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1">Verilog blocking vs non-blocking assignments & race conditions.</p>
                </button>

                <button onclick="selectTrack('qualcomm', 'tier-1', 'qualcomm_vlsi_adv_01')" class="track-btn w-full text-left p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/20 hover:border-amber-500/60 hover:bg-amber-950/40 transition active:scale-[0.98]">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-amber-300">Qualcomm Advanced Pack</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">Tier-1 • 1 FET</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1">Clock Domain Crossing (CDC) FIFO & UPF multi-voltage gating.</p>
                </button>

                <button onclick="selectTrack('tcs_prime', 'standard', 'tcs_prime_cpp_01')" class="track-btn w-full text-left p-3.5 rounded-xl border border-slate-800 hover:border-indigo-500/50 bg-slate-800/50 hover:bg-slate-800 transition active:scale-[0.98]">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-indigo-400">TCS Prime Systems</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Standard FREE</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1">C++ pointers, memory management, RAII & weak_ptr.</p>
                </button>

                <button onclick="selectTrack('amazon', 'standard', 'amazon_bst_01')" class="track-btn w-full text-left p-3.5 rounded-xl border border-slate-800 hover:border-orange-500/50 bg-slate-800/50 hover:bg-slate-800 transition active:scale-[0.98]">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-orange-400">Amazon DSA</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Standard FREE</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1">Binary Search Tree validation and Lowest Common Ancestor (LCA).</p>
                </button>

                <button onclick="selectTrack('amazon', 'tier-1', 'amazon_bar_raiser_01')" class="track-btn w-full text-left p-3.5 rounded-xl border border-amber-500/30 bg-amber-950/20 hover:border-amber-500/60 hover:bg-amber-950/40 transition active:scale-[0.98]">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-amber-300">Amazon Bar Raiser Drill</span>
                        <span class="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">Tier-1 • 1 FET</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1">Distributed cache stampede & Leadership Principles (Customer Obsession).</p>
                </button>
            </div>

            <!-- Payment Protocol Box -->
            <div class="mt-6 p-4 rounded-xl bg-slate-800/40 border border-slate-700/60">
                <div class="flex items-center gap-2 mb-2">
                    <span class="text-amber-400">💳</span>
                    <h3 class="text-xs font-semibold uppercase text-slate-300">Payment Protocol Sandbox</h3>
                </div>
                <p class="text-xs text-slate-400 mb-3">Transfer 1.0 testnet FET on Dorado to unlock Tier-1 packs.</p>
                <button onclick="generateSimulatedPayment()" class="w-full py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold rounded-lg text-xs shadow-lg shadow-amber-500/20 transition">
                    Generate 1.0 FET Payment Voucher
                </button>
                <div id="payment-voucher-box" class="mt-2 hidden">
                    <p class="text-[10px] text-slate-400">Voucher Tx Hash:</p>
                    <input id="tx-hash-input" type="text" readonly class="w-full bg-slate-950 text-cyan-300 font-mono text-[11px] p-1.5 rounded border border-slate-700 mt-1">
                </div>
            </div>
        </div>

        <!-- Question & Answer Area -->
        <div class="lg:col-span-2 space-y-6">
            <div id="question-card" class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <div class="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                    <div>
                        <span id="q-company" class="text-xs font-bold uppercase tracking-wider text-cyan-400">Qualcomm</span>
                        <h2 id="q-topic" class="text-lg font-bold text-slate-100">Verilog Blocking vs Non-Blocking Assignments</h2>
                    </div>
                    <span id="q-tier-badge" class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Free Drill</span>
                </div>
                <p id="q-text" class="text-slate-300 text-sm leading-relaxed whitespace-pre-line"></p>
                
                <div id="payment-warning" class="hidden mt-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs"></div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <label class="block text-sm font-semibold text-slate-300 mb-2">Candidate Interview Response</label>
                <textarea id="answer-text" rows="7" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 transition font-sans" placeholder="Formulate your detailed technical response here..."></textarea>
                <div class="mt-4 flex justify-between items-center">
                    <span class="text-xs text-slate-500" id="word-count">0 words</span>
                    <button id="submit-btn" onclick="submitAnswer()" class="px-6 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 font-bold text-white rounded-xl shadow-lg shadow-indigo-500/20 transition active:scale-95 text-sm">
                        Submit for Senior LLM Grading
                    </button>
                </div>
            </div>

            <!-- Evaluation Card -->
            <div id="evaluation-card" class="hidden bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
                <div class="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                    <div>
                        <h3 class="text-base font-bold text-slate-100">Bar Raiser Grading Report</h3>
                        <p class="text-xs text-slate-400" id="eval-timestamp"></p>
                    </div>
                    <div class="text-right">
                        <div class="text-3xl font-black text-cyan-400" id="eval-score">0.0<span class="text-sm text-slate-500 font-normal"> / 10.0</span></div>
                        <div id="eval-badge" class="text-xs font-semibold px-2.5 py-1 rounded-full mt-1"></div>
                    </div>
                </div>

                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
                    <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                        <span class="text-[10px] uppercase text-slate-500 block">Technical Accuracy</span>
                        <span id="score-tech" class="text-base font-bold text-slate-200">0.0 / 4.0</span>
                    </div>
                    <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                        <span class="text-[10px] uppercase text-slate-500 block">Depth & Mechanics</span>
                        <span id="score-depth" class="text-base font-bold text-slate-200">0.0 / 3.0</span>
                    </div>
                    <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                        <span class="text-[10px] uppercase text-slate-500 block">Edge Cases & Risks</span>
                        <span id="score-edge" class="text-base font-bold text-slate-200">0.0 / 2.0</span>
                    </div>
                    <div class="p-3 bg-slate-950 rounded-xl border border-slate-800 text-center">
                        <span class="text-[10px] uppercase text-slate-500 block">Clarity & Style</span>
                        <span id="score-clarity" class="text-base font-bold text-slate-200">0.0 / 1.0</span>
                    </div>
                </div>

                <div class="space-y-4 text-xs">
                    <div>
                        <h4 class="font-bold text-emerald-400 mb-1 flex items-center gap-1.5"><span>💪</span> Demonstrated Strengths</h4>
                        <ul id="eval-strengths" class="space-y-1 text-slate-300 list-disc list-inside"></ul>
                    </div>
                    <div>
                        <h4 class="font-bold text-rose-400 mb-1 flex items-center gap-1.5"><span>⚠️</span> Synthesis Risks & Gaps</h4>
                        <ul id="eval-risks" class="space-y-1 text-slate-300 list-disc list-inside"></ul>
                    </div>
                    <div>
                        <h4 class="font-bold text-amber-400 mb-1 flex items-center gap-1.5"><span>📚</span> High-Yield Remedial Topics</h4>
                        <ul id="eval-remedial" class="space-y-1 text-slate-300 list-disc list-inside"></ul>
                    </div>
                    <div class="p-3 bg-slate-950 rounded-xl border border-slate-800">
                        <h4 class="font-bold text-slate-300 mb-1">Interviewer Feedback</h4>
                        <p id="eval-feedback" class="text-slate-400 leading-relaxed"></p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let currentQuestion = null;

        async function selectTrack(company, tier, qId) {
            const txHash = document.getElementById('tx-hash-input').value;
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    student_id: 'web_student',
                    company: company,
                    tier: tier,
                    question_id: qId,
                    payment_tx_hash: txHash
                })
            });
            const data = await res.json();
            currentQuestion = data;
            renderQuestion(data);
        }

        function renderQuestion(q) {
            document.getElementById('q-company').innerText = q.company;
            document.getElementById('q-topic').innerText = q.topic + ' (' + q.difficulty + ')';
            document.getElementById('q-text').innerText = q.question_text;
            
            const badge = document.getElementById('q-tier-badge');
            const warn = document.getElementById('payment-warning');

            if (!q.is_unlocked) {
                badge.innerText = '🔒 Locked (1.0 FET Required)';
                badge.className = 'px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30';
                warn.innerText = q.payment_instructions || 'Tier-1 Pack Locked. Please generate and submit 1.0 FET payment voucher.';
                warn.classList.remove('hidden');
            } else {
                badge.innerText = q.tier === 'tier-1' ? '🔓 Tier-1 Unlocked' : 'Free Standard';
                badge.className = q.tier === 'tier-1' 
                    ? 'px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
                warn.classList.add('hidden');
            }
        }

        async function generateSimulatedPayment() {
            const res = await fetch('/api/simulate-payment', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ amount_fet: 1.0 })
            });
            const data = await res.json();
            document.getElementById('tx-hash-input').value = data.tx_hash;
            document.getElementById('payment-voucher-box').classList.remove('hidden');
        }

        async function submitAnswer() {
            if (!currentQuestion || !currentQuestion.is_unlocked) {
                alert('Please unlock or select an active question first!');
                return;
            }
            const answer = document.getElementById('answer-text').value;
            if (!answer.trim()) {
                alert('Please enter your technical answer before submitting.');
                return;
            }

            const btn = document.getElementById('submit-btn');
            btn.innerText = 'Evaluating with Bar Raiser LLM...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/evaluate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: currentQuestion.session_id,
                        question_id: currentQuestion.question_id,
                        student_id: 'web_student',
                        student_answer: answer
                    })
                });
                const evalData = await res.json();
                renderEvaluation(evalData);
            } finally {
                btn.innerText = 'Submit for Senior LLM Grading';
                btn.disabled = false;
            }
        }

        function renderEvaluation(e) {
            const card = document.getElementById('evaluation-card');
            card.classList.remove('hidden');
            document.getElementById('eval-timestamp').innerText = 'Graded at ' + e.timestamp;
            document.getElementById('eval-score').innerHTML = e.score.toFixed(1) + '<span class="text-sm text-slate-500 font-normal"> / 10.0</span>';
            
            const badge = document.getElementById('eval-badge');
            badge.innerText = e.score_badge;
            if (e.score >= 9.0) {
                badge.className = 'text-xs font-semibold px-2.5 py-1 rounded-full mt-1 bg-amber-500/20 text-amber-300 border border-amber-500/30';
            } else if (e.score >= 7.5) {
                badge.className = 'text-xs font-semibold px-2.5 py-1 rounded-full mt-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
            } else {
                badge.className = 'text-xs font-semibold px-2.5 py-1 rounded-full mt-1 bg-rose-500/20 text-rose-300 border border-rose-500/30';
            }

            document.getElementById('score-tech').innerText = (e.rubric_breakdown.technical_correctness || 0).toFixed(1) + ' / 4.0';
            document.getElementById('score-depth').innerText = (e.rubric_breakdown.depth_and_mechanics || 0).toFixed(1) + ' / 3.0';
            document.getElementById('score-edge').innerText = (e.rubric_breakdown.edge_cases_and_risks || 0).toFixed(1) + ' / 2.0';
            document.getElementById('score-clarity').innerText = (e.rubric_breakdown.clarity_and_precision || 0).toFixed(1) + ' / 1.0';

            const strList = document.getElementById('eval-strengths');
            strList.innerHTML = e.strengths.map(s => `<li>${s}</li>`).join('');

            const riskList = document.getElementById('eval-risks');
            riskList.innerHTML = e.synthesis_risks.map(r => `<li>${r}</li>`).join('');

            const remList = document.getElementById('eval-remedial');
            remList.innerHTML = e.remedial_topics.map(t => `<li>${t}</li>`).join('');

            document.getElementById('eval-feedback').innerText = e.feedback_summary;
            card.scrollIntoView({ behavior: 'smooth' });
        }

        // Initialize with default Qualcomm track
        selectTrack('qualcomm', 'standard', 'qualcomm_verilog_01');
    </script>
</body>
</html>
"""

    @app.get("/", response_class=HTMLResponse)
    async def get_index():
        return HTMLResponse(HTML_TEMPLATE)

    class QueryReq(BaseModel):
        student_id: str = "web_user"
        company: str
        tier: str = "standard"
        question_id: str
        payment_tx_hash: str = None

    @app.post("/api/query")
    async def api_query(req: QueryReq):
        q = InterviewQuery(
            student_id=req.student_id,
            company=req.company,
            tier=req.tier,
            question_id=req.question_id,
            payment_tx_hash=req.payment_tx_hash
        )
        resp = serve_interview_query(q, sender="web_interface")
        return JSONResponse(resp.model_dump())

    class SimPayReq(BaseModel):
        amount_fet: float = 1.0

    @app.post("/api/simulate-payment")
    async def api_sim_pay(req: SimPayReq):
        tx = payment_protocol.simulate_transfer("fetch1web_student_wallet", amount_fet=req.amount_fet)
        return JSONResponse({"tx_hash": tx, "status": "success"})

    class EvalReq(BaseModel):
        session_id: str
        question_id: str
        student_id: str
        student_answer: str

    @app.post("/api/evaluate")
    async def api_evaluate(req: EvalReq):
        sub = InterviewAnswerSubmission(
            session_id=req.session_id,
            question_id=req.question_id,
            student_id=req.student_id,
            student_answer=req.student_answer
        )
        ev = evaluate_student_submission(sub)
        return JSONResponse(ev.model_dump())

    print(f"\n[Launching Modern Interviewer Agent Web UI on http://127.0.0.1:{port}]")
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OmniRoute Interviewer Agent & Payment Protocol")
    parser.add_argument("--web", action="store_true", help="Launch interactive modern Web dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Web server port")
    args = parser.parse_args()

    if args.web:
        run_web_server(port=args.port)
    else:
        run_cli_chat()
