"""
agent_interviewer.py - Company Interviewer Agent.
Fetch.ai uAgent serving company-tailored technical interview drills (Qualcomm, TCS Prime, Amazon),
LLM grading rubric evaluation, and testnet FET Payment Protocol for Tier-1 mock packs.
"""

import os
import sys
import json
import time
import uuid
from typing import Dict, Any, Optional

# Ensure safe UTF-8 output on all operating systems
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from uagents import Agent, Context, Protocol
from models import (
    InterviewQuery,
    InterviewQuestionResponse,
    InterviewAnswerSubmission,
    InterviewEvaluation,
    PaymentVerificationQuery,
    PaymentVerificationResponse
)
from payment_protocol import PaymentProtocol
from llm_evaluator import LLMEvaluator

# Configuration
AGENT_NAME = "company_interviewer"
AGENT_PORT = int(os.getenv("INTERVIEWER_AGENT_PORT", "8000"))
AGENT_SEED = os.getenv("INTERVIEWER_AGENT_SEED", "company_interviewer_fetchai_hackathon_seed_2026")
INTERVIEW_BANK_PATH = os.path.join(os.path.dirname(__file__), "interview_bank.json")

# Initialize Company Interviewer Agent
interviewer_agent = Agent(
    name=AGENT_NAME,
    port=AGENT_PORT,
    seed=AGENT_SEED,
    endpoint=[f"http://127.0.0.1:{AGENT_PORT}/submit"]
)

interviewer_protocol = Protocol(name="CompanyInterviewerProtocol", version="1.0.0")

# Core Engine components
payment_protocol = PaymentProtocol()
llm_evaluator = LLMEvaluator()

# Load question bank
with open(INTERVIEW_BANK_PATH, "r", encoding="utf-8") as f:
    INTERVIEW_BANK = json.load(f)["companies"]

# In-memory session tracking: session_id -> metadata
active_sessions: Dict[str, Dict[str, Any]] = {}


