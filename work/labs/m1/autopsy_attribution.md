# Lab A: context autopsy, failure attribution

Input: `data/novatech/m1/autopsy_transcript.md` (the window NovaBot sent for Priya's question about TCK-1042, and its answer).

One row per failure. Use **one** component per row, chosen from:
`system` · `user_input` · `history` · `knowledge` · `tools` · `memory_state` · `budget` (for cross-cutting problems).
Quote the evidence from the window in "double quotes" (or `backticks` for code and payloads). Describe what is
missing from the **design**, not what the model did wrong. Add as many rows as you find.

| # | Component | Evidence (quoted from the window) | What is missing in the design |
|---|---|---|---|
| 1 | System | “Premium customers get 1-hour responses.” | The system needs a rule to verify response-time commitments using the latest support policy instead of relying on fixed instructions. |
| 2 | Knowledge | FAQ says: “All Premium and Elite customers receive hotfixes for any supported version.” Policy says hotfixes are for the “current and previous minor version.” | A source-priority rule is missing. Official policy documents should take priority over general FAQ answers when their information conflicts. |
| 3 | Tools | "Available tools include customer_lookup and entitlement_check, but their results are not present in the context window." | A verification step should require checking the customer's account, product version, and active entitlements before giving a final answer. |
| 4 | History | "The history contains unrelated discussions about billing, conference arrangements, meeting rooms, and product roadmaps." | The system needs a history-filtering mechanism that keeps relevant ticket information and removes unrelated conversation details. |
| 5 | Memory State | "The transcript shows memory_state: 0 and “(empty)”. | A session-state mechanism is needed to retain important details such as the customer ID, ticket number, product version, and pending checks during the support conversation. |
| 6 | Budget | "History uses 23,827 tokens out of a total 31,687 tokens, while the allowed budget is 12,000 tokens." | A context-management rule is required to limit token usage by prioritising important information and removing repeated or irrelevant content. |

## Token table check (step 1)

- Largest component and its share of the window: History is the largest component, using 23,827 tokens, which is approximately 75.2% of the total 31,687 tokens.
- Is there a budget at all? What would it have been under the course's 12,000-token window? The course budget is 12,000 tokens. The actual context uses 31,687 tokens, exceeding the limit by 19,687 tokens.

## Pair compare (step 3)

- Disagreements and how you resolved them (which quoted evidence settled it): Knowledge and tool_results both contributed to the hotfix eligibility issue. The FAQ states that Premium customers receive hotfixes for any supported version, whereas the official policy restricts eligibility to the current and previous minor versions. Also, no customer entitlement-check result is available. The official policy is more specific and should be treated as authoritative.
- Where two components both seemed responsible, the one a design change would fix first: - Knowledge should be fixed first by introducing a source-priority rule. This prevents the assistant from relying on a general FAQ when an official policy provides stricter conditions.
- 

## Top three and fix first (step 4)

1. Introduce a source-priority rule so official policies override conflicting FAQ information.
2. Make customer lookup and entitlement verification compulsory before giving contract-related answers.
3. Reduce irrelevant conversation history and repeated tool results to stay within the token budget.

**Fix first:** (finding #, component, and why it changes the answer most)
Knowledge. Giving official policy documents priority over FAQs would directly correct the hotfix eligibility decision and reduce the chance of making an incorrect promise to the customer.
