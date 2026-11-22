"""Regression tests, part 1 (no weights needed): the gate's rules, the data split, the session ids, the file-size rule.

Run:  python -m tests.regression_gate_test      (offline, deterministic, no PyTorch)
"""
import json
import tempfile
import unittest
from pathlib import Path

from tests.regression_helpers import report

from agent import session_id
from core import dataset_builder as db
from core import evalsuite, gate

ROOT = Path(__file__).resolve().parent.parent
BASE = {"chat": (10, 10), "code": (9, 10), "units": (8, 10)}


class GateRules(unittest.TestCase):
    def verdict(self, skills, labels=None, base=BASE, cfg=None):
        return gate.compare(report(base), report(skills, labels or list(skills)), cfg)

    def test_identical_candidate_passes(self):
        self.assertTrue(self.verdict(BASE)["passed"])

    def test_skill_drop_beyond_limit_is_rejected(self):
        v = self.verdict({**BASE, "units": (6, 10)})   # -20 points on one skill
        self.assertFalse(v["passed"])
        self.assertIn("units", v["reasons"][0])

    def test_small_drop_inside_the_limit_passes(self):
        big = {"chat": (100, 100), "code": (100, 100), "units": (100, 100)}
        slip = {**big, "chat": (97, 100)}   # -3 points on one skill (allowed 5), -1% overall (allowed 1%)
        self.assertTrue(self.verdict(slip, base=big)["passed"])

    def test_overall_drop_is_rejected_even_when_each_skill_is_inside_its_limit(self):
        base = {f"s{i}": (100, 100) for i in range(5)}
        slip = {f"s{i}": (96, 100) for i in range(5)}   # each -4 points (allowed 5), overall -4 (allowed 1)
        v = self.verdict(slip, base=base)
        self.assertFalse(v["passed"])
        self.assertIn("overall", " ".join(v["reasons"]))

    def test_a_removed_skill_is_rejected(self):
        v = self.verdict({"chat": (10, 10), "code": (9, 10)}, base=BASE)
        self.assertFalse(v["passed"])
        self.assertIn("units", " ".join(v["reasons"]))

    def test_new_skill_needs_enough_accuracy_and_does_not_hide_regressions(self):
        ok = self.verdict({**BASE, "tafsir": (9, 10)})
        weak = self.verdict({**BASE, "tafsir": (5, 10)})
        hidden = self.verdict({**BASE, "units": (2, 10), "tafsir": (10, 10)})
        self.assertTrue(ok["passed"])
        self.assertFalse(weak["passed"])
        self.assertFalse(hidden["passed"])

    def test_regressions_and_fixes_are_listed_by_question(self):
        v = self.verdict({"chat": (10, 10), "code": (10, 10), "units": (8, 10)})
        self.assertEqual(len(v["fixes"]), 1)
        self.assertEqual(v["regressions"], [])

    def test_limits_come_from_the_config(self):
        strict = {"max_skill_drop": 0.0, "max_overall_drop": 0.0}
        self.assertFalse(self.verdict({**BASE, "code": (8, 10)}, cfg=strict)["passed"])
        self.assertTrue(self.verdict({**BASE, "code": (8, 10)}, cfg={"max_skill_drop": 0.2, "max_overall_drop": 0.2})["passed"])

    def test_gate_json_overrides_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "gate.json").write_text(json.dumps({"max_skill_drop": 0.2}))
            cfg = gate.load_config(Path(d))
        self.assertEqual((cfg["max_skill_drop"], cfg["max_overall_drop"]), (0.2, 0.01))


class DataAndRules(unittest.TestCase):
    def test_validation_never_contains_a_training_text(self):
        for brain in db.BRAINS:
            train, val = db.train_val_split(db.build_dataset(brain)[0])
            self.assertFalse({t for t, _ in train} & {t for t, _ in val}, brain)
            self.assertGreater(len(val), 1000)

    def test_gate_questions_are_not_in_the_generated_training_data(self):
        for brain, suite in (("router", "heldout"), ("coder", "coder_heldout")):
            texts = {evalsuite.normalize(t) for t, _ in db.build_dataset(brain)[0]}
            leaked = [q for q, _ in evalsuite.load_suites(brain)[suite] if evalsuite.normalize(q) in texts]
            self.assertEqual(leaked, [], f"{suite} questions leaked into training: {leaked[:3]}")

    def test_self_training_never_uses_a_gate_question(self):
        held = next(q for q, _ in evalsuite.load_suites("router")["heldout"])
        rows = [{"text": held + " ؟", "intent": "chat", "neural": "web", "ok": True},
                {"text": "سؤال جديد تماما", "intent": "chat", "neural": "web", "ok": True}]
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d, "q.jsonl")
            archive.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
            old, db.ARCHIVE = db.ARCHIVE, archive
            try:
                self.assertEqual([t for t, _, _ in db.load_auto_labels()], ["سؤال جديد تماما"])
            finally:
                db.ARCHIVE = old

    def test_session_ids(self):
        self.assertEqual(session_id.clean("3f2a9c1e-7b64-4d0a-9a1b-0c2d3e4f5a6b"), "3f2a9c1e-7b64-4d0a-9a1b-0c2d3e4f5a6b")
        for weak in ("", "1", "admin", "a" * 65, "id with spaces and symbols!!"):
            self.assertEqual(session_id.clean(weak), "")

    def test_every_python_file_stays_within_150_lines(self):
        long = [f"{p.relative_to(ROOT)} ({n})" for p in ROOT.rglob("*.py") if ".git" not in p.parts
                and (n := len(p.read_text(encoding="utf-8").splitlines())) > 150]
        self.assertEqual(long, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
