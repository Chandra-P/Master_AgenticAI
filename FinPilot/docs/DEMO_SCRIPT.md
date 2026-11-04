# Presentation script

Use a fresh seeded database and deterministic mode for reproducibility. If demonstrating OpenAI, configure local keys, restart the API, and show the mode label. Never project the keys themselves.

1. **Problem:** “Most tools summarize the past. FinPilot tests a future decision against your actual evidence and constraints.”
2. **Dashboard:** show October income $10,000, expenses $6,000, surplus $4,000, cash $60,000. Point out the synthetic label and complete-month period.
3. **Proactive insight:** use the car-decision banner. Explain that this is an invitation to analyze, not a claim that the car is affordable.
4. **Transaction SQL:** in Copilot ask “Compare grocery spending in September versus October.” Show $800 → $900, $100, 12.50%. Open tool trace; no RAG was needed.
5. **Loan evidence:** ask “What APR is listed in my current auto-loan offer?” Show 6.49%, current version, and the 5% late-fee distractor in the passage. Previous APR is 7.49%.
6. **Primary scenario:** ask “Can I afford the $50,000 car in my current loan offer without dropping below my $25,000 emergency fund or substantially delaying my house goal?” Show three options. Higher down: $586.84 payment, house delay three months; lower down: $782.46, two months; postpone: zero delay.
7. **Evidence/calculations:** open calculation steps. Explain that the $20,000 house savings are already inside $60,000 cash. A $20,000 down payment consumes $5,000 earmarked for the house. Unknown ownership costs mean the result remains partial evidence.
8. **Agent/tool trace:** show document, SQL, structured memory, scenario, and validator events. Explain that these are concise execution records, not hidden reasoning.
9. **Evaluation Lab:** click Run evaluation suite. Wait for the real 59-case run, inspect SQL/RAG/SIM/SEC categories, expand a case to show independent expectations and actual evidence. Explain that this benchmark is synthetic and deterministic, not a live-model guarantee.
10. **Security:** open the Security test document. The $2,000 legitimate credit limit remains visible while the embedded instruction is quarantined. In Copilot, asking “Can I afford it?” without a referent abstains. Settings requires confirmation before changing a critical constraint.
11. **Close:** “FinPilot keeps the decision human, the math deterministic, and the evidence visible.”

Suggested contingency: if an external API fails, show the explicitly labeled deterministic fallback and retained local trace. If a document is missing or conflicting, demonstrate the abstention as a trust feature. Do not claim unknown insurance or tax costs are covered.


## Optional tax-planning chapter

Open Tax Planning after the dashboard. Show the two reviewed regular paystubs, and explain current versus YTD and the remaining paycheck counts. Show $14,020 projected federal tax against $11,882.40 withholding and a $2,137.60 estimated balance. Compare Alex adding $250 traditional 401(k) per check: $220 estimated income-tax reduction but $1,000 less immediate take-home across remaining checks. Compare $100 HSA per check: distinguish the $281.40 economic cost from $369.40 immediate cash reduction. Show the earmarked tax reserve and house goal, the official rule links, and explicit profile/paystub confirmation. In Evaluation Lab select TAX. Explain the supported scope and that withholding changes payment timing rather than tax liability.

### Optional council extension

Set `COUNCIL_MODE=demo` in `backend/.env` and restart the API. Ask the car-affordability question. Open the Model council panel: three explicitly simulated reviews flag constraint warnings and hold a blanket recommendation while preserving calculated alternatives. Inspect the `model_council` trace and deterministic validation. Explain that live mode requires `COUNCIL_MODE=openai` and three account-accessible models; agreement is not a confidence score. To present real votes, perform and verify a credentialed run beforehand. Never describe demo votes as live model opinions.
