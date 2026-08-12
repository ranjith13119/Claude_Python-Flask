---
description: Tests a Spendly feature. Usage: /test-feature <spec name> e.g. /test-feature 05-backend-connection
---

Run the full testing pipeline for the feature specified in $ARGUMENTS.

If no argument is provided, stop immediately and say:
"Please provide a spec name. Usage: /test-feature <spec-name> e.g. /test-feature 05-backend-connection"

If `.claude/specs/$ARGUMENTS.md` does not exist, stop immediately and say:
"Spec file not found at .claude/specs/$ARGUMENTS.md. Please check the spec name and try again."

---

## Step 1: Write Tests

Use the `task` tool to launch a **general** subagent with the following context:

- Spec file to base tests on: `.claude/specs/$ARGUMENTS.md`
- Source files to read for structure:
  - `app.py`
  - `database/` directory
- Output test file to create: `tests/test_$ARGUMENTS.py`
- Rule: Write tests based on what the spec says the feature SHOULD do. Do NOT derive test logic from reading the implementation. Cover happy paths, edge cases, auth guards, validation errors, and DB side effects.

Wait for the subagent to fully complete and confirm the test file has been written before proceeding to Step 2.

---

## Step 2: Run Tests

Once the test-writing subagent has finished, run:

```
python -m pytest tests/test_$ARGUMENTS.py -v
```

- Run ONLY the specified test file. Do NOT run the full test suite.
- Analyze any failures by cross-referencing the test code, the spec, and the source files (`app.py`, `database/`).
- Classify each failure as a bug or a missing feature.

---

## Handoff Rules

- Do NOT start Step 2 until Step 1 is fully complete
- Do NOT attempt to fix any code regardless of what the test results show
- Do NOT run any tests beyond `tests/test_$ARGUMENTS.py`
- If the test-writing subagent reports it could not write the test file, stop and report the reason — do NOT proceed to Step 2

---

## Final Output

After both steps complete, produce a combined summary:

### Testing Pipeline Report — $ARGUMENTS

**Step 1 — Tests Written**
- List each test written with a one-line description of which spec requirement it validates

**Step 2 — Test Results**
- Structured report of pass/fail per test

**Verdict**
One of:
- ✅ Ready for code review — all tests pass
- ❌ Needs fixes — list the failing tests and their root causes