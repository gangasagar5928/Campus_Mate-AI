"""
agent_student_twin.py - Root Entrypoint for CampusMate AI Student Twin Agent.
Routes to agents.student_twin.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.student_twin import student_agent

if __name__ == "__main__":
    print(f"[Starting CampusMate AI Student Twin: {student_agent.address}...]")
    student_agent.run()
