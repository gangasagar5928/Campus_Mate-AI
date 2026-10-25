import re

def test_intent_matching(query: str):
    lower = query.lower()
    
    # Check Profile Update
    b_match = re.search(r"\b(ece|cse|it|mech)\b", lower)
    s_match = re.search(r"(?:semester|sem)\s*(\d+)", lower)
    c_match = None
    for c in ["qualcomm", "google", "nvidia", "microsoft", "amazon", "tcs"]:
        if c in lower:
            c_match = c
            break

    # Intent A: Balancing Formula & Strategy
    if any(k in lower for k in ["how do you balance", "balancing formula", "how does it balance", "ratio", "60/40", "50/50", "10/90", "academic debt", "balancing work"]):
        return "INTENT_BALANCING_STRATEGY"

    # Intent B: Branches & AKTU Coverage
    if any(k in lower for k in ["which branch", "what branches", "branches supported", "is cse supported", "is mech supported", "aktu coverage", "all semesters"]):
        return "INTENT_BRANCHES_COVERAGE"

    # Intent C: Target Company Strategy & Placement Guide
    if any(k in lower for k in ["how to prepare for", "recruitment guide", "placement guide", "interview tips", "what does google ask", "qualcomm prep"]):
        return "INTENT_COMPANY_GUIDE"

    # Intent D: Web3 / FET Micropayments
    if any(k in lower for k in ["fet token", "dorado", "how to unlock", "micropayment", "wallet", "faucet", "testnet fet"]):
        return "INTENT_WEB3_PAYMENTS"

    # Intent E: Sessional Exam Strategy & CGPA Protection
    if any(k in lower for k in ["cgpa", "exam tips", "how to score high", "sessional tips", "study tips"]):
        return "INTENT_EXAM_TIPS"

    # Intent F: Remedial Hook & Mutation Details
    if any(k in lower for k in ["remedial hook", "mutation hook", "why did my schedule change", "remedial mutation"]):
        return "INTENT_REMEDIAL_HOOK"

    # Intent G: Profile Status
    if any(k in lower for k in ["my profile", "current settings", "my current branch", "my status"]):
        return "INTENT_PROFILE_STATUS"

    return "OTHER"

queries = [
    "How do you balance college and placement?",
    "Explain the 60/40 ratio",
    "Which branches are supported?",
    "How to prepare for Qualcomm?",
    "What does Google ask in interviews?",
    "How to unlock Amazon pack with FET?",
    "Tips to score high in AKTU sessional",
    "What is the evening remedial mutation hook?",
    "Show my profile"
]

for q in queries:
    print(f"'{q}' -> {test_intent_matching(q)}")
