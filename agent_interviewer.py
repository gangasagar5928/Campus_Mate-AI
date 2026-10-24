"""
agent_interviewer.py - Company Interviewer Agent.
"""
import os, sys, json, time, uuid
from uagents import Agent, Context, Protocol
from models import InterviewQuery, InterviewQuestionResponse, InterviewAnswerSubmission, InterviewEvaluation
from payment_protocol import PaymentProtocol
from llm_evaluator import LLMEvaluator

AGENT_NAME = "company_interviewer"
AGENT_PORT = int(os.getenv("INTERVIEWER_AGENT_PORT", "8000"))
interviewer_agent = Agent(name=AGENT_NAME, port=AGENT_PORT, seed="seed_2026")
interviewer_protocol = Protocol(name="CompanyInterviewerProtocol", version="1.0.0")
payment_protocol = PaymentProtocol()
llm_evaluator = LLMEvaluator()
