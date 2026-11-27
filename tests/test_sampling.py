from copy import deepcopy
import json
from pathlib import Path
import unittest

from passport import evaluate
from sampling import check, code_letter, plan


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def ac_re(lot_size, aql):
    applied = plan(lot_size, aql)
    return applied["sample_size"], applied["accept"], applied["reject"]


class PlanTableTests(unittest.TestCase):
    def test_level_ii_code_letters_at_band_edges(self):
        cases = {2: "A", 8: "A", 9: "B", 90: "E", 91: "F", 1200: "J", 1201: "K",
                 3200: "K", 3201: "L", 500000: "P", 500001: "Q"}
        for lot_size, letter in cases.items():
            with self.subTest(lot_size=lot_size):
                self.assertEqual(code_letter(lot_size), letter)

    def test_published_plans(self):
        # (lot size, AQL) -> (n, Ac, Re), read straight from Table II-A without arrows.
        cases = {
            (2400, 2.5): (125, 7, 8),   # K
            (1000, 2.5): (80, 5, 6),    # J
            (120, 2.5): (20, 1, 2),     # F
            (1000, 6.5): (80, 10, 11),  # J
            (2400, 4.0): (125, 10, 11), # K
            (5000, 1.0): (200, 5, 6),   # L
            (20000, 0.65): (315, 5, 6), # M
            (20000, 2.5): (315, 14, 15),  # M
            (100000, 2.5): (500, 21, 22),  # N
        }
        for (lot_size, aql), expected in cases.items():
            with self.subTest(lot_size=lot_size, aql=aql):
                self.assertEqual(ac_re(lot_size, aql), expected)

    def test_arrows_change_the_sample_size(self):
        # AQL 2.5: B arrows down to C (n=5, 0/1); D arrows up to C; E arrows down to F (n=20, 1/2).
        self.assertEqual(ac_re(12, 2.5), (5, 0, 1))
        self.assertEqual(ac_re(40, 2.5), (5, 0, 1))
        self.assertEqual(ac_re(60, 2.5), (20, 1, 2))
        # AQL 2.5 below N (21/22) arrows up: a lot of 200,000 (P) uses n=500.
        self.assertEqual(ac_re(200000, 2.5), (500, 21, 22))
        self.assertEqual(plan(200000, 2.5)["plan_letter"], "N")

    def test_sample_larger_than_lot_means_full_inspection(self):
        # Lot of 4 (A) at AQL 2.5 arrows down to C, n=5 > lot: inspect all 4.
        applied = plan(4, 2.5)
        self.assertTrue(applied["full_inspection"])
        self.assertEqual(applied["sample_size"], 4)

    def test_unsupported_input_is_refused_not_guessed(self):
        for lot_size, aql in ((2400, 10.0), (2400, 0.4), (2400, True), (1, 2.5), (2400.0, 2.5)):
            with self.subTest(lot_size=lot_size, aql=aql):
                with self.assertRaises(ValueError):
                    plan(lot_size, aql)


class SamplingCheckTests(unittest.TestCase):
    def sampling(self, **changes):
        record = {"lot_size": 2400, "aql": 2.5, "inspected": 125, "nonconforming": 0}
        record.update(changes)
        return record

    def test_full_sample_within_ac_passes(self):
        applied, blockers = check(self.sampling(nonconforming=7), "pass")
        self.assertEqual(blockers, [])
        self.assertEqual(applied["code_letter"], "K")

    def test_undersized_sample_blocks(self):
        _, blockers = check(self.sampling(inspected=5), "pass")
        self.assertEqual(len(blockers), 1)
        self.assertIn("plan needs 125 units, 5 inspected", blockers[0])

    def test_pass_contradicting_ac_blocks(self):
        _, blockers = check(self.sampling(nonconforming=8), "pass")
        self.assertEqual(len(blockers), 1)
        self.assertIn("contradicts", blockers[0])

    def test_reaching_re_early_is_not_reported_as_incomplete(self):
        _, blockers = check(self.sampling(inspected=40, nonconforming=8), "fail")
        self.assertEqual(blockers, [])

    def test_malformed_sampling_is_invalid_input(self):
        bad = [
            {"lot_size": 2400, "aql": 2.5, "inspected": 125},
            self.sampling(extra=1),
            self.sampling(inspected=-1),
            self.sampling(nonconforming=3, inspected=2),
            self.sampling(inspected=2500),
            self.sampling(nonconforming=True),
        ]
        for record in bad:
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    check(record, "pass")


class PassportSamplingTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((EXAMPLES / "ready.json").read_text(encoding="utf-8"))
        self.directory = EXAMPLES / "evidence"

    def test_ready_example_reports_the_applied_plan(self):
        report = evaluate(self.manifest, self.directory)
        self.assertEqual(report["status"], "ready_for_human_review")
        applied = report["sampling_plans"]["LABEL-REVISION"]
        self.assertEqual((applied["sample_size"], applied["accept"], applied["reject"]), (125, 7, 8))

    def test_undersized_sample_blocks_the_packet(self):
        manifest = deepcopy(self.manifest)
        manifest["requirements"][0]["sampling"]["inspected"] = 5
        report = evaluate(manifest, self.directory)
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any("sample incomplete" in reason for reason in report["blockers"]))

    def test_requirement_without_sampling_behaves_as_before(self):
        manifest = deepcopy(self.manifest)
        del manifest["requirements"][0]["sampling"]
        report = evaluate(manifest, self.directory)
        self.assertEqual(report["status"], "ready_for_human_review")
        self.assertEqual(report["sampling_plans"], {})

    def test_unsupported_aql_is_invalid_input(self):
        manifest = deepcopy(self.manifest)
        manifest["requirements"][0]["sampling"]["aql"] = 10.0
        with self.assertRaisesRegex(ValueError, "LABEL-REVISION"):
            evaluate(manifest, self.directory)


if __name__ == "__main__":
    unittest.main()
