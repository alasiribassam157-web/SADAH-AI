"""Editing a built project: rules, spec validation (the spec comes back from the browser, so it is untrusted) and the
API functions. Offline, no PyTorch. The case suite is development data; held-out data is measured separately.

Run:  python -m tests.builder_edit_test
"""
import io
from dataclasses import replace
import unittest
import zipfile

from builder import api, edit, specio
from builder.build import build, render
from tests.builder_edit_case import check
from tests.builder_edit_heldout import HELDOUT_EDITS
from tests.builder_edit_suite import SUITE

BASE = build("موقع لمطعم باسم بيت الشواء")


class Rules(unittest.TestCase):
    def test_every_suite_case_passes(self):
        failed = [(i, found) for q, i, e in SUITE if (found := check(q, i, e))]
        self.assertEqual(failed, [])

    def test_the_heldout_set_is_well_formed_and_disjoint_from_the_suite(self):
        seen = {(q, i) for q, i, _ in SUITE}
        self.assertGreaterEqual(len(HELDOUT_EDITS), 15)
        self.assertEqual(len({(q, i) for q, i, _ in HELDOUT_EDITS}), len(HELDOUT_EDITS))
        self.assertFalse({(q, i) for q, i, _ in HELDOUT_EDITS} & seen)

    def test_an_edit_never_changes_the_original_spec(self):
        before = specio.to_dict(BASE.spec)
        edit.apply(BASE.spec, "غير اللون الى اخضر واضف قسم الاسعار واضف خدمة توصيل")
        self.assertEqual(specio.to_dict(BASE.spec), before)

    def test_edits_compose_and_every_step_still_builds(self):
        spec = BASE.spec
        for ins in ("غير اللون الى اخضر", "اضف قسم الاسعار", "اضف خدمة توصيل", "جوالي 0501234567", "شيل قسم من نحن"):
            done = edit.apply(spec, ins)
            self.assertTrue(done.changed, ins)
            self.assertTrue(render(done.spec).ok, ins)
            spec = done.spec
        self.assertEqual((spec.accent, spec.sections, spec.facts["phone"]),
                         ("#15803d", ["services", "pricing", "contact"], "0501234567"))
        self.assertIn("توصيل", spec.services)
        self.assertGreater(len(spec.services), 1)   # the added service joins the defaults, it does not replace them

    def test_the_contact_section_cannot_be_removed_and_unsupported_features_are_named(self):
        self.assertFalse(edit.apply(BASE.spec, "احذف قسم التواصل").changed)
        done = edit.apply(BASE.spec, "اضف بث مباشر")
        self.assertFalse(done.changed)
        self.assertIn("غير مدعوم", done.note)

    def test_an_item_name_is_a_label_not_a_feature_request(self):
        self.assertTrue(edit.apply(BASE.spec, "اضف خدمة حجز طاولات").changed)

    def test_an_edited_name_is_escaped_in_the_page(self):
        done = edit.apply(BASE.spec, "غير الاسم الى <b>x</b>")   # tags are not Arabic letters, so no name is taken
        self.assertFalse(done.changed)
        hostile = replace(BASE.spec, name="<script>alert(1)</script>")
        self.assertNotIn("<script>alert", render(hostile).files["index.html"])


class SpecInput(unittest.TestCase):
    def good(self):
        return specio.to_dict(BASE.spec)

    def test_a_round_trip_is_lossless(self):
        spec, bad = specio.check(self.good())
        self.assertEqual((bad, specio.to_dict(spec)), ([], self.good()))

    def test_malformed_or_hostile_specs_are_rejected_not_rendered(self):
        d = self.good()
        for patch in ({"accent": "#fff;}</style><script>"}, {"accent": "red"}, {"accent": "#12345g"}, {"kind": "nope"},
                      {"name": ""}, {"name": "x" * 500}, {"sections": ["about", 5]}, {"sections": ["admin", "contact"]},
                      {"services": ["a"] * 100}, {"data": [["a", "x"], ["b", 1]]}, {"data": [["a", True], ["b", 1]]},
                      {"items": [["a"]]}, {"facts": "phone"}, {"app": "x" * 100}):
            spec, bad = specio.check({**d, **patch})
            self.assertTrue(spec is None or bad, patch)
        for junk in (None, [], "x", 5):
            self.assertEqual(specio.check(junk)[0], None)

    def test_unknown_fact_keys_are_dropped(self):
        spec, _ = specio.check({**self.good(), "facts": {"phone": "0501234567", "script": "x"}})
        self.assertEqual(spec.facts, {"phone": "0501234567"})


class Api(unittest.TestCase):
    def test_build_returns_the_spec_and_edit_takes_it_back(self):
        r = api.respond("موقع لمطعم باسم بيت الشواء")
        self.assertTrue(r["ok"] and r["spec"]["name"] == "بيت الشواء")
        e = api.respond_edit(r["spec"], "غير اللون الى اخضر")
        self.assertTrue(e["ok"] and e["changed"])
        self.assertEqual(e["spec"]["accent"], "#15803d")
        self.assertIn("#15803d", e["files"]["style.css"])
        self.assertIn("<style>", e["preview"])

    def test_an_unchanged_edit_says_why_and_a_bad_spec_is_a_problem_not_a_crash(self):
        r = api.respond("موقع لمطعم باسم بيت الشواء")
        e = api.respond_edit(r["spec"], "ممكن تساعدني")
        self.assertTrue(e["ok"] and not e["changed"] and "ما فهمت" in e["note"])
        bad = api.respond_edit({"kind": "landing"}, "غير اللون الى اخضر")
        self.assertFalse(bad["ok"])
        self.assertTrue(bad["problems"])
        self.assertFalse(api.respond_edit("x", "غير اللون")["ok"])

    def test_the_zip_can_come_from_an_edited_spec(self):
        r = api.respond("موقع لمطعم باسم بيت الشواء")
        e = api.respond_edit(r["spec"], "غير اللون الى اخضر")
        z = zipfile.ZipFile(io.BytesIO(api.zip_of(spec_data=e["spec"])))
        self.assertIn("#15803d", z.read("style.css").decode())
        self.assertIsNone(api.zip_of(spec_data={"kind": "x"}))
        self.assertIsNone(api.zip_of(request="اصنع لي ذكاء"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
