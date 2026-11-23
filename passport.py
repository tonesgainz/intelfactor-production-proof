"""Verify and summarize evidence for a single purchase order, lot and revision."""

import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sys


IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")
DIGEST = re.compile(r"[a-f0-9]{64}")


def fields(value, names, label):
    if not isinstance(value, dict) or value.keys() != set(names.split()):
        raise ValueError(f"{label} must contain exactly these fields: {names}")


def identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a valid identifier")


def indexed(records, kind, names):
    if not isinstance(records, list):
        raise ValueError(f"{kind} records must be a list")
    result = {}
    for record in records:
        fields(record, f"id {names}", kind)
        identifier(record["id"], f"{kind} ID")
        key = record["id"]
        if key in result:
            raise ValueError(f"duplicate {kind} ID: {key}")
        result[key] = record
    return result


def verify_evidence(record, scope, requirements, directory):
    fields(record["scope"], "order lot revision", "evidence scope")
    if record["scope"] != scope:
        raise ValueError("order, lot or specification revision does not match")
    identifier(record["requirement"], "evidence requirement")
    if record["requirement"] not in requirements:
        raise ValueError("requirement does not exist")
    identifier(record["kind"], "evidence kind")
    timestamp = record["captured_at"]
    if not isinstance(timestamp, str) or "T" not in timestamp:
        raise ValueError("capture time must include a date and time zone")
    if datetime.fromisoformat(timestamp).utcoffset() is None:
        raise ValueError("capture time must include a time zone")
    expected = record["sha256"]
    if not isinstance(expected, str) or not DIGEST.fullmatch(expected):
        raise ValueError("declared SHA-256 is invalid")
    path = directory / f'{record["id"]}.txt'
    if path.is_symlink() or not path.is_file():
        raise ValueError("expected a regular evidence file")
    with path.open("rb") as source:
        actual = sha256()
        for chunk in iter(lambda: source.read(65536), b""):
            actual.update(chunk)
    if actual.hexdigest() != expected:
        raise ValueError("file SHA-256 differs from the manifest")


def evaluate(manifest, directory):
    fields(manifest, "schema_version scope requirements evidence exceptions", "manifest")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("unsupported manifest schema version")
    scope = manifest["scope"]
    fields(scope, "order lot revision", "scope")
    for key, value in scope.items():
        identifier(value, key)
    requirements = indexed(manifest["requirements"], "requirement", "kind result evidence")
    if not requirements:
        raise ValueError("at least one requirement is required")
    evidence = indexed(
        manifest["evidence"], "evidence", "scope requirement kind captured_at sha256"
    )
    exceptions = indexed(
        manifest["exceptions"], "exception", "requirement status disposition evidence"
    )

    verified = {}
    blockers = []
    for key, record in sorted(evidence.items()):
        try:
            verify_evidence(record, scope, requirements, directory)
        except (OSError, ValueError) as exc:
            blockers.append(f"Evidence {key}: {exc}")
        else:
            verified[key] = record

    def supports(reference, requirement, kind):
        if not isinstance(reference, str):
            return False
        record = verified.get(reference)
        return bool(record and record["requirement"] == requirement and record["kind"] == kind)

    for key, requirement in sorted(requirements.items()):
        identifier(requirement["kind"], "required evidence kind")
        if requirement["result"] not in ("pass", "fail", "pending"):
            raise ValueError(f"invalid result for requirement {key}")
        if requirement["result"] != "pass":
            blockers.append(f'Requirement {key}: recorded result is {requirement["result"]}')
        if not supports(requirement["evidence"], key, requirement["kind"]):
            blockers.append(f"Requirement {key}: matching evidence is missing or invalid")

    for key, exception in sorted(exceptions.items()):
        requirement = exception["requirement"]
        identifier(requirement, "exception requirement")
        if requirement not in requirements:
            raise ValueError(f"exception {key} references an unknown requirement")
        if exception["status"] == "open":
            blockers.append(f"Exception {key}: open against requirement {requirement}")
        elif exception["status"] == "resolved":
            note = exception["disposition"]
            if not isinstance(note, str) or not note.strip():
                blockers.append(f"Exception {key}: resolution needs a disposition")
            if not supports(exception["evidence"], requirement, "corrective-action"):
                blockers.append(f"Exception {key}: corrective-action evidence is missing or invalid")
        else:
            raise ValueError(f"invalid status for exception {key}")

    return {
        "schema_version": 1,
        "scope": scope,
        "status": "blocked" if blockers else "ready_for_human_review",
        "blockers": blockers,
        "requirements": requirements,
        "exceptions": exceptions,
        "verified_evidence": verified,
        "manifest_sha256": sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest(),
    }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("evidence_directory", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        report = evaluate(manifest, args.evidence_directory)
    except (OSError, ValueError) as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
