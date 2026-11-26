"""My autopsy tool: open the window NovaBot sent to the model and measure what is in it.

Run it from the work folder:   uv run python labs/m1/autopsy.py
"""
import json
import re
from pathlib import Path

# ----- Step 1: open the window -----
WINDOW_FILE = Path("data/novatech/m1/autopsy_window.json")
window = json.loads(WINDOW_FILE.read_text(encoding="utf-8"))

parts = {}
for component in window["components"]:
    parts[component["component"]] = component

print("STEP 1: the request")
print("Asked by:", window["persona"])
print("Question:", parts["user_input"]["content"])
print("NovaBot answered:")
print(window["response"])

# ----- Step 2: where do the tokens go? -----
BUDGET = 12000
total = window["total_window_tokens"]

print()
print("STEP 2: tokens by component")
for name, component in parts.items():
    share = 100 * component["tokens"] / total
    print(f"{name:<18} {component['tokens']:>7} {share:5.1f}%")
print(f"{'total':<18} {total:>7}")
print(f"Budget {BUDGET}: the window is {total / BUDGET:.1f} times the budget")

# ----- Step 3: what rules was the model given? -----
print()
print("STEP 3: the system context, line by line")
for number, line in enumerate(parts["system"]["content"].splitlines(), start=1):
    print(number, line)

# ----- Step 4: what knowledge was retrieved? -----
print()
print("STEP 4: retrieved knowledge, in rank order")
for chunk in window["knowledge_chunks"]:
    print("---", chunk["chunk"])
    print(chunk["text"])

# ----- Step 5: what is in the conversation history? -----
history = parts["history"]["content"]
turns = re.findall(r"^\[(CONV-\S+) (\w+)\]$", history, flags=re.M)

print()
print("STEP 5: conversation history")
print("Turns:", len(turns))
print("History tokens:", parts["history"]["tokens"])
print("Full ticket dumps inside the history:", history.count('"ticket": {'))
print("First turn:")
print(history.split("\n\n")[0])

# ----- Step 6: which tools were on the desk? -----
tool_lines = parts["tool_definitions"]["content"].splitlines()

print()
print("STEP 6: tools and state")
print("Tools defined:", len(tool_lines))
for line in tool_lines:
    print("  ", line.split(":")[0])
for call in window["tool_calls_this_request"]:
    print("Tool called for this request:", call["tool"])
print("Tool result tokens:", parts["tool_results"]["tokens"])
print("Memory / state tokens:", parts["memory_state"]["tokens"])
