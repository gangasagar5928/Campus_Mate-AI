"""
main.py - CampusMate AI Entrypoint.
Autonomous Academic & Placement Twin Agent discovered via ASI:One (ACP 0.3.0).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.student_twin import student_agent

def main():
    print("=" * 60)
    print("Starting CampusMate AI (Autonomous Academic & Career Agent)...")
    print(f"Agent Address: {student_agent.address}")
    print("=" * 60)
    student_agent.run()

if __name__ == "__main__":
    main()
