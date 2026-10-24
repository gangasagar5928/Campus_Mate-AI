"""
models.py - Message Schemas for Company Interviewer Agent and Student Twin Agent.
Built on Fetch.ai uAgents Model framework.
"""

from typing import Optional, List, Dict, Any
from uagents import Model


class InterviewQuery(Model):
    """
    Sent by StudentTwinAgent to request an interview question or pack.
    """
    student_id: str
    company: str  # e.g., 'qualcomm', 'tcs_prime', 'amazon'
    tier: str = "standard"  # 'standard' (free) or 'tier-1' (requires 1 FET)
    question_id: Optional[str] = None
    payment_tx_hash: Optional[str] = None
    session_id: Optional[str] = None


class InterviewQuestionResponse(Model):
    """
    Returned by CompanyInterviewerAgent with the selected drill question
    or a payment barrier if Tier-1 pack is locked.
    """
    session_id: str
    question_id: str
    company: str
    track: str
    tier: str
    topic: str
    difficulty: str
    question_text: str
    is_unlocked: bool
    required_fee_fet: float = 0.0
    interviewer_wallet_address: str = ""
    payment_instructions: Optional[str] = None


class InterviewAnswerSubmission(Model):
    """
    Sent by StudentTwinAgent containing the candidate's technical response.
    """
    session_id: str
    question_id: str
    student_id: str
    student_answer: str


class InterviewEvaluation(Model):
    """
    Returned by CompanyInterviewerAgent with the numerical score out of 10.0,
    score badge, strengths, synthesis risks, and remedial topics.
    """
    session_id: str
    question_id: str
    student_id: str
    company: str
    score: float
    score_badge: str
    rubric_breakdown: Dict[str, float]
    strengths: List[str]
    synthesis_risks: List[str]
    remedial_topics: List[str]
    feedback_summary: str
    timestamp: str


class PaymentVerificationQuery(Model):
    """
    Optional query to verify testnet FET transaction status ahead of drill.
    """
    student_id: str
    tx_hash: str
    pack_id: str


class PaymentVerificationResponse(Model):
    """
    Response indicating whether payment has been confirmed on the ledger.
    """
    tx_hash: str
    is_valid: bool
    amount_fet: float
    sender: str
    recipient: str
    message: str
