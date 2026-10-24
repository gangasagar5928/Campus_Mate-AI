# 🎬 Hackathon Submission Video Script & Storyboard
**Role:** Member 3: Interviewer Agent, Payment Protocol & Video Lead  
**Project:** OmniRoute - Multi-Agent Interview Drill Engine & Monetization Protocol  
**Target Video Duration:** 3:00 Minutes  
**Target Audience:** Hackathon Judges, Fetch.ai Core Engineers, Recruiters  

---

## ⏱️ Video Timeline Breakdown

| Timestamp | Segment | Visual On Screen | Narration / Voiceover |
|---|---|---|---|
| **0:00 - 0:25** | **The Hook & Problem** | Architecture diagram: Candidate Twin connecting to Company Interviewer Agent via Fetch.ai uAgents protocol. | *"Technical interviews at Tier-1 tech giants like Qualcomm, TCS Prime, and Amazon have an unforgiving technical bar. Generalist chatbots give generic answers without company rubrics or financial stakes. Welcome to Member 3's subsystem: The Company Interviewer Agent and FET Payment Protocol."* |
| **0:25 - 0:55** | **Agent Architecture & Standard Drill** | Terminal / Web UI: StudentTwinAgent sends `InterviewQuery` for Qualcomm Verilog blocking vs non-blocking track. Live question served instantly. | *"Built on Fetch.ai's uAgents framework, our Company Interviewer Agent dynamically queries a curated recruitment bank. Here, a student twin requests the Qualcomm VLSI track. The agent serves a deep hardware question on Verilog event queues and delta cycles."* |
| **0:55 - 1:35** | **LLM Grading Rubric & Score Badges** | Student submits technical answer. Screen displays LLM evaluation card with score badge (`🏆 Outstanding / ✅ Strong Pass`), criteria breakdown, strengths, and remedial topics. | *"When the student submits their response, our Senior Bar Raiser LLM engine evaluates it against an uncompromising 10.0 rubric. It breaks down technical accuracy out of 4, depth out of 3, edge cases out of 2, and clarity out of 1. It identifies exact synthesis risks—like latch inference—and outputs targeted remedial study topics."* |
| **1:35 - 2:20** | **Bonus Criteria: 1 FET Payment Protocol** | Screen attempts to access Tier-1 Amazon Bar Raiser Drill. A red lock triggers: *Payment Required: 1.0 Testnet FET*. Student agent executes Dorado transfer; payment confirmed; drill unlocks! | *"Now, the bonus monetization criteria: Specialized Tier-1 mock packs—like the Amazon Bar Raiser Drill or Qualcomm VLSI Advanced Pack—are protected by our Fetch.ai testnet FET payment protocol. When accessed without payment, the gate rejects the request with the agent's bech32 wallet address. The student agent executes a 1.0 testnet FET transfer on the Dorado network. CosmPy validates the transaction, enforces cryptographic replay protection, and unlocks the Tier-1 Bar Raiser drill!"* |
| **2:20 - 2:45** | **End-to-End Multi-Agent Bureau** | Terminal executing `python demo_multiagent_bureau.py` showing concurrent Bureau event loop with both agents communicating autonomously. | *"Everything runs seamlessly in a Fetch.ai Bureau or distributed across network endpoints. The entire cycle—from interview query, to on-chain FET monetization, to Bar Raiser LLM evaluation—runs autonomously without human middlemen."* |
| **2:45 - 3:00** | **Conclusion & Impact** | Clean summary slide with GitHub link, team credits, and Fetch.ai ecosystem badge. | *"OmniRoute delivers company-tailored interview mastery powered by autonomous agents and Web3 micropayments. Thank you for watching!"* |

---

## 🎥 Recording Checklist for Video Lead

1. **Resolution & Settings:**
   - Record in 1080p (1920x1080) at 60 FPS using OBS Studio.
   - Use high-contrast dark theme (terminal with glowing cyan/amber text or the modern Tailwind Web UI on `http://127.0.0.1:5000`).

2. **Terminal Preparation:**
   ```powershell
   # Launch Modern Web Dashboard Demo:
   python interactive_chat.py --web

   # Or launch CLI Multi-Agent Bureau Demo:
   python demo_multiagent_bureau.py
   ```

3. **Key Visual Moments to Highlight:**
   - **Wallet Address:** Show the Fetch.ai Dorado testnet wallet address (`fetch1...`).
   - **Payment Rejection:** Highlight the locked Tier-1 prompt before payment.
   - **Payment Confirmation:** Show the transaction hash verified and instant unlock.
   - **Score Badge:** Zoom in on the score badge (`🏆 Outstanding` or `✅ Strong Pass`) and the synthesized Remedial Study Topics.
