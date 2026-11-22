"""Tests for core.geneval: the suite is scoreable, and the existing gate rejects a generator that bluffs.

Run:  python -m tests.geneval_test      (offline, no PyTorch)
"""
import unittest

from core import gate, geneval


def grounded(question, context):
    """Honest reference generator: answers from the context, abstains without it."""
    return context[0].rsplit(" هي ", 1)[1].rstrip(".") if context else "لا أعرف ذلك."


def bluffer(question, context):
    """Always confident, never grounded: the failure the gate exists to stop."""
    return "عاصمتها الرياض وعملتها الريال ولغتها الإنجليزية بلا شك."


class GenEval(unittest.TestCase):
    def test_suite_covers_every_skill_with_arabic_facts(self):
        cases = geneval.build_suite()
        self.assertEqual({c["skill"] for c in cases}, {"capital", "currency", "language", "abstain"})
        self.assertGreaterEqual(len(cases), 20)
        self.assertTrue(all(c["context"] and c["want"] in c["context"][0] for c in cases if c["want"]))

    def test_honest_generator_scores_perfectly(self):
        rep = geneval.evaluate(grounded)
        by = rep["suites"]["gen_facts"]["by_skill"]
        self.assertTrue(all(v["correct"] == v["total"] > 0 for v in by.values()), by)

    def test_bluffer_fails_abstention_and_support(self):
        by = geneval.evaluate(bluffer)["suites"]["gen_facts"]["by_skill"]
        self.assertEqual(by["abstain"]["correct"], 0)
        self.assertEqual(by["supported"]["correct"], 0)

    def test_gate_rejects_the_bluffer_and_passes_itself(self):
        base = geneval.evaluate(grounded)
        self.assertTrue(gate.compare(base, geneval.evaluate(grounded))["passed"])
        verdict = gate.compare(base, geneval.evaluate(bluffer))
        self.assertFalse(verdict["passed"])
        self.assertTrue(any("abstain" in r for r in verdict["reasons"]))

    def test_unsupported_share_and_abstention_markers(self):
        self.assertEqual(geneval.unsupported_share("القاهرة", ["عاصمة مصر هي القاهرة."]), 0.0)
        self.assertGreater(geneval.unsupported_share("القاهرة مدينة ساحرة جدا", ["عاصمة مصر هي القاهرة."]), 0.5)
        self.assertTrue(geneval.abstains("آسف، لا أعرف."))
        self.assertFalse(geneval.abstains("عاصمتها الرياض"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
