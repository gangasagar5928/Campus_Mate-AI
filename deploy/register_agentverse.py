"""
register_agentverse.py - Agentverse Registration Script
Registers CampusMate AI Student Twin with Agentverse using official Agent Chat Protocol (ACP).
"""

import os
from uagents_core.utils.registration import (
    register_chat_agent,
    RegistrationRequestCredentials,
)

# Parse .env if present in root or deploy dir
for loc in [
    os.path.join(os.path.dirname(__file__), "..", ".env"),
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.getcwd(), ".env")
]:
    if os.path.exists(loc):
        with open(loc, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k not in os.environ:
                        os.environ[k] = v
        break

AGENT_NAME = os.getenv("AGENT_NAME", "Campusmate-AI")
AGENT_ENDPOINT = os.getenv("AGENT_ENDPOINT", "https://campusmate-ai.loca.lt/submit")
AGENTVERSE_KEY = os.getenv("AGENTVERSE_KEY")
AGENT_SEED = os.getenv("AGENT_SEED_PHRASE", "campusmate_student_twin_secret_seed_gcet_2026")

if not AGENTVERSE_KEY:
    raise ValueError("AGENTVERSE_KEY environment variable is required.")

print(f"Registering agent '{AGENT_NAME}' with endpoint '{AGENT_ENDPOINT}'...")

success = register_chat_agent(
    AGENT_NAME,
    AGENT_ENDPOINT,
    active=True,
    credentials=RegistrationRequestCredentials(
        agentverse_api_key=AGENTVERSE_KEY,
        agent_seed_phrase=AGENT_SEED,
    ),
    description="Autonomous academic & placement twin agent coordinating syllabus balance and mock interview drills.",
)

print(f"Registration Result: {'SUCCESS' if success else 'FAILED'}")