def find_question(company_key: str, tier: str = "standard", question_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Helper to locate target question in the interview bank."""
    company_data = INTERVIEW_BANK.get(company_key.lower().strip())
    if not company_data:
        # Fallback search across all companies
        for c_data in INTERVIEW_BANK.values():
            for q in c_data.get("questions", []):
                if question_id and q.get("id") == question_id:
                    return q
        return None

    questions = company_data.get("questions", [])
    if question_id:
        for q in questions:
            if q.get("id") == question_id:
                return q

    # Match by tier
    for q in questions:
        if q.get("tier", "standard").lower() == tier.lower():
            return q

    return questions[0] if questions else None


def serve_interview_query(query: InterviewQuery, sender: str = "student_agent") -> InterviewQuestionResponse:
    """
    Core business logic for processing an InterviewQuery.
    Can be invoked via uAgent message or directly via CLI/Web interface.
    """
    company_key = query.company.lower().strip()
    tier_requested = query.tier.lower().strip()
    session_id = query.session_id or f"sess_{uuid.uuid4().hex[:8]}"

    q_data = find_question(company_key, tier=tier_requested, question_id=query.question_id)
    if not q_data:
        return InterviewQuestionResponse(
            session_id=session_id,
            question_id="unknown",
            company=query.company,
            track="Unknown",
            tier=tier_requested,
            topic="Not Found",
            difficulty="N/A",
            question_text=f"No interview question found for company '{query.company}' and tier '{tier_requested}'. Available companies: qualcomm, tcs_prime, amazon.",
            is_unlocked=False,
            required_fee_fet=0.0,
            interviewer_wallet_address=payment_protocol.agent_address,
            payment_instructions=None
        )

    # Check if question is a Tier-1 Premium Mock Pack
    is_tier_1 = (q_data.get("tier", "standard").lower() == "tier-1")
    fee_fet = float(q_data.get("fee_fet", 1.0 if is_tier_1 else 0.0))

    if is_tier_1:
        # Enforce Payment Protocol
        is_paid, pay_msg, pay_meta = payment_protocol.verify_payment(
            tx_hash=query.payment_tx_hash,
            expected_min_fet=fee_fet,
            student_id=query.student_id or sender
        )
        if not is_paid:
            # Payment required: return locked gate with payment instructions
            instructions = payment_protocol.get_payment_instructions(
                pack_name=q_data.get("track", q_data.get("topic")),
                fee_fet=fee_fet
            )
            return InterviewQuestionResponse(
                session_id=session_id,
                question_id=q_data["id"],
                company=q_data["company"],
                track=q_data["track"],
                tier=q_data["tier"],
                topic=q_data["topic"],
                difficulty=q_data["difficulty"],
                question_text=f"🔒 [LOCKED] {pay_msg}\n\nTo unlock the Tier-1 Mock Pack, submit 1.0 testnet FET transfer proof.",
                is_unlocked=False,
                required_fee_fet=fee_fet,
                interviewer_wallet_address=payment_protocol.agent_address,
                payment_instructions=instructions
            )

    # Question is unlocked (either free standard or paid Tier-1)
    active_sessions[session_id] = {
        "question_id": q_data["id"],
        "student_id": query.student_id,
        "sender": sender,
        "company": q_data["company"],
        "tier": q_data["tier"],
        "unlocked_at": time.time()
    }

    return InterviewQuestionResponse(
        session_id=session_id,
        question_id=q_data["id"],
        company=q_data["company"],
        track=q_data["track"],
        tier=q_data["tier"],
        topic=q_data["topic"],
        difficulty=q_data["difficulty"],
        question_text=q_data["question"],
        is_unlocked=True,
        required_fee_fet=0.0,
        interviewer_wallet_address=payment_protocol.agent_address,
        payment_instructions=None
    )


def evaluate_student_submission(submission: InterviewAnswerSubmission) -> InterviewEvaluation:
    """
    Evaluates submitted answer against structured LLM grading rubric.
    """
    # Locate question metadata
    q_data = None
    for c_data in INTERVIEW_BANK.values():
        for q in c_data.get("questions", []):
            if q.get("id") == submission.question_id:
                q_data = q
                break
        if q_data:
            break

    if not q_data:
        # Fallback question structure if not located
        q_data = {
            "id": submission.question_id,
            "company": "Technical Track",
            "topic": "General Engineering Drill",
            "expected_rubric": {"must_include": ["Clarity", "Correctness"]}
        }

    # Execute LLM rubric evaluation
    eval_result = llm_evaluator.evaluate_answer(q_data, submission.student_answer)

    return InterviewEvaluation(
        session_id=submission.session_id,
        question_id=submission.question_id,
        student_id=submission.student_id,
        company=q_data.get("company", "Tech Company"),
        score=eval_result["score"],
        score_badge=eval_result["score_badge"],
        rubric_breakdown=eval_result["rubric_breakdown"],
        strengths=eval_result["strengths"],
        synthesis_risks=eval_result["synthesis_risks"],
        remedial_topics=eval_result["remedial_topics"],
        feedback_summary=eval_result["feedback_summary"],
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )


# --- uAgent Message Handlers ---

@interviewer_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"🚀 Company Interviewer Agent Online: {AGENT_NAME}")
    ctx.logger.info(f"Agent Address: {interviewer_agent.address}")
    ctx.logger.info(f"Testnet FET Wallet Address: {payment_protocol.agent_address}")
    ctx.logger.info("Question Bank Loaded Tracks: Qualcomm, TCS Prime, Amazon")
    ctx.logger.info("Payment Protocol: 1.0 Testnet FET required for Tier-1 Packs")
    ctx.logger.info("=" * 60)


@interviewer_protocol.on_message(model=InterviewQuery, replies={InterviewQuestionResponse})
async def handle_interview_query(ctx: Context, sender: str, msg: InterviewQuery):
    ctx.logger.info(f"[CompanyInterviewer] Received InterviewQuery from {sender} | Company: {msg.company} | Tier: {msg.tier}")
    response = serve_interview_query(msg, sender=sender)
    if response.is_unlocked:
        ctx.logger.info(f"[CompanyInterviewer] Serving unlocked question '{response.question_id}' to {sender}")
    else:
        ctx.logger.info(f"[CompanyInterviewer] Tier-1 gate locked for {sender}. Fee required: {response.required_fee_fet} FET")
    await ctx.send(sender, response)


@interviewer_protocol.on_message(model=InterviewAnswerSubmission, replies={InterviewEvaluation})
async def handle_answer_submission(ctx: Context, sender: str, msg: InterviewAnswerSubmission):
    ctx.logger.info(f"[CompanyInterviewer] Received answer submission for question '{msg.question_id}' from {sender}")
    evaluation = evaluate_student_submission(msg)
    ctx.logger.info(f"[CompanyInterviewer] Grading completed. Score: {evaluation.score}/10.0 | Badge: {evaluation.score_badge}")
    await ctx.send(sender, evaluation)


@interviewer_protocol.on_message(model=PaymentVerificationQuery, replies={PaymentVerificationResponse})
async def handle_payment_query(ctx: Context, sender: str, msg: PaymentVerificationQuery):
    is_valid, message, meta = payment_protocol.verify_payment(msg.tx_hash, expected_min_fet=1.0, student_id=msg.student_id)
    resp = PaymentVerificationResponse(
        tx_hash=msg.tx_hash,
        is_valid=is_valid,
        amount_fet=meta.get("amount_fet", 0.0),
        sender=meta.get("sender", "unknown"),
        recipient=payment_protocol.agent_address,
        message=message
    )
    await ctx.send(sender, resp)


interviewer_agent.include(interviewer_protocol)


if __name__ == "__main__":
    print(f"[Starting Company Interviewer Agent on port {AGENT_PORT}...]")
    interviewer_agent.run()
