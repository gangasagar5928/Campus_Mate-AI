"""
llm_evaluator.py - LLM Evaluation Engine for Company Technical Drills.
"""
import os, json, re, requests
from typing import Dict, Any, List, Optional
from prompts import EVALUATION_SYSTEM_PROMPT, EVALUATION_USER_TEMPLATE, get_score_badge

class LLMEvaluator:
    def __init__(self, gemini_api_key=None, openai_api_key=None, omniroute_url=None, model_name="gemini-1.5-flash"):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.omniroute_url = omniroute_url or os.getenv("OMNIROUTE_URL")
        self.model_name = model_name
