"""Builder tests, part 3: the portfolio / blog / event templates and the understanding rules added with them.
Offline, no PyTorch.

Run:  python -m tests.builder_stage3_test
"""
import unittest

from builder import checks
from builder.build import build
from builder.understand import understand
from tests.builder_requests import SUITE


def asked(skill):
    return [c["q"] for c in SUITE if c["skill"] == skill]


class NewTemplates(unittest.TestCase):
    def test_every_new_kind_in_the_suite_builds_a_site_that_passes_all_checks(self):
        for kind in ("portfolio", "blog", "event"):
            self.assertGreaterEqual(len(asked(kind)), 6, kind)
            for q in asked(kind):
                r = build(q)
                self.assertTrue(r.ok and r.spec.kind == kind, q)
                self.assertEqual(checks.check_site(r.files), [], q)
                self.assertEqual(sorted(r.files), ["index.html", "style.css"])

    def test_each_kind_has_its_own_sections_and_marks_unknown_text(self):
        expect = {"portfolio": ("skills", "projects"), "blog": ("posts",), "event": ("details", "program")}
        for kind, ids in expect.items():
            html = build(asked(kind)[0]).files["index.html"]
            for i in ids:
                self.assertIn(f'id="{i}"', html, kind)
            self.assertIn("(عدّل هذا النص)", html, kind)

    def test_names_are_escaped_in_the_new_templates(self):
        for word in ("مدونة", "بورتفوليو", "دعوة"):
            r = build(f"ابغى {word} باسم <script>x</script>")
            if r.ok:
                self.assertNotIn("<script>x", r.files["index.html"])


class Understanding(unittest.TestCase):
    def kind(self, text):
        return understand(text).spec.kind

    def test_a_registration_form_for_an_event_is_still_a_web_app(self):
        self.assertEqual(self.kind("نموذج تسجيل لحضور الفعالية باسم لقاء"), "webapp")

    def test_a_gallery_of_cars_is_not_a_portfolio_and_a_personal_site_stays_a_landing(self):
        self.assertEqual(self.kind("أبغى موقع لمعرض سيارات باسم النخبة"), "landing")
        self.assertEqual(self.kind("موقع شخصي لي باسم محمد العتيبي"), "landing")

    def test_a_year_after_a_name_word_belongs_to_the_name(self):
        self.assertEqual(understand("ابي دعوة لحفلة تخرج باسم تخرج 2026").spec.name, "تخرج 2026")

    def test_numbers_after_a_name_are_still_dashboard_data(self):
        spec = understand("لوحة بيانات باسم المبيعات يناير 100 فبراير 150").spec
        self.assertEqual((spec.name, [lbl for lbl, _ in spec.data]), ("المبيعات", ["يناير", "فبراير"]))

    def test_a_colour_word_can_be_the_name_but_still_ends_a_name(self):
        self.assertEqual(understand("موقع لمكتب تصميم باسم لون وفيه اسعار").spec.name, "لون")
        self.assertEqual(understand("موقع لمطعم اسمه البيت ولونه احمر").spec.name, "البيت")

    def test_missing_name_asks_and_unsupported_features_are_refused_for_new_kinds(self):
        for q in ("ابغى مدونة", "ابغى دعوة", "ابغى ملف شخصي"):
            self.assertEqual(build(q).question, "ما اسم المشروع؟", q)
        for q in ("ابغى مدونة فيها حجز مواعيد", "ابغى مدونة فيها تسجيل دخول", "ابغى موقع فعالية فيه حجز تذاكر"):
            self.assertIn("غير مدعوم", build(q).message, q)

    def test_a_refused_word_is_matched_as_a_whole_word_not_inside_another_word(self):
        self.assertTrue(build("ابغى دعوة لحفل تخرج باسم دفعة النور").ok)  # دفعة (a class) is not دفع (payment)
        for q in ("ابغى موقع للدفع", "ابغى موقع وفيه الدفع", "ابغى موقع مع الحجز"):
            self.assertIn("غير مدعوم", build(q).message, q)

    def test_the_refusal_message_lists_the_new_kinds(self):
        msg = build("ابغى تطبيق اندرويد باسم رحلة").message
        for word in ("ملف أعمال", "مدونة", "دعوة"):
            self.assertIn(word, msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
