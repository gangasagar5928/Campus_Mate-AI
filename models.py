"""
models.py - Message Schemas for Company Interviewer Agent and Student Twin Agent.
Built on Fetch.ai uAgents Model framework.
"""
from typing import Optional, List, Dict, Any
from uagents import Model

class InterviewQuery(Model):
    student_id: str
    company: str
    tier: str = "standard"
    question_id: Optional[str] = None
    payment_tx_hash: Optional[str] = None
    session_id: Optional[str] = None

class InterviewQuestionResponse(Model):
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
    session_id: str
    question_id: str
    student_id: str
    student_answer: str
