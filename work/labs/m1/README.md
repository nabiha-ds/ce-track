# Module 1 lab: the NovaBot autopsy, then your Context Spec v1

NovaBot, NovaTech's first support assistant, gave a support engineer a confident, wrong answer.
You find out why, then design the rules that stop it from happening in NovaAssist.

| Sitting | Time | You finish with |
|---|---|---|
| **Part 1** (steps 1 to 4) | 60 min | Your own autopsy tool and your first three findings |
| **Part 2** (steps 5 to 11) | 2 hours | Five findings, your Context Spec v1, two measured runs, one decision record |

**How every step works:** type the lines → run your file → answer the question → run the check.
Run every command from the `work` folder (`cd C:\ce\ce-track\work`; Mac: `cd ~/ce/ce-track/work`).
Every Python command starts with `uv run`.

| You need | Command |
|---|---|
| Run your file | `uv run python labs/m1/autopsy.py` |
| Check a step | `uv run python labs/m1/check_m1.py --step 2` |
| Fell behind? Copy the file as it is at the end of that step (replaces yours) | `copy labs\m1\catchup\step2.py labs\m1\autopsy.py` (step1 to step6) |

Mac: `cp labs/m1/catchup/step2.py labs/m1/autopsy.py`.

**Do not read the big file.** `data/novatech/m1/autopsy_transcript.md` is the full window NovaBot sent to the
model: about 1,300 lines. Nobody can read that in a session, and neither could the model. Your script reads it
for you, one component at a time.

Your findings go in `labs/m1/autopsy_attribution.md`: one row per finding, with **one** component, a **quote**
copied from your script's output, and what the **design** was missing (never "the model was wrong").

---

# Part 1 (60 minutes)

No starter file: you build `labs/m1/autopsy.py` from an empty file.

## Step 1. Open the window (10 min)

Create the file and save it: `code labs\m1\autopsy.py`. Type:

```python
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
```

Run it. You see who asked, the question, and NovaBot's answer.
**Read the answer once.** It makes three claims: a hotfix, a product version, a response time. Keep them in mind.

Check: `uv run python labs/m1/check_m1.py --step 1`

## Step 2. Where do the tokens go? (10 min)

Add at the end of your file:

```python
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
```

Run it. **Question:** which component takes most of the window? Did anything limit the size of this window?

**Finding 1 (we write this one together).** Open `labs/m1/autopsy_attribution.md` and fill row 1.
The component is `budget`. The evidence is a line you copy from your output, in "double quotes".

Check: `uv run python labs/m1/check_m1.py --step 2`

## Step 3. What rules was the model given? (10 min)

```python
# ----- Step 3: what rules was the model given? -----
print()
print("STEP 3: the system context, line by line")
for number, line in enumerate(parts["system"]["content"].splitlines(), start=1):
    print(number, line)
```

Run it. Six lines: this is everything NovaBot was told about how to behave.
**Questions:** Which line states a fact that can change next month? Compare that line with NovaBot's answer.
Is there any line about where an answer must come from, or what to do when two documents disagree?

**Finding 2:** component `system`. Quote the line. Say what rule is missing.

Check: `uv run python labs/m1/check_m1.py --step 3`

## Step 4. What knowledge was retrieved? (15 min)

```python
# ----- Step 4: what knowledge was retrieved? -----
print()
print("STEP 4: retrieved knowledge, in rank order")
for chunk in window["knowledge_chunks"]:
    print("---", chunk["chunk"])
    print(chunk["text"])
```

Run it. Two chunks reached the model. `DOC-FAQ-...` is a FAQ page; `DOC-POL-...` is a policy document.
**Questions:** Which one is ranked first? Do the two say the same thing about hotfixes? Which one did
NovaBot repeat (look at its "Source" line)? Which of the two should win when they disagree?

**Finding 3:** component `knowledge`. Quote the sentence NovaBot relied on. Say what the design was missing.

**Checkpoint for Part 1:** `uv run python labs/m1/check_m1.py --part 1`, then post the result in your pod channel.

Save your work:

```
git add labs/m1
git commit -m "M1 autopsy: first three findings"
```

---

# Part 2 (2 hours)

## Step 5. What is in the conversation history? (15 min)

```python
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
```

Run it. **Questions:** Which product version does the first turn say the customer is on? Which version did
NovaBot put in its answer? The same ticket was pasted into the history several times: what does that cost?

**Finding 4:** component `history`. Quote the first turn. Say what the design should have kept and dropped.

Check: `uv run python labs/m1/check_m1.py --step 5`

## Step 6. Which tools were on the desk? (15 min)

```python
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
```

Run it. **Questions:** The question was about what the customer is *entitled* to. Which tool would answer
that? Was it called? How many tools does this question need, and how many were defined? How large is the one
tool result? What did NovaBot remember about this customer (memory / state)?

**Finding 5:** component `tools`. (Stretch: a sixth finding for `memory_state` or `user_input`.)

Then fill "Top three and fix first" at the bottom of `autopsy_attribution.md`: with your pod, rank the findings
by how much fixing each one would change the answer.

Check: `uv run python labs/m1/check_m1.py --step 6`, then `git add labs/m1` and `git commit -m "M1 autopsy"`.

## Step 7. Start your Context Spec v1 (15 min)

