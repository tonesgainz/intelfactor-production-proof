# IntelFactor Production Proof

An isolated Evidence Passport demonstration for a single synthetic production order and lot.

## Purpose and scope

This repository is a demonstration of evidence readiness, not a production quality-management or certification system. The proposed verifier checks that an order, lot and specification revision match declared evidence, and uses SHA-256 to detect changed fixture bytes. The intended result is either blocked or ready for human review; no automated acceptance, payment or shipment authorization is implied.

## Development and review

Implementation and verification are tracked in [PR #2](https://github.com/tonesgainz/intelfactor-production-proof/pull/2). Sampling-plan checks and a read-only fixture verification skill are separate proposals ([#4](https://github.com/tonesgainz/intelfactor-production-proof/pull/4), [#6](https://github.com/tonesgainz/intelfactor-production-proof/pull/6)). Consult the reviewed branch and its tests for exact commands; these proposals are not represented as merged features.

Use only synthetic fixtures in this public repository. Never commit real purchase orders, factory images, customer names, private documents or credentials. Verify matching and mismatched records, altered file hashes, failed checks and unresolved exceptions. Record the exact tested revision and expected outcomes. Any sampling-plan implementation requires independent validation against the applicable authorized standard and agreed inspection requirements; a passing demo is not certification.
