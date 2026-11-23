"""Check every example manifest's evidence fixtures. Standard library only.

Usage: python .claude/skills/verify-evidence-fixtures/scripts/check_fixtures.py [examples_dir]

For each *.json manifest in the examples directory, and each evidence record it declares:
  - the file <evidence_dir>/<id>.txt exists and is a regular file
  - its first line starts with "SYNTHETIC DEMO"
  - it names the manifest's order, lot and revision
  - its SHA-256 matches the declared digest

Prints one line per record and every problem found. Exits 1 if there is any problem, else 0.
It never rewrites a file or a manifest.
"""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HEADER = "SYNTHETIC DEMO"
SCOPE_PARTS = ("order", "lot", "revision")


def names(text, value):
    """True if value appears as a whole token, not inside a longer identifier."""
    return re.search(rf"(?<![A-Za-z0-9_-]){re.escape(value)}(?![A-Za-z0-9_-])", text) is not None


def check_manifest(path, evidence_dir):
    problems, lines = [], []
    manifest = json.loads(path.read_text(encoding="utf-8"))
    scope = manifest.get("scope") if isinstance(manifest, dict) else None
    if not isinstance(scope, dict) or any(
        not isinstance(scope.get(part), str) or not scope.get(part).strip() for part in SCOPE_PARTS
    ):
        # Without a complete scope there is nothing to check the files against: fail, don't skip.
        problems.append(f"{path.name}: scope must give a non-empty order, lot and revision")
        return lines, problems
    for record in manifest.get("evidence", []):
        key = record.get("id", "?")
        file = evidence_dir / f"{key}.txt"
        if file.is_symlink() or not file.is_file():
            problems.append(f"{path.name} {key}: missing regular file {file}")
            continue
        data = file.read_bytes()
        actual = sha256(data).hexdigest()
        text = data.decode("utf-8", errors="replace")
        first = text.splitlines()[0] if text else ""
        status = "ok"
        if not first.startswith(HEADER):
            problems.append(f"{path.name} {key}: first line does not start with '{HEADER}'")
            status = "PROBLEM"
        if record.get("scope") != {part: scope[part] for part in SCOPE_PARTS}:
            problems.append(
                f"{path.name} {key}: record scope {record.get('scope')} differs from manifest scope"
            )
            status = "PROBLEM"
        for part in SCOPE_PARTS:
            if not names(text, scope[part]):
                problems.append(f"{path.name} {key}: file does not name {part} {scope[part]}")
                status = "PROBLEM"
        if actual != record.get("sha256"):
            problems.append(
                f"{path.name} {key}: declared {record.get('sha256')} but file is {actual}"
            )
            status = "PROBLEM"
        lines.append(f"{status:7} {path.name:14} {key:12} sha256={actual}")
    return lines, problems


def main(argv):
    examples = Path(argv[1]) if len(argv) > 1 else Path("examples")
    evidence_dir = examples / "evidence"
    manifests = sorted(examples.glob("*.json"))
    if not manifests:
        print(f"no manifests found in {examples}", file=sys.stderr)
        return 1
    all_problems = []
    for manifest in manifests:
        lines, problems = check_manifest(manifest, evidence_dir)
        print("\n".join(lines) if lines else f"--      {manifest.name:14} (no evidence records)")
        all_problems.extend(problems)
    if all_problems:
        print(f"\n{len(all_problems)} problem(s):", file=sys.stderr)
        for problem in all_problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"\nAll evidence fixtures in {len(manifests)} manifest(s) check out.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
