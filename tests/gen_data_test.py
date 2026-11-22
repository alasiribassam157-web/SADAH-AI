"""Tests for the generative brain's data pipeline (cleaning, leak guard, source registry). Offline, no PyTorch.

Run:  python -m tests.gen_data_test
"""
import json
import tempfile
import unittest
from pathlib import Path

from gpu import clean, data, sources

AR = "القاهرة هي عاصمة جمهورية مصر العربية وأكبر مدنها من حيث عدد السكان في المنطقة كلها"


class Cleaning(unittest.TestCase):
    def test_normalize_folds_forms_and_strips_marks(self):
        self.assertEqual(clean.normalize("مـــرحبـــا  ‏بك"), "مرحبا بك")
        self.assertEqual(clean.normalize("ﻻ"), "لا")
        self.assertEqual(clean.normalize("a\n\n\n\nb"), "a\n\nb")

    def test_quality_filters(self):
        self.assertTrue(clean.quality_ok(AR, min_arabic=0.8))
        self.assertFalse(clean.quality_ok("قصير"))
        self.assertFalse(clean.quality_ok("http://a.example/x " * 6))
        self.assertFalse(clean.quality_ok("hello world this is english text only " * 2, min_arabic=0.5))
        self.assertFalse(clean.quality_ok("نعم " * 40))

    def test_near_duplicates_are_dropped_but_different_text_is_kept(self):
        d = clean.Deduper()
        self.assertFalse(d.seen(AR))
        self.assertTrue(d.seen(AR + "."))
        self.assertFalse(d.seen("الرياض عاصمة المملكة العربية السعودية وفيها مقر الحكومة ومعظم الوزارات والهيئات"))

    def test_pipeline_counts_reasons(self):
        stats = {}
        out = list(clean.pipeline([AR, AR, "قصير", "x"], min_arabic=0.5, stats=stats))
        self.assertEqual(out, [AR])
        self.assertEqual(stats, {"kept": 1, "duplicate": 1, "quality": 2})


class LeakGuard(unittest.TestCase):
    def test_evaluation_question_inside_a_document_is_caught(self):
        g = clean.LeakGuard(["كم سعر الدولار اليوم مقابل الريال السعودي"])
        self.assertTrue(g.leaks("قال أحدهم: كم سعر الدولار اليوم مقابل الريال السعودي؟ ثم انصرف"))
        self.assertFalse(g.leaks(AR))

    def test_real_heldout_questions_never_reach_training_text(self):
        from gpu.data import leak_guard
        from tests.heldout_cases import HELDOUT
        guard = leak_guard()
        sample = [q for qs in HELDOUT.values() for q in qs if len(clean.words(q)) >= 4][:20]
        self.assertTrue(sample and all(guard.leaks(f"مقدمة {q} خاتمة") for q in sample))

    def test_local_pipeline_runs_and_drops_only_the_unclean(self):
        stats = {}
        docs = list(data.documents(True, stats))
        self.assertEqual(len(docs), stats.get("kept", 0))
        self.assertEqual(stats.get("leak", 0), 0, "the shipped KB must not contain evaluation questions")


class SourceRegistry(unittest.TestCase):
    def reg(self, **entries):
        p = Path(tempfile.mkdtemp()) / "s.json"
        p.write_text(json.dumps(entries), encoding="utf-8")
        return p

    def test_unreviewed_or_unknown_or_machine_written_sources_are_refused(self):
        p = self.reg(ok={"license": "x", "url": "", "human_written": True, "status": "approved"},
                     web={"license": "?", "url": "", "human_written": True, "status": "unreviewed"},
                     gen={"license": "x", "url": "", "human_written": False, "status": "approved"})
        self.assertEqual(list(sources.require(["ok"], p)), ["ok"])
        for name in ("web", "gen", "missing"):
            with self.assertRaises(sources.SourceError):
                sources.require([name], p)

    def test_shipped_registry_covers_what_the_pipeline_uses(self):
        for local in (True, False):
            self.assertTrue(sources.manifest(data.used_sources(local)))

    def test_unreviewed_web_crawl_is_not_approved_by_default(self):
        self.assertEqual(sources.load()["arabic-web-crawl"]["status"], "unreviewed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
