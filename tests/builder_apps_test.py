"""Builder apps: nine apps (tasks, register + calculator, counter, timer, expenses, notes, converter, habits), each a fixed reviewed
script that passes the static checks. Offline.

Run:  python -m tests.builder_apps_test
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from builder import checks, webapp
from builder.build import build
from builder.spec import APPS, Spec


def make(app: str, name: str = "تجربة") -> dict:
    return webapp.render(Spec(kind="webapp", name=name, app=app))


class Templates(unittest.TestCase):
    def test_every_app_passes_the_static_checks_with_three_files(self):
        for a in APPS:
            files = make(a)
            self.assertEqual(sorted(files), ["app.js", "index.html", "style.css"], a)
            self.assertEqual(checks.check_site(files), [], a)

    def test_every_app_script_is_valid_javascript(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        for a in APPS:
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "app.js"
                path.write_text(make(a)["app.js"], encoding="utf-8")
                done = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, f"{a}: {done.stderr}")

    def test_each_app_has_the_elements_its_script_looks_up_and_escapes_the_name(self):
        for a in APPS:
            files = make(a, "<script>alert(1)</script>")
            self.assertNotIn("<script>alert", files["index.html"])
            ids = {w.split('"')[0] for w in files["app.js"].split('getElementById("')[1:]}
            for i in ids:
                self.assertIn(f'id="{i}"', files["index.html"], f"{a}: #{i}")


class Requests(unittest.TestCase):
    def test_each_app_is_found_from_its_arabic_words(self):
        for q, app in [("ابغى حاسبة باسم حسابي", "calculator"), ("ابي عداد تسبيح باسم ذكر", "counter"), ("مؤقت بومودورو باسم تركيز", "timer"),
                       ("تطبيق مصروفات باسم جيبي", "expenses"), ("تطبيق ملاحظات باسم دفتري", "notes"),
                       ("محول وحدات باسم قياس", "converter"), ("تطبيق عادات باسم نمط", "habits"), ("تطبيق قائمة مهام باسم انجاز", "tasks")]:
            r = build(q)
            self.assertTrue(r.ok, q)
            self.assertEqual((r.spec.kind, r.spec.app), ("webapp", app), q)

    def test_a_bare_app_request_asks_which_app_and_a_bank_link_is_refused(self):
        self.assertIn("أي تطبيق", build("ابغى تطبيق").question)
        r = build("تطبيق مصروفات يربط حسابي البنكي")
        self.assertFalse(r.ok)
        self.assertFalse(r.files)


if __name__ == "__main__":
    unittest.main()
