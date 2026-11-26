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
