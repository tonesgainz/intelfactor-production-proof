# IntelFactor Production Proof

An Evidence Passport demo for one synthetic purchase order, production lot and specification revision. The demo follows a packaging-label mismatch from an open exception to a documented corrective action and reinspection. The verifier checks whether the packet is complete enough for a brand and factory reviewer to make an acceptance decision.

## Run the demo

Use Python 3.11 or newer from the repository root. The CLI and tests have no third-party dependencies.

```sh
python passport.py examples/blocked.json examples/evidence
python passport.py examples/ready.json examples/evidence
python -m unittest discover -s tests -v
```

| Exit | Result |
| --- | --- |
| 0 | `ready_for_human_review`. The report includes the accepted evidence records and manifest fingerprint. |
| 1 | `blocked`. The report lists the missing checks, invalid evidence or outstanding exceptions. |
| 2 | Invalid input. The error appears on stderr. |

Each example declares the order, lot and revision, the required checks and their reported outcomes, and the evidence and exception records. Evidence IDs correspond to `<id>.txt` files in the evidence directory. A record must match the packet scope, requirement and required evidence kind, carry a timestamp with a time zone, and match its declared SHA-256. An exception needs a recorded disposition and a verified corrective-action file before its resolution counts, and the requirement's passing evidence must be captured after that corrective action.

The verifier checks package consistency and file integrity. The source manifest supplies the requirements, results, timestamps and expected digests. A human reviewer still confirms the original specification, authenticity of the evidence, disposition and authority to accept or release the order. The demo has no signer identity, access control or production integrations.

## Software factory walkthrough

1. Turn the buyer problem into [a ticket with acceptance criteria](../../issues/1).
2. Use [AGENTS.md](AGENTS.md) to define the rules that guide implementation and review.
3. Run the test suite and both demo outcomes. GitHub Actions runs both on Python 3.11 and 3.13.
4. On the project pull request, use Qodo review to check evidence scope, fail-closed behavior and the human approval boundary. Apply or explain review findings, and rerun verification for any new commit.
5. A maintainer reviews the checks and Qodo's findings before approving a merge.

See [the workflow and submission checklist](docs/hackathon.md) for the review evidence needed.
