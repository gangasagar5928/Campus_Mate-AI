import json

with open("curriculum.json", "r", encoding="utf-8") as f:
    curriculum = json.load(f)

with open("interview_bank.json", "r", encoding="utf-8") as f:
    bank = json.load(f)

with open("cloud_agent_template.py", "r", encoding="utf-8") as f:
    template = f.read()

output = template.replace("__CURRICULUM_JSON__", json.dumps(curriculum, indent=2))
output = output.replace("__INTERVIEW_BANK_JSON__", json.dumps(bank, indent=2))

with open("agentverse_cloud_agent.py", "w", encoding="utf-8") as f:
    f.write(output)

print(f"Generated agentverse_cloud_agent.py! Size: {len(output)} bytes")
