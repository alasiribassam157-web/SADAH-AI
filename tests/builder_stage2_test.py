"""Builder tests, part 2: dashboard / shop / web-app templates, the JavaScript checker, and the evaluation + gate.
Offline, no PyTorch.

Run:  python -m tests.builder_stage2_test
"""
import io
import unittest
import zipfile

from builder import checks
from builder.build import build, to_zip
from builder.evaluate import evaluate
from core import gate
from tests.builder_heldout import HELDOUT
from tests.builder_requests import SUITE


def req(skill, i=0):
    return [c["q"] for c in SUITE if c["skill"] == skill][i]


class Templates(unittest.TestCase):
    def test_dashboard_shows_the_given_numbers_and_marks_sample_data(self):
        r = build(req("dashboard"))
        html = r.files["index.html"]
        self.assertTrue(r.ok and "340" in html and "150" in html)  # total 100+150+90, a value
        sample = build("لوحة بيانات باسم الأداء")
        self.assertIn("بيانات تجريبية", sample.files["index.html"])

    def test_shop_lists_products_and_says_it_takes_no_payment(self):
        r = build("سوّ لي متجر باسم الورد وفيه ورد 20 وشموع 35 وعطر 120")
        self.assertIn("120 ريال", r.files["index.html"])
        self.assertIn("لا يوجد دفع", r.files["index.html"])

    def test_webapp_ships_app_js_and_passes_the_js_checks(self):
        for i in range(4):
            r = build(req("webapp", i))
            self.assertTrue(r.ok and "app.js" in r.files, req("webapp", i))
            z = zipfile.ZipFile(io.BytesIO(to_zip(r.files)))
            self.assertEqual(sorted(z.namelist()), ["app.js", "index.html", "style.css"])
            self.assertEqual(checks.check_site(r.files), [])

    def test_names_cannot_inject_markup_in_any_template(self):
        for q in ("لوحة بيانات باسم <b> فيها يناير 1 فبراير 2", "متجر باسم <i>"):
            r = build(q)
            if r.ok:
                self.assertNotIn("<b>", r.files["index.html"])
                self.assertNotIn("<i>", r.files["index.html"])


class JsChecker(unittest.TestCase):
    def test_banned_code_is_caught(self):
        for bad in ("eval('1')", "el.innerHTML = x", "fetch('/a')", "new Function('x')", "document.write(1)",
                    "var u = 'https://a.example'", "document.cookie"):
            self.assertTrue(checks.check_js(bad), bad)

    def test_unbalanced_brackets_are_caught(self):
        self.assertTrue(checks.check_js("function f( { }"))

    def test_the_templates_own_scripts_are_clean(self):
        from builder import webapp
        self.assertEqual(checks.check_js(webapp.TASKS_JS), [])
        self.assertEqual(checks.check_js(webapp.REGISTER_JS), [])

    def test_a_stray_file_or_mismatched_script_fails_the_site(self):
        files = build(req("webapp")).files
        self.assertTrue(checks.check_site({**files, "extra.php": "x"}))
        no_js = {k: v for k, v in files.items() if k != "app.js"}
        self.assertTrue(checks.check_site(no_js))


class EvaluationAndGate(unittest.TestCase):
    def test_development_suite_is_fully_passed(self):
        rep = evaluate()["suites"]["builder_requests"]
        failed = [c["q"] for c in rep["cases"] if not c["ok"]]
        self.assertEqual(failed, [])

    def test_heldout_set_meets_the_stage_threshold(self):
        rep = evaluate(suite=HELDOUT)["suites"]["builder_requests"]
        self.assertGreaterEqual(rep["correct"] / rep["total"], 0.8, [c["q"] for c in rep["cases"] if not c["ok"]])

    def test_gate_rejects_a_builder_that_forgets_a_kind_and_passes_itself(self):
        base = evaluate()
        self.assertTrue(gate.compare(base, evaluate())["passed"])

        def landing_only(request):
            r = build(request)
            if r.ok and r.spec.kind != "landing":
                r.ok, r.message, r.files = False, "غير مدعوم", {}
            return r

        verdict = gate.compare(base, evaluate(landing_only))
        self.assertFalse(verdict["passed"])
        self.assertTrue(any("dashboard" in x or "shop" in x or "webapp" in x for x in verdict["reasons"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
