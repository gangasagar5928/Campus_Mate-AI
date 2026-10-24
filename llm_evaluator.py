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

    def _call_gemini(self, user_prompt: str) -> Optional[str]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.gemini_api_key}"
            payload = {"contents": [{"role": "user", "parts": [{"text": f"{EVALUATION_SYSTEM_PROMPT}\n\n{user_prompt}"}]}]}
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception: pass
        return None

    def _call_openai(self, user_prompt: str) -> Optional[str]:
        try:
            headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o-mini", "messages": [{"role": "system", "content": EVALUATION_SYSTEM_PROMPT}, {"role": "user", "content": user_prompt}]}
            resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception: pass
        return None
