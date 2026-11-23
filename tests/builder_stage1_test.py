"""Builder tests, part 1: the landing page, the static checkers, honest questions/refusals, the zip.
Offline, no PyTorch.

Run:  python -m tests.builder_stage1_test
"""
import io
import unittest
import zipfile

from builder import checks, content
from builder.build import build, to_zip
from builder.landing import render
from builder.spec import Spec
from tests.builder_requests import SUITE

CAR_SHOWROOM = "أبغى موقع لمعرض سيارات باسم النخبة وفيه صفحة اتصال"


def asked(skill):
    return [c["q"] for c in SUITE if c["skill"] == skill]


class Landing(unittest.TestCase):
    def test_every_landing_request_in_the_suite_builds_and_passes_all_checks(self):
        for c in (c for c in SUITE if c["skill"] == "landing"):
            r = build(c["q"])
            self.assertTrue(r.ok, c["q"])
            self.assertEqual(checks.check_site(r.files), [], c["q"])
            self.assertEqual(r.spec.name, c["expect"]["name"], c["q"])

    def test_a_car_showroom_is_not_mistaken_for_a_photo_gallery(self):
        self.assertNotIn("gallery", build(CAR_SHOWROOM).spec.sections)

    def test_zip_holds_the_files_and_is_valid(self):
        r = build(CAR_SHOWROOM)
        z = zipfile.ZipFile(io.BytesIO(to_zip(r.files)))
        self.assertEqual(sorted(z.namelist()), ["index.html", "style.css"])
        self.assertIn("النخبة", z.read("index.html").decode("utf-8"))


class QuestionsAndRefusals(unittest.TestCase):
    def test_missing_name_asks_one_short_question_and_builds_nothing(self):
        for request in (q for q in asked("ask") if "لعبة" not in q):   # a game with no kind asks which game (builder_games_test)
            r = build(request)
            self.assertFalse(r.ok, request)
            self.assertEqual(r.question, "ما اسم المشروع؟", request)
            self.assertEqual(r.files, {})

    def test_unsupported_requests_are_refused_honestly(self):
        for request in asked("refuse"):
            r = build(request)
            self.assertFalse(r.ok, request)
            self.assertIn("غير مدعوم", r.message, request)
            self.assertEqual(r.files, {})


class Checkers(unittest.TestCase):
    def site(self):
        return render(Spec(name="تجربة", business="مطعم", sections=["about", "services", "contact"]))

    def test_good_site_passes(self):
        self.assertEqual(checks.check_site(self.site()), [])

    def test_each_defect_is_caught(self):
        good = self.site()["index.html"]
        defects = {
            "dir": good.replace(' dir="rtl"', ""),
            "title": good.replace("<title>تجربة</title>", "<title></title>"),
            "viewport": good.replace('<meta name="viewport"', '<meta name="x"'),
            "anchor": good.replace('href="#contact"', 'href="#nowhere"'),
            "unclosed": good.replace("</main>", ""),
            "handler": good.replace("<footer>", '<footer onclick="x()">'),
            "script": good.replace("</body>", "<script>1</script></body>"),
            "foreign script": good.replace("</body>", '<script src="x.js"></script></body>'),
            "external": good.replace('href="style.css"', 'href="https://evil.example/x.css"'),
            "second h1": good.replace("<main>", "<main><h1>ثانٍ</h1>"),
            "unlabelled input": good.replace("</main>", '<input id="q" type="text"></main>'),
        }
        for label, html in defects.items():
            self.assertTrue(checks.check_html(html), f"{label} was not caught")

    def test_css_defects_are_caught(self):
        self.assertTrue(checks.check_css("body{direction:rtl"))
        self.assertTrue(checks.check_css("body{color:red}"))

    def test_values_are_escaped_so_a_name_cannot_inject_markup(self):
        files = render(Spec(name='<script>alert(1)</script>"', business="مطعم"))
        self.assertNotIn("<script", files["index.html"])
        self.assertEqual(checks.check_site(files), [])

    def test_every_business_type_has_three_services_and_a_tagline(self):
        for words, (label, tagline, services) in content.BUSINESS.items():
            self.assertTrue(label and tagline and len(services) == 3, words)


if __name__ == "__main__":
    unittest.main(verbosity=2)
