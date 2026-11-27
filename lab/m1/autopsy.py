import json

from pathlib import Path
WINDOW_FILE = Path("work/data/novatech/m1/autopsy_window.json")

window = json.loads(WINDOW_FILE.read_text(encoding="utf-8"))

parts = {}
for component in window["components"]:
    parts[component["component"]] = component

print()
print("STEP 1: USER QUESTION AND AI ANSWER")

question = parts["user_input"]["content"]
answer = window["response"]

print("\nUser Question:")
print(question)

print("\nAI Answer:")
print(answer)

BUDGET =12000
total = window["total_window_tokens"]
print()
print("STEP 2 : tokens by component")
for name, component in parts.items():
    share = 100 * component["tokens"] / total
    print(f"{name:<18} {component['tokens']:>7} {share:5.1f}%")

print(f"{'total':<18} {total:>7}")
print(f"Budget {BUDGET}: the window is {total / BUDGET:.1f} times the budget")

print()
print("STEP 3: the system context, line by line")

for number, line in enumerate(parts["system"]["content"].splitlines(), start = 1):
    print(number, line)

print()
print("STEP 4: KNOWLEDGE DOCUMENTS AND CHUNKS")

for chunk in window["knowledge_chunks"]:
    print()
    print("Document:", chunk["chunk"])
    print("Preview:", chunk["text"][:300])

print()
print("STEP 5: KEY TICKET EVIDENCE")

tool_text = parts["tool_results"]["content"]

keywords = ["customer_id", "product_version_id", "subject",
            "NovaSync 2.3", "hotfix", "Premium"]

for line in tool_text.splitlines():
    if any(word.lower() in line.lower() for word in keywords):
        print(line.strip())

print()
print("WORKAROUND IDENTIFIED")
print("Source: DOC-TRB-031")
print("1. Remove connector.legacy_profile block.")
print("2. Re-run connector validation.")
print("3. Restart the sync service.")

print()
print("STEP 6: INSPECT TOOL CALLS")

calls = window["tool_calls_this_request"]

for call in calls:
    print("Tool:", call["tool"])
    print("Arguments:", call["args"])

print()
print("STEP 7: AVAILABLE WINDOW KEYS")

print(window.keys())

print()
print("STEP 8: CHECK CUSTOMER HISTORY")

print("Total history turns:", window["history_turns"])

print()
print("STEP 9: CUSTOMER TIER EVIDENCE")

history_text = parts["history"]["content"]

for word in ["Premium", "Elite", "Standard"]:
    count = history_text.lower().count(word.lower())
    print(f"{word} mentioned: {count} times")

print()
print("Conclusion: Customer tier is not confirmed by these mentions.")

print()
print("FINAL EVIDENCE ANALYSIS")

print()
print("CLAIM 1: Orbital is a Premium customer")
print("Evidence: No verified customer tier found.")
print("Finding: Unsupported claim.")

print()
print("CLAIM 2: Orbital is entitled to a hotfix")
print("Evidence: DOC-FAQ-003 and DOC-POL-001.")
print("Finding: Conditional on customer tier and version eligibility.")

print()
print("CLAIM 3: Orbital is owed a 1-hour response")
print("Evidence: System instruction, line 3.")
print("Finding: One-hour response applies to Premium customers.")
print("Orbital's eligibility is unverified.")

print()
print("ADDITIONAL FINDING")
print("Ticket confirms NovaSync 2.3.0, not 2.2.")