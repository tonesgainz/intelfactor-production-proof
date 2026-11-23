# IntelFactor Production Proof

The Python CLI checks document integrity and completeness for one synthetic order and lot. Run `python -m unittest discover -s tests -v` from the repository root.

1. Match every evidence record to the exact order, lot, specification revision and requirement.
2. Verify the file against the declared SHA-256 before counting it as evidence.
3. Fail closed for missing evidence, failed requirements and open exceptions. Require a disposition and supporting corrective-action evidence when an exception is resolved.
4. Reserve all shipment, payment and acceptance decisions for a human. Automation can mark a packet ready for review.
5. Use synthetic data in examples and test fixtures. Keep the verifier runnable offline with Python's standard library.

## Pull request quality gate

Check the ticket's acceptance criteria before changing code. Run the unit tests and both demo outcomes. Require a completed Qodo review of the current PR commit before merge. Investigate all findings, fix verified High and Medium findings and surface Low findings for the maintainer. Rerun tests and review after fixes. Escalate unresolved findings or stalled review to the maintainer.
