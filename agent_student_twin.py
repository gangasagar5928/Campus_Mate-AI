"""
agent_student_twin.py - Student Twin Agent.
Fetch.ai uAgent representing the student candidate.
Communicates with CompanyInterviewerAgent via uAgents message protocol,
demonstrates standard drill queries, testnet FET payment for Tier-1 mock packs,
and receives structured InterviewEvaluation score badges.
"""

import os
import sys
import time

# Ensure safe UTF-8 output on all operating systems
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uagents import Agent, Context, Protocol
from models import (
    InterviewQuery,
    InterviewQuestionResponse,
    InterviewAnswerSubmission,
    InterviewEvaluation
)
from payment_protocol import PaymentProtocol

# Configuration
STUDENT_AGENT_NAME = "student_twin_agent"
STUDENT_PORT = int(os.getenv("STUDENT_AGENT_PORT", "8001"))
STUDENT_SEED = os.getenv("STUDENT_AGENT_SEED", "student_twin_candidate_seed_fetchai_2026")
INTERVIEWER_ADDRESS = os.getenv("INTERVIEWER_AGENT_ADDRESS", "")

student_agent = Agent(
    name=STUDENT_AGENT_NAME,
    port=STUDENT_PORT,
    seed=STUDENT_SEED,
    endpoint=[f"http://127.0.0.1:{STUDENT_PORT}/submit"]
)

student_protocol = Protocol(name="StudentTwinProtocol", version="1.0.0")
payment_helper = PaymentProtocol()

# Mock student answers for demonstration
SAMPLE_ANSWERS = {
    "qualcomm_verilog_01": (
        "In Verilog, blocking assignments (=) execute sequentially and block execution until complete. "
        "Non-blocking assignments (<=) evaluate the right hand side in the active region and schedule "
        "assignment into the NBA (Non-blocking assignment) event queue region. Sequential always blocks "
        "must use non-blocking (<=) to eliminate race conditions across registers. Combinational always blocks "
        "use blocking (=) to ensure immediate signal update and prevent unintended latch synthesis."
    ),
    "tcs_prime_cpp_01": (
        "In C++, raw pointers require explicit memory deallocation with delete, whereas references are immutable aliases. "
        "Smart pointers automate lifetime via RAII. std::unique_ptr offers exclusive zero-overhead ownership, while "
        "std::shared_ptr maintains an atomic reference counted control block. A memory leak occurs when two shared_ptrs "
        "reference each other cyclically, keeping use_count >= 1. To fix this, std::weak_ptr provides a non-owning observer."
    ),
    "amazon_bst_01": (
        "Checking node.left.val < node.val < node.right.val locally is insufficient because a right grandchild in "
        "the left subtree could exceed the root value. An optimal BST validation algorithm uses range bounds (min, max) "
        "recursively in O(N) time and O(h) space, or checks in-order traversal monotonicity. For Lowest Common Ancestor (LCA), "
        "we iteratively traverse from root: if both p and q are less than node.val, go left; if both greater, go right; "
        "the divergence point is the LCA in O(h) time and O(1) space."
    ),
    "amazon_bar_raiser_01": (
        "For Part A: Amazon-scale distributed cache utilizes consistent hashing with 200 virtual nodes per server to prevent hot spots. "
        "Eviction employs LRU using a hash map combined with a doubly linked list. To stop Cache Stampede, we employ probabilistic "
        "early expiration (XFetch) and distributed lease locks. We use Write-Through with asynchronous cache invalidation.\n\n"
        "For Part B (Leadership Principles): On Prime Day, cache thrashing raised P99 latency to 850ms. Practicing Customer Obsession "
        "and Dive Deep, I identified non-jittered hourly TTL expirations. I executed a Two-Way Door reversible emergency patch adding "
        "15% Gaussian jitter and stale-while-revalidate fallback, restoring P99 latency to 11ms within 4 minutes."
    )
}

# State machine for demo run
student_state = {
    "current_step": "init",
    "target_interviewer": INTERVIEWER_ADDRESS,
    "last_question_id": None,
    "session_id": None
}


