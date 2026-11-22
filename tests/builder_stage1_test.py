"""Stage-1 tests for the builder: the exit criterion (10/10 simple requests give a site that passes every check),
the checkers themselves, and honest refusals. Offline, no PyTorch.

Run:  python -m tests.builder_stage1_test
"""
import io
import unittest
import zipfile

from builder import checks, content
from builder.build import build, to_zip
from builder.landing import render
from builder.spec import Spec
from tests.builder_requests import NEEDS_NAME, SIMPLE, UNSUPPORTED


class ExitCriterion(unittest.TestCase):
    def test_every_simple_request_builds_a_site_that_passes_all_checks(self):
        failures = []
        for request, name, business, sections, accent in SIMPLE:
            r = build(request)
            ok = (r.ok and r.spec.name == name and r.spec.business == business
                  and all(s in r.spec.sections for s in sections)
                  and (accent is None or r.spec.accent == accent) and not checks.check_site(r.files))
            if not ok:
                failures.append((request, r.spec, r.problems, r.question))
        self.assertEqual(failures, [], f"{len(SIMPLE) - len(failures)}/{len(SIMPLE)} passed")

    def test_a_car_showroom_is_not_mistaken_for_a_photo_gallery(self):
        self.assertNotIn("gallery", build(SIMPLE[0][0]).spec.sections)
        self.assertIn("gallery", build(SIMPLE[5][0]).spec.sections)

    def test_missing_name_asks_one_short_question_and_builds_nothing(self):
        for request in NEEDS_NAME:
            r = build(request)
            self.assertFalse(r.ok)
            self.assertEqual(r.question, "ما اسم المشروع؟")
            self.assertEqual(r.files, {})

    def test_unsupported_kinds_are_refused_honestly(self):
        for request in UNSUPPORTED:
            r = build(request)
            self.assertFalse(r.ok)
            self.assertIn("غير مدعوم", r.message)
            self.assertEqual(r.files, {})

    def test_zip_holds_the_files_and_is_valid(self):
        r = build(SIMPLE[0][0])
        z = zipfile.ZipFile(io.BytesIO(to_zip(r.files)))
        self.assertEqual(sorted(z.namelist()), ["index.html", "style.css"])
        self.assertIn("النخبة", z.read("index.html").decode("utf-8"))


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
            "external": good.replace('href="style.css"', 'href="https://evil.example/x.css"'),
            "second h1": good.replace("<main>", "<main><h1>ثانٍ</h1>"),
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
