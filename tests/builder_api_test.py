"""Builder API tests: the JSON answer, the self-contained preview, the page and route wiring.
Offline, no FastAPI needed (the router is only built when the app runs).

Run:  python -m tests.builder_api_test
"""
import ast
import unittest
from pathlib import Path

from builder import checks
from builder.api import respond, preview
from tests.builder_requests import SUITE

ROOT = Path(__file__).resolve().parents[1]


def first(skill):
    return next(c["q"] for c in SUITE if c["skill"] == skill)


class Respond(unittest.TestCase):
    def test_a_built_site_returns_files_and_a_single_page_preview(self):
        for skill in ("landing", "dashboard", "shop", "webapp"):
            r = respond(first(skill))
            self.assertTrue(r["ok"], skill)
            self.assertEqual(r["kind"], skill)
            self.assertIn("index.html", r["files"])
            self.assertIn("<style>", r["preview"])
            self.assertNotIn('href="style.css"', r["preview"])
            self.assertNotIn('src="app.js"', r["preview"])

    def test_webapp_preview_carries_its_script_inline(self):
        r = respond(first("webapp"))
        self.assertIn("<script>", r["preview"])
        self.assertIn(r["files"]["app.js"], r["preview"])

    def test_question_and_refusal_have_no_files(self):
        ask = respond(first("ask"))
        self.assertEqual((ask["ok"], ask["question"], ask["files"], ask["preview"]), (False, "ما اسم المشروع؟", {}, ""))
        no = respond(first("refuse"))
        self.assertFalse(no["ok"])
        self.assertIn("غير مدعوم", no["message"])
        self.assertEqual(no["files"], {})

    def test_the_files_still_pass_every_check(self):
        self.assertEqual(checks.check_site(respond(first("shop"))["files"]), [])

    def test_a_very_long_request_is_cut_not_crashed(self):
        self.assertIn("ok", respond("ابغى موقع باسم نور " + "و" * 50000))

    def test_preview_leaves_a_page_without_app_js_untouched_by_script_rules(self):
        html = '<link rel="stylesheet" href="style.css">'
        self.assertEqual(preview({"index.html": html, "style.css": "a{}"}), "<style>a{}</style>")


class Wiring(unittest.TestCase):
    def test_app_registers_the_router_and_the_page(self):
        src = (ROOT / "app.py").read_text(encoding="utf-8")
        ast.parse(src)
        self.assertIn("builder_api.build_router()", src)
        self.assertIn('@app.get("/builder")', src)

    def test_the_page_is_rtl_arabic_sandboxed_and_loads_its_assets(self):
        html = (ROOT / "ui" / "builder.html").read_text(encoding="utf-8")
        self.assertIn('lang="ar" dir="rtl"', html)
        self.assertIn('sandbox="allow-scripts"', html)  # no same-origin: generated code cannot touch the app
        for asset in ("builder.js", "builder.css"):
            self.assertIn(asset, html)
            self.assertTrue((ROOT / "ui" / asset).is_file())

    def test_the_page_script_never_writes_server_text_as_html(self):
        js = (ROOT / "ui" / "builder.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", js)


if __name__ == "__main__":
    unittest.main(verbosity=2)