The Context Spec is where you fix what you found: it sets a budget for every component.

```
copy context_spec\example_spec.yaml context_spec\spec_v1.yaml
code context_spec\spec_v1.yaml
```

Mac: `cp context_spec/example_spec.yaml context_spec/spec_v1.yaml`.

1. Set `spec_version: "1.0"`.
2. Find the `token_budget` of each component. They must add up to no more than `total_tokens - response_reserve`
   (the example uses 10,500 of 12,000).
3. Make **one** budget change that one of your findings supports (move tokens from one component to another),
   and note which finding it answers.

After every change, validate (the loader lists every problem at once):

```
uv run python -m novaassist.cli --spec context_spec/spec_v1.yaml --fake --once "hello"
```

Check: `uv run python labs/m1/check_m1.py --step 7`

## Step 8. Write the system context (25 min)

NovaBot's six lines were collected over time. Yours are designed. Open the four files in
`context_spec\system\v1\`; the comment at the top of each says what it must decide. Write at least three rules
in each (30 words or more).

| File | It answers |
|---|---|
| `role.md` | Who is served (P1 Priya, P2 Daniel, P3 Meera: see `data/novatech/stores/csv/personas.csv`), what the assistant is for, what it must never do |
| `grounding.md` | When to cite and how; what to say when the context does not contain the answer |
| `conflicts.md` | Which source wins when two disagree (your finding 3), and how the conflict is shown to the user |
| `tone.md` | Structure and length of an answer for each persona |

One rule for all four: **facts that change do not belong here** (your finding 2). They belong in sources.

Check: `uv run python labs/m1/check_m1.py --step 8`

## Step 9. Break it and read the trace (20 min)

Replay the same 22-turn conversation through NovaAssist, once with your spec and once with the example spec:

```
uv run python labs/m1/load_autopsy_history.py --session autopsy
uv run python labs/m1/run_probes.py --spec context_spec/spec_v1.yaml --session autopsy
uv run python labs/m1/run_probes.py --spec context_spec/example_spec.yaml --session autopsy
```

Each command asks three probe questions (P-1 to P-3, in `probes.yaml`), twice each, and writes a run report to
`labs/m1/runs/`. Then read the trace of one P-1 run; the file name is printed by `run_probes`:

```
uv run python labs/m1/trace_summary.py traces/<the P-1 trace file>.jsonl
```

Write down, for your spec and for the example spec: window tokens by channel, history turns kept and excluded
(and the reason), budget violations. NovaBot kept all 22 turns. How many does your spec keep?
**Look for `autopsy-T01`** in the list of excluded turns: that is the turn with the customer's product version
(your finding 4). Is it kept or excluded? Which turns are the largest, and what are they?

While your `.env` says `LLM_PROVIDER=fake`, the answers are placeholders, but **the token numbers and the
exclusions are real**: they come from your spec, not from the model.

Check: `uv run python labs/m1/check_m1.py --step 9`

**Stretch (needs a real model):** score each answer with the rubric R1 to R5 printed in the run report.
Answers vary between runs, so score the worse of the two.

## Step 10. Improve one thing and record the decision (20 min)

Make **one** change that your numbers justify (a budget, a priority, or a system rule). A good first candidate
is in the `history` component of your spec: `selection: {recent_turns: 6}` decides how many recent turns are
considered, and `token_budget` decides how many tokens they may use. Re-run only the probe it targets, for
example:

```
uv run python labs/m1/run_probes.py --spec context_spec/spec_v1.yaml --session autopsy --probe P-1
```

Then record the decision:

```
copy labs\m1\decision_record_template.md labs\m1\decision_records.md
```

Fill **D-M1-01** in three to six lines: the options you considered, your choice, the numbers before and after,
the risk you accept. (Stretch: D-M1-02, your source-authority rule, with the evidence from probe P-2.)

Check: `uv run python labs/m1/check_m1.py --step 10`

## Step 11. Save and finish (5 min)

```
git add context_spec labs/m1
git commit -m "M1: Context Spec v1"
uv run python labs/m1/check_m1.py --part 2
```

Post the result in your pod channel. Your Context Spec v1 stays with you for the whole track: every later
module amends it.

---

## Files in this folder

| File | What it is for |
|---|---|
| `autopsy.py` | **Yours**: the autopsy tool you build in steps 1 to 6 |
| `catchup/step1.py` to `step6.py` | The tool as it is at the end of each step |
| `autopsy_attribution.md` | Your findings table |
| `check_m1.py` | Checks a step (`--step`), a sitting (`--part`), or everything (no option). Structure only: it never judges whether a finding is "right" |
| `load_autopsy_history.py` | Replays the autopsy conversation (22 turns) into a NovaAssist session |
| `probes.yaml`, `policy_excerpts.md` | The three probes, the rubric, and the policy clauses supplied with probe P-2 |
| `run_probes.py` | Runs the probes with a spec you choose and writes a run report to `runs/` |
| `trace_summary.py` | Summarises a trace file: tokens by channel, kept / excluded items and why, violations |
| `decision_record_template.md` | Copy to `decision_records.md` in step 10 |

**Start again:** from the course folder, `uv run ce.py reset S01` restores the starting state and keeps a
backup of your current work.
