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
