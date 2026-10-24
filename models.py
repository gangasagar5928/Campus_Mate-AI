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
