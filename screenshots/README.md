# Evidence screenshots

Captures used in the hackathon Discussion posts. Each one is a real screen or real command output from this repository.

| File | What it shows |
| --- | --- |
| `pr2-qodo-review-resolved.jpg` | Qodo's review on PR #2 after the fix: the Medium finding "Stale inspections clear corrected lots", resolved by `cae05a1` |
| `pr2-ci-green.jpg` | GitHub Actions run for `cae05a1`: both matrix jobs passed |
| `pr2-demo-terminal.png` | Output of both demo runs and the test suite at `113b581`, rendered from the captured terminal text |
| `day01-lot-story.png` | Diagram of the synthetic lot in `examples/` going from blocked to ready for review. Drawn from the example manifests (IDs, times and statuses come from the files) |
| `day13-run1-steps1-2.png` | Tony's first fresh Claude Code session on `day13/fresh-session-check` at `2eae139`: step 1 reports no fixture edits (the gap this run exposed) and the fixture checker passes |
| `day13-run1-steps5-6.png` | Same run: 27 tests pass, `ready.json` exits 0 as `ready_for_human_review`, `blocked.json` reports its three blockers |
| `day13-local-verification-a5cbf4b.png` | Rendered command output (Linux) at `a5cbf4b`. The updated step 1 commands list the committed PR #4 fixture changes, and the checker, 27 tests and both demos pass. Supporting evidence, not the fresh-session run |
