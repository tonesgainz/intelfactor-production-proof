from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from passport import evaluate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class PassportTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((EXAMPLES / "ready.json").read_text(encoding="utf-8"))
        self.directory = EXAMPLES / "evidence"

    def test_valid_packet_waits_for_a_human(self):
        report = evaluate(self.manifest, self.directory)
        self.assertEqual(report["status"], "ready_for_human_review")
        self.assertEqual(report["blockers"], [])
        self.assertEqual(set(report["verified_evidence"]), {"E-INSPECT", "E-REWORK"})

    def test_blocked_demo_reports_missing_evidence_and_open_exception(self):
        manifest = json.loads((EXAMPLES / "blocked.json").read_text(encoding="utf-8"))
        report = evaluate(manifest, self.directory)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(len(report["blockers"]), 3)
        self.assertTrue(any("open" in reason for reason in report["blockers"]))

    def test_each_part_of_scope_must_match(self):
        for key in ("order", "lot", "revision"):
            with self.subTest(key=key):
                manifest = deepcopy(self.manifest)
                manifest["evidence"][0]["scope"][key] = "DIFFERENT"
                report = evaluate(manifest, self.directory)
                self.assertEqual(report["status"], "blocked")
                self.assertNotIn("E-INSPECT", report["verified_evidence"])

    def test_valid_hash_cannot_substitute_wrong_kind_or_requirement(self):
        for wrong_match in ("kind", "requirement"):
            with self.subTest(wrong_match=wrong_match):
                manifest = deepcopy(self.manifest)
                if wrong_match == "kind":
                    manifest["requirements"][0]["evidence"] = "E-REWORK"
                else:
                    manifest["requirements"].append(
                        {"id": "OTHER", "kind": "inspection", "result": "pass", "evidence": "E-INSPECT"}
                    )
                self.assertEqual(evaluate(manifest, self.directory)["status"], "blocked")

    def test_file_edits_and_missing_files_block_review(self):
        with TemporaryDirectory() as temp:
            directory = Path(temp)
            shutil.copy(self.directory / "E-REWORK.txt", directory)
            inspection = directory / "E-INSPECT.txt"
            for content, explanation in ((None, "regular evidence file"), ("changed", "SHA-256")):
                with self.subTest(content=content):
                    if content is not None:
                        inspection.write_text(content, encoding="utf-8")
                    report = evaluate(self.manifest, directory)
                    self.assertEqual(report["status"], "blocked")
                    self.assertTrue(any(explanation in reason for reason in report["blockers"]))

    def test_exception_needs_disposition_and_corrective_action(self):
        self.manifest["exceptions"][0].update(disposition=" ", evidence="E-INSPECT")
        report = evaluate(self.manifest, self.directory)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(len(report["blockers"]), 2)

    def test_reinspection_must_follow_the_corrective_action(self):
        # Qodo review finding on PR #2: an inspection that predates the rework must not clear it.
        for inspected_at in ("2026-11-23T09:05:00+08:00", "2026-11-23T09:10:00+08:00",
                             "2026-11-23T01:05:00+00:00"):
            with self.subTest(inspected_at=inspected_at):
                manifest = deepcopy(self.manifest)
                manifest["evidence"][0]["captured_at"] = inspected_at
                report = evaluate(manifest, self.directory)
                self.assertEqual(report["status"], "blocked")
                self.assertTrue(any("before the corrective action" in r for r in report["blockers"]))

    def test_reinspection_after_rework_in_another_time_zone_counts(self):
        self.manifest["evidence"][0]["captured_at"] = "2026-11-23T01:15:00+00:00"
        report = evaluate(self.manifest, self.directory)
        self.assertEqual(report["status"], "ready_for_human_review")

    def test_failed_requirement_blocks_despite_valid_evidence(self):
        self.manifest["requirements"][0]["result"] = "fail"
        report = evaluate(self.manifest, self.directory)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(len(report["blockers"]), 1)

    def test_timestamp_requires_timezone(self):
        self.manifest["evidence"][0]["captured_at"] = "2026-11-23T09:15:00"
        report = evaluate(self.manifest, self.directory)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("time zone" in reason for reason in report["blockers"]))

    def test_duplicate_ids_are_invalid(self):
        self.manifest["evidence"].append(self.manifest["evidence"][0])
        with self.assertRaisesRegex(ValueError, "duplicate evidence ID"):
            evaluate(self.manifest, self.directory)

    def test_manifest_digest_is_stable_and_tracks_changes(self):
        before = evaluate(self.manifest, self.directory)["manifest_sha256"]
        reordered = dict(reversed(list(self.manifest.items())))
        self.assertEqual(before, evaluate(reordered, self.directory)["manifest_sha256"])
        self.manifest["exceptions"][0]["disposition"] = "Updated"
        self.assertNotEqual(before, evaluate(self.manifest, self.directory)["manifest_sha256"])

    def test_cli_status_codes(self):
        with TemporaryDirectory() as temp:
            invalid = Path(temp) / "invalid.json"
            invalid.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            for manifest, status in (
                (EXAMPLES / "ready.json", 0),
                (EXAMPLES / "blocked.json", 1),
                (invalid, 2),
            ):
                with self.subTest(manifest=manifest):
                    result = subprocess.run(
                        [sys.executable, str(ROOT / "passport.py"), str(manifest), str(self.directory)],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, status)
                    if status == 2:
                        self.assertIn("duplicate JSON field", result.stderr)
                        self.assertEqual(result.stdout, "")
                    else:
                        self.assertIn("status", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
