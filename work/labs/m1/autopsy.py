import json 

from pathlib import Path  
WINDOW_FILE = Path("data/novatech/m1/autopsy_window.json")

window = json.loads(WINDOW_FILE.read_text(encoding="utf-8")) 

parts = {} 
for component in window["components"]:               
    parts[component["component"]] = component         

BUDGET =12000
total = window["total_window_tokens"]
print()
print("STEP 2 : tokens by component")
for name, component in parts.items():
    share = 100 * component["tokens"] / total
    print(f"{name:<18} {component['tokens']:>7} {share:5.1f}%")
print(f"{"total":<18} {total:>7}")
print(f"Budget {BUDGET}: the window is {total / BUDGET:.1f} times the budget")

print()
print("STEP 3: the system context, line by line")

for number, line in enumerate(parts["system"]["content"].splitlines(), start = 1):
    print(number, line)