"""Regression tests, part 2: the registry, the gate and rollback on the REAL router weights (NumPy, no PyTorch).

A candidate that is a byte copy of the stable brain must pass; a candidate really degraded (its currency output
switched off) must be rejected, can never be promoted, and must leave models/router.pt untouched.
Run:  python -m tests.regression_registry_test
"""
import shutil
import unittest
from pathlib import Path

from tests.regression_helpers import degrade, fresh_models

from core import evalsuite, lifecycle
from core.registry import PASSED, REJECTED, STABLE, Registry, RegistryError, sha256


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.dir = fresh_models()
        self.reg = Registry(self.dir)
        self.v1 = lifecycle.init("router", self.reg)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def good(self) -> int:
        return self.reg.add("router", self.reg.weights("router", self.v1), {"experiment": "copy"})

    def bad(self, label: str = "currency") -> int:
        path = degrade(self.reg.served("router"), self.dir / "bad.pt", label)
        return self.reg.add("router", path, {"experiment": f"break-{label}"}, move=True)

    def test_init_registers_the_served_weights_as_stable_v1(self):
        meta = self.reg.meta("router", self.v1)
        self.assertEqual((self.v1, self.reg.stable("router"), meta["status"]), (1, 1, STABLE))
        self.assertEqual(meta["sha256"], sha256(self.reg.served("router")))
        self.assertIn("heldout", meta["eval"]["suites"])
        self.assertEqual(lifecycle.init("router", self.reg), 1)   # idempotent

    def test_identical_candidate_passes_and_promotion_archives_the_old_stable(self):
        v2 = self.good()
        self.assertTrue(lifecycle.review("router", v2, self.reg)["passed"])
        lifecycle.promote("router", v2, self.reg)
        self.assertEqual((self.reg.stable("router"), self.reg.meta("router", 1)["status"]), (2, "archived"))
        self.assertTrue(self.reg.served_matches_stable("router"))

    def test_degraded_candidate_is_rejected_and_the_stable_brain_is_untouched(self):
        before, v2 = sha256(self.reg.served("router")), self.bad()
        verdict = lifecycle.review("router", v2, self.reg)
        self.assertFalse(verdict["passed"])
        self.assertIn("currency", " ".join(verdict["reasons"]))
        self.assertTrue(verdict["regressions"])
        self.assertEqual(self.reg.meta("router", v2)["status"], REJECTED)
        with self.assertRaises(RegistryError):
            lifecycle.promote("router", v2, self.reg)
        with self.assertRaises(RegistryError):
            self.reg.promote("router", v2)
        self.assertEqual((sha256(self.reg.served("router")), self.reg.stable("router")), (before, 1))

    def test_each_skill_is_protected_not_only_the_average(self):
        for label in ("prayer", "translate"):   # a different skill each time
            self.assertFalse(lifecycle.review("router", self.bad(label), self.reg)["passed"], label)

    def test_a_candidate_cannot_be_promoted_without_review(self):
        with self.assertRaises(RegistryError):
            self.reg.promote("router", self.good())

    def test_a_review_of_an_old_stable_is_stale(self):
        a, b = self.good(), self.good()
        lifecycle.review("router", a, self.reg), lifecycle.review("router", b, self.reg)
        lifecycle.promote("router", a, self.reg)
        with self.assertRaises(RegistryError):
            lifecycle.promote("router", b, self.reg)   # b was judged against v1, the stable one is now v2

    def test_rollback_restores_the_exact_previous_weights(self):
        v1_bytes = sha256(self.reg.served("router"))
        v2 = self.good()
        lifecycle.review("router", v2, self.reg), lifecycle.promote("router", v2, self.reg)
        self.assertEqual(self.reg.rollback("router"), 1)
        self.assertEqual((self.reg.stable("router"), sha256(self.reg.served("router"))), (1, v1_bytes))

    def test_rollback_refuses_rejected_versions_and_empty_history(self):
        with self.assertRaises(RegistryError):
            self.reg.rollback("router")
        bad = self.bad()
        lifecycle.review("router", bad, self.reg)
        with self.assertRaises(RegistryError):
            self.reg.rollback("router", bad)

    def test_corrupt_registry_weights_are_detected_before_install(self):
        v2 = self.good()
        lifecycle.review("router", v2, self.reg)
        with self.reg.weights("router", v2).open("ab") as f:
            f.write(b"corrupt")
        with self.assertRaises(RegistryError):
            lifecycle.promote("router", v2, self.reg)
        self.assertTrue(self.reg.served_matches_stable("router"))

    def test_silent_drift_of_the_served_file_blocks_review(self):
        v2 = self.good()
        with self.reg.served("router").open("ab") as f:
            f.write(b"x")
        with self.assertRaises(RegistryError):
            lifecycle.review("router", v2, self.reg)

    def test_evaluation_is_deterministic(self):
        a = evalsuite.evaluate("router", self.reg.served("router"))
        b = evalsuite.evaluate("router", self.reg.served("router"))
        self.assertEqual(a, b)

    def test_history_records_every_state_change(self):
        v2 = self.bad()
        lifecycle.review("router", v2, self.reg)
        events = (Path(self.reg.brain_dir("router")) / "history.jsonl").read_text().splitlines()
        self.assertGreaterEqual(len(events), 4)   # added v1, init, added v2, review
        self.assertEqual(self.reg.meta("router", v2)["status"], REJECTED)
        self.assertNotEqual(PASSED, REJECTED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
