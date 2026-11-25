---
name: verify-evidence-fixtures
description: Use after any change to examples/ (an evidence .txt file, a manifest, or a new fixture) and before committing or opening a PR. Checks that every evidence fixture is synthetic, names its order/lot/revision, and matches its declared SHA-256, then runs the tests and both demo outcomes.
---

# Verify evidence fixtures

The verifier only trusts evidence whose bytes match the manifest's SHA-256. A fixture edit without a matching hash
update breaks the demo, and re-hashing to hide an unintended edit defeats the point of the project. This
procedure keeps both honest.

## Inputs

- The repository root as the working directory.
- The base branch the work will merge into: the PR's base branch, or `main` if there is no PR. If you can't
  tell which branch that is, stop and ask.
- The ticket or PR that explains the fixture changes. If you can't say why a file changed, stop and ask the
  maintainer before continuing.

## Steps

1. **List every fixture change, committed or not.** Fetch the base first (`git fetch origin <base>`), then run
   both:
   - `git diff --stat origin/<base>...HEAD -- examples/` for changes already committed on this branch
   - `git status --short examples/` for changes not committed yet

   Write down each changed file and the ticket or reason for the change. An empty `git status` does **not** mean
   nothing changed: on a PR branch the fixture edits are usually already committed.
2. **Run the fixture check.**
   `python .claude/skills/verify-evidence-fixtures/scripts/check_fixtures.py examples`
   Expected: one `ok` line per evidence record and `All evidence fixtures ... check out.`, with exit code 0.
3. **If a hash differs:**
   - If the file is one you intentionally edited in step 1, update only that record's `sha256` in every manifest
     that declares it, using the `sha256=` value the script printed. Then rerun step 2.
   - If the file was **not** in your intended edits, **stop**. Report the file, the declared hash and the actual
     hash to the maintainer. Do not re-hash it.
4. **If a file is missing its `SYNTHETIC DEMO` header, or doesn't name the manifest's order, lot or revision,
   stop.** It may be real data or a mismatched fixture. Never add the header to a file you didn't write as
   synthetic data.
5. **Run the tests.** `python -m unittest discover -s tests -v`. Expected: every test passes.
6. **Run both demo outcomes and check the exit codes.**
   - `python passport.py examples/ready.json examples/evidence` must exit **0** with `"status": "ready_for_human_review"`.
   - `python passport.py examples/blocked.json examples/evidence` must exit **1** with `"status": "blocked"`.
   Any other exit code (2 means invalid input) is a failure. Report it and don't commit.

## Evidence to save

Paste into the PR description, or into the task report if there is no PR:

- The fixture changes from step 1 (both commands) and the reason for each.
- The full output of step 2, including the per-record hash lines.
- The test summary line from step 5 (`Ran N tests ... OK`).
- Both demo exit codes and statuses from step 6.

## When to stop and ask

- A changed fixture that you can't trace to the task.
- A hash mismatch on a file you didn't edit.
- A missing synthetic header, or a scope (order/lot/revision) that doesn't match.
- A manifest the script can't parse, or a demo exit code other than 0 (ready) or 1 (blocked).

Report what you found and leave the files as they are.
