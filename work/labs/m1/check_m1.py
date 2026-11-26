"""M1 checks: is what the lab asks for in place? Structure only, never "correct" answers.

    uv run python labs/m1/check_m1.py --step 2     one step of the lab sheet (steps 1 to 11)
    uv run python labs/m1/check_m1.py --part 1     the first sitting (steps 1 to 4)
    uv run python labs/m1/check_m1.py --part 2     the weekend sitting (steps 5 to 11)
    uv run python labs/m1/check_m1.py              the full exit check below

Steps 1 to 6 run your labs/m1/autopsy.py and look for the facts it must print; the facts are read from the
window file itself. Steps 7 to 11 use the exit-check items below (step 9 also counts offline run reports;
step 10 needs D-M1-01 only).

The full exit check prints PASS/FAIL per item and exits non-zero if any item fails:
1. context_spec/spec_v1.yaml loads with the kit loader
2. its component budgets fit within total_tokens - response_reserve
3. the four system-context files are no longer the placeholders
4. labs/m1/autopsy_attribution.md has at least five findings, each with one valid component and quoted evidence
5. labs/m1/runs/ has a real-model run report for the example spec and for spec_v1
6. labs/m1/decision_records.md has both decision records, filled in
7. your M1 work (context_spec/, labs/m1/) is committed in Git
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT_ROOT))

from novaassist.spec import SpecError, load_spec  # noqa: E402

COMPONENTS = {"system", "user_input", "history", "knowledge", "tools", "memory_state", "budget"}
MIN_FINDINGS = 5
MIN_SYSTEM_WORDS = 30
MIN_RECORD_WORDS = 15
# sha256 of the starter placeholders (text stripped, LF line endings)
PLACEHOLDERS = {
    "role.md": "ade55407b380b1b7f9d9eef202a11ce2d2286b0794c921fac2cfbaf4ff096226",
    "grounding.md": "e6b4bcf74e45ea2f2914813dbfd9fa44d75732f01024c757e8aca945353de7ce",
    "conflicts.md": "79793bcc904c97afd98183c0114bd61c59bcf11e33943dbcbd51ef66ff18e552",
    "tone.md": "ba9a9ee3b2f6d365360b9043fb03fbe9deee8c06f2c823c0bd2ab804fcb38e4e",
}
QUOTE = re.compile(r'"[^"]*\w+\W+\w+\W+\w+[^"]*"|“[^”]*\w+\W+\w+\W+\w+[^”]*”|`[^`]+`')
COMMENT = re.compile(r"<!--.*?-->", re.S)
WINDOW_REL = Path("data") / "novatech" / "m1" / "autopsy_window.json"
BUDGET = 12000  # the course's simulated window, used in step 2
STEP_FINDINGS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}  # finding rows expected by the end of each autopsy step
PARTS = {1: range(1, 5), 2: range(5, 12)}
LAST_STEP = 11


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()


def _words(text: str) -> int:
    return len(re.findall(r"\w+", COMMENT.sub("", text)))


def check_spec(ws: Path) -> tuple[bool, str, object]:
    path = ws / "context_spec" / "spec_v1.yaml"
    if not path.is_file():
        return False, "context_spec/spec_v1.yaml not found (copy example_spec.yaml and amend it)", None
    try:
        spec = load_spec(path)
    except SpecError as exc:
        return False, str(exc), None
    return True, f"spec_v1.yaml loads (spec_version {spec.version})", spec


def check_budgets(spec) -> tuple[bool, str]:
    if spec is None:
        return False, "skipped: spec_v1.yaml does not load"
    total = 0
    for name, comp in spec.data["components"].items():
        tb = comp["token_budget"]
        total += sum(tb.values()) if isinstance(tb, dict) else tb
    available = spec.total_tokens - spec.response_reserve
    return total <= available, f"component budgets {total} of {available} available tokens"


def check_system_files(ws: Path, spec) -> tuple[bool, str]:
    files = spec.component("system").get("files", []) if spec is not None else \
        [f"system/v1/{name}" for name in PLACEHOLDERS]
    base = spec.path.parent if spec is not None else ws / "context_spec"
    problems = []
    for name in PLACEHOLDERS:
        rel = next((f for f in files if Path(f).name == name), None)
        if rel is None:
            problems.append(f"{name} is not listed in components.system.files")
            continue
        path = base / rel
        if not path.is_file():
            problems.append(f"{rel} not found")
            continue
        text = _text(path)
        if hashlib.sha256(text.encode("utf-8")).hexdigest() == PLACEHOLDERS[name]:
            problems.append(f"{rel} is still the placeholder")
        elif _words(text) < MIN_SYSTEM_WORDS:
            problems.append(f"{rel} has fewer than {MIN_SYSTEM_WORDS} words outside comments")
    return not problems, "; ".join(problems) or "all four system files designed"


def findings(path: Path) -> tuple[list[str], list[str]]:
    """Valid finding rows and the problems with the others."""
    valid, problems = [], []
    for line in _text(path).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.lstrip().startswith("|") or len(cells) < 4 or not cells[0].isdigit():
            continue
        if not any(cells[1:]):
            continue  # an empty template row
        component = cells[1].strip("`*").lower().replace(" ", "_").replace("/", "_")
        if component not in COMPONENTS:
            problems.append(f"row {cells[0]}: component {cells[1]!r} is not one of {sorted(COMPONENTS)}")
        elif not QUOTE.search(cells[2]):
            problems.append(f"row {cells[0]}: no quoted evidence")
        else:
            valid.append(cells[0])
    return valid, problems


def check_attribution(ws: Path) -> tuple[bool, str]:
    path = ws / "labs" / "m1" / "autopsy_attribution.md"
    if not path.is_file():
        return False, "labs/m1/autopsy_attribution.md not found"
    valid, problems = findings(path)
    ok = len(valid) >= MIN_FINDINGS
    msg = f"{len(valid)} findings with a valid component and quoted evidence (need {MIN_FINDINGS})"
    return ok, msg + (f"; {'; '.join(problems)}" if problems else "")


def check_runs(ws: Path, allow_fake: bool) -> tuple[bool, str]:
    runs = ws / "labs" / "m1" / "runs"
    missing = []
    for stem in ("example_spec", "spec_v1"):
        reports = sorted(runs.glob(f"{stem}_*.md")) if runs.is_dir() else []
        if not allow_fake:
            reports = [r for r in reports if "(fake client" not in r.read_text(encoding="utf-8")]
        if not reports:
            missing.append(stem)
    if missing:
        hint = "" if allow_fake else " (fake-client reports do not count: run without --fake)"
        return False, f"no run report for {', '.join(missing)} in labs/m1/runs/{hint}"
    return True, "run reports present for example_spec and spec_v1"


def check_decisions(ws: Path, records: tuple[str, ...] = ("D-M1-01", "D-M1-02")) -> tuple[bool, str]:
    path = ws / "labs" / "m1" / "decision_records.md"
    if not path.is_file():
        return False, "labs/m1/decision_records.md not found (copy decision_record_template.md)"
    text = _text(path)
    template = _text(Path(__file__).resolve().parent / "decision_record_template.md")
    template_words = set(re.findall(r"\w+", template.lower()))
    problems = []
    for record in records:
        match = re.search(rf"^##\s*{record}\b(.*?)(?=^##\s|\Z)", text, re.M | re.S)
        if not match:
            problems.append(f"{record} section missing")
            continue
        own = [w for w in re.findall(r"\w+", COMMENT.sub("", match.group(1)).lower()) if w not in template_words]
        if len(own) < MIN_RECORD_WORDS:
            problems.append(f"{record} is not filled in")
    return not problems, "; ".join(problems) or f"{' and '.join(records)} filled in"


def check_git(ws: Path) -> tuple[bool, str]:
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--", "context_spec", "labs/m1"], cwd=ws,
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"git not available: {exc}"
    if out.returncode != 0:
        if "not a git repository" in out.stderr:
            return False, "this workspace is not a Git repository - ask the trainer (or run git init once)"
        return False, f"git status failed: {out.stderr.strip()}"
    pending = [ln for ln in out.stdout.splitlines() if ln.strip()]
    if pending:
        return False, f"{len(pending)} uncommitted change(s) under context_spec/ or labs/m1/ - run git add and git commit"
    return True, "M1 work committed"


def run_checks(ws: Path, allow_fake: bool = False) -> list[tuple[str, bool, str]]:
    ok, msg, spec = check_spec(ws)
    results = [("1 spec_v1 loads", ok, msg)]
    results.append(("2 budgets fit", *check_budgets(spec)))
    results.append(("3 system files designed", *check_system_files(ws, spec)))
    results.append(("4 autopsy attribution", *check_attribution(ws)))
    results.append(("5 run reports", *check_runs(ws, allow_fake)))
    results.append(("6 decision records", *check_decisions(ws)))
    results.append(("7 committed", *check_git(ws)))
    return results


# --- step checks (the lab sheet's steps 1 to 11) ------------------------------------------------------------------

def _flat(text: str) -> str:
    """Lower case, no thousands separators, single spaces: so small formatting differences do not matter."""
    return " ".join(text.replace(",", "").lower().split())


def run_autopsy(ws: Path) -> tuple[str | None, str]:
    """Run the participant's labs/m1/autopsy.py from the workspace; (output, "") or (None, what went wrong)."""
    script = ws / "labs" / "m1" / "autopsy.py"
    if not script.is_file():
        return None, "labs/m1/autopsy.py not found (create it, or copy a catch-up file from labs/m1/catchup/)"
    try:
        done = subprocess.run([sys.executable, str(script)], cwd=ws, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60,
                              env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"could not run autopsy.py: {exc}"
    if done.returncode != 0:
        last = (done.stderr.strip().splitlines() or ["no error message"])[-1]
        return None, f"autopsy.py stops with an error: {last}"
    return done.stdout, ""


def expected_facts(step: int, window: dict) -> list[tuple[str, str]]:
    """(what it is, text that must appear in the output) for an autopsy step, read from the window itself."""
    parts = {c["component"]: c for c in window["components"]}
    total = window["total_window_tokens"]
    if step == 1:
        return [("the question", parts["user_input"]["content"]),
                ("NovaBot's answer", window["response"].splitlines()[0])]
    if step == 2:
        facts = [(f"tokens for {name}", str(c["tokens"])) for name, c in parts.items() if c["tokens"]]
        return facts + [("the total", str(total)), ("how many times the budget", f"{total / BUDGET:.1f} times")]
    if step == 3:
        lines = [ln for ln in parts["system"]["content"].splitlines() if ln.strip()]
        return [(f"system line {i}", ln) for i, ln in enumerate(lines, start=1)]
    if step == 4:
        return [(f"knowledge chunk {i}", k["chunk"]) for i, k in enumerate(window["knowledge_chunks"], start=1)]
    if step == 5:
        history = parts["history"]["content"]
        return [("the number of turns", f"turns: {window['history_turns']}"),
                ("the history tokens", str(parts["history"]["tokens"])),
                ("the first turn", history.split("\n\n")[0])]
    tools = [ln.split(":")[0].lstrip("- ") for ln in parts["tool_definitions"]["content"].splitlines()]
    return ([(f"tool {name}", name) for name in tools]
            + [("the tool called", f"request: {c['tool']}") for c in window["tool_calls_this_request"]])


def check_autopsy_step(ws: Path, step: int) -> list[tuple[str, bool, str]]:
    window_path = ws / WINDOW_REL
    if not window_path.is_file():
        return [(f"step {step} output", False, f"{WINDOW_REL.as_posix()} not found: run this from the work folder")]
    output, problem = run_autopsy(ws)
    if output is None:
        return [(f"step {step} output", False, problem)]
    flat = _flat(output)
    missing = [what for what, text in expected_facts(step, json.loads(window_path.read_text(encoding="utf-8")))
               if _flat(text) not in flat]
    results = [(f"step {step} output", not missing,
                f"your script does not print: {', '.join(missing)}" if missing else "your script prints what this step needs")]
    if step in STEP_FINDINGS:
        need = STEP_FINDINGS[step]
        path = ws / "labs" / "m1" / "autopsy_attribution.md"
        valid, problems = findings(path) if path.is_file() else ([], ["labs/m1/autopsy_attribution.md not found"])
        msg = f"{len(valid)} finding row(s) with a component and quoted evidence (need {need} by now)"
        results.append((f"step {step} findings", len(valid) >= need, msg + (f"; {'; '.join(problems)}" if problems else "")))
    return results


def check_step(ws: Path, step: int) -> list[tuple[str, bool, str]]:
    """The checks for one step of the lab sheet."""
    if step <= 6:
        return check_autopsy_step(ws, step)
    if step == 7:
        ok, msg, spec = check_spec(ws)
        return [("step 7 spec_v1 loads", ok, msg), ("step 7 budgets fit", *check_budgets(spec))]
    if step == 8:
        return [("step 8 system files", *check_system_files(ws, check_spec(ws)[2]))]
    if step == 9:
        return [("step 9 run reports", *check_runs(ws, allow_fake=True))]
    if step == 10:
        return [("step 10 decision record", *check_decisions(ws, ("D-M1-01",)))]
    return [("step 11 committed", *check_git(ws))]


def report_steps(ws: Path, steps: list[int]) -> int:
    failed_steps, script_behind = [], []
    for step in steps:
        for name, ok, msg in check_step(ws, step):
            print(f"{'PASS' if ok else 'FAIL'}  {name:<24} {msg}")
            if not ok and step not in failed_steps:
                failed_steps.append(step)
            if not ok and name.endswith("output"):
                script_behind.append(step)
    if not failed_steps:
        print(f"\nPASS. {'Go on to the next step.' if steps[-1] < LAST_STEP else 'Module 1 lab complete.'}")
        return 0
    print(f"\nNot yet: step {', '.join(map(str, failed_steps))}. Read the step again in labs/m1/README.md.")
    if script_behind:
        first = script_behind[0]
        print(f"Fell behind? Copy the file as it is at the end of step {first} (replaces yours): "
              f"labs/m1/catchup/step{first}.py -> labs/m1/autopsy.py")
    else:
        print("Your script is fine. What is missing is written above (a finding row, a file, or a commit).")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M1 checks: one step, one sitting, or the full exit check.")
    parser.add_argument("--workspace", type=Path, default=KIT_ROOT)
    parser.add_argument("--allow-fake", action="store_true", help="count fake-client run reports (offline dry runs)")
    parser.add_argument("--step", type=int, choices=range(1, LAST_STEP + 1), metavar="N", help="check one step (1-11)")
    parser.add_argument("--part", type=int, choices=sorted(PARTS), help="check a whole sitting (1 or 2)")
    args = parser.parse_args(argv)
    if args.step or args.part:
        return report_steps(args.workspace, [args.step] if args.step else list(PARTS[args.part]))
    results = run_checks(args.workspace, args.allow_fake)
    for name, ok, msg in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<26} {msg}")
    failed = sum(not ok for _, ok, _ in results)
    print(f"\n{'M1 exit check PASS' if not failed else f'M1 exit check FAIL ({failed} item(s))'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