@student_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"🎓 Student Twin Agent Online: {STUDENT_AGENT_NAME}")
    ctx.logger.info(f"Student Agent Address: {student_agent.address}")
    ctx.logger.info("Ready to conduct company interview drills.")
    ctx.logger.info("=" * 60)


@student_protocol.on_message(model=InterviewQuestionResponse)
async def handle_question_response(ctx: Context, sender: str, msg: InterviewQuestionResponse):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"📩 Received Interview Response from Company Interviewer ({sender}):")
    ctx.logger.info(f"Session ID: {msg.session_id}")
    ctx.logger.info(f"Company: {msg.company} | Track: {msg.track} | Tier: {msg.tier.upper()}")
    ctx.logger.info(f"Topic: {msg.topic} | Difficulty: {msg.difficulty}")
    ctx.logger.info(f"Is Unlocked: {msg.is_unlocked}")

    if not msg.is_unlocked:
        ctx.logger.warning(f"⚠️ Pack Locked! Required fee: {msg.required_fee_fet} FET")
        ctx.logger.info(f"Payment Instructions: {msg.payment_instructions}")

        # Simulate student completing testnet payment
        ctx.logger.info("💳 Initiating 1.0 TESTNET FET transfer on Dorado testnet...")
        tx_hash = payment_helper.simulate_transfer(
            sender_address=str(student_agent.address),
            amount_fet=1.0,
            memo=f"Unlock {msg.company} {msg.track}"
        )
        ctx.logger.info(f"✅ Payment Broadcast! Tx Hash: {tx_hash}")
        ctx.logger.info("🔄 Resubmitting InterviewQuery with payment voucher...")

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

    # Question is unlocked! Serve to student
    ctx.logger.info("\n" + "-" * 40)
    ctx.logger.info(f"📋 QUESTION PROMPT:\n{msg.question_text}")
    ctx.logger.info("-" * 40 + "\n")

    student_state["last_question_id"] = msg.question_id
    student_state["session_id"] = msg.session_id

    # Formulate answer
    answer_text = SAMPLE_ANSWERS.get(
        msg.question_id,
        "A rigorous, multi-faceted engineering explanation addressing the core principles, architecture, and edge cases."
    )

    ctx.logger.info(f"✍️ Submitting candidate answer for question '{msg.question_id}'...")
    submission = InterviewAnswerSubmission(
        session_id=msg.session_id,
        question_id=msg.question_id,
        student_id=str(student_agent.address),
        student_answer=answer_text
    )
    await ctx.send(sender, submission)


@student_protocol.on_message(model=InterviewEvaluation)
async def handle_evaluation_result(ctx: Context, sender: str, msg: InterviewEvaluation):
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"🏆 RECEIVED INTERVIEW EVALUATION & SCORE BADGE:")
    ctx.logger.info(f"Company: {msg.company} | Question ID: {msg.question_id}")
    ctx.logger.info(f"FINAL SCORE: {msg.score} / 10.0")
    ctx.logger.info(f"SCORE BADGE: {msg.score_badge}")
    ctx.logger.info("\n📊 RUBRIC BREAKDOWN:")
    for metric, score in msg.rubric_breakdown.items():
        ctx.logger.info(f"  • {metric.replace('_', ' ').title()}: {score}")

    ctx.logger.info("\n💪 STRENGTHS IDENTIFIED:")
    for s in msg.strengths:
        ctx.logger.info(f"  + {s}")

    ctx.logger.info("\n⚠️ SYNTHESIS RISKS / TECHNICAL GAPS:")
    for r in msg.synthesis_risks:
        ctx.logger.info(f"  - {r}")

    ctx.logger.info("\n📚 REMEDIAL STUDY TOPICS:")
    for t in msg.remedial_topics:
        ctx.logger.info(f"  * {t}")

    ctx.logger.info(f"\n📝 FEEDBACK SUMMARY:\n{msg.feedback_summary}")
    ctx.logger.info("=" * 60)


student_agent.include(student_protocol)


if __name__ == "__main__":
    print(f"[Starting Student Twin Agent on port {STUDENT_PORT}...]")
    student_agent.run()
