"""Publish to a link: the link carries the project, nothing is stored. Offline (the HTTP side is in app_test).

Run:  python -m tests.builder_share_test
"""
import base64
import json
import re
import unittest
import zlib
from pathlib import Path

from builder import checks, share, specio
from builder.build import build

UI = Path(__file__).resolve().parent.parent / "ui"


def token_of(request: str) -> str:
    return share.encode(specio.to_dict(build(request).spec))


class Tokens(unittest.TestCase):
    def test_a_project_round_trips_and_the_site_is_the_same_one(self):
        for q in ["متجر بثيم فخم باسم ليل وفيه شاي 20 وقهوة 30", "لعبة ثعبان باسم الافعى", "تطبيق ملاحظات باسم دفتري", "دعوة لحفل زفاف باسم نورة وفهد يوم الخميس"]:
            files = share.files_of(token_of(q))
            self.assertIsNotNone(files, q)
            plain = build(q).files
            self.assertEqual(sorted(files), sorted(plain), q)
            self.assertEqual(files["style.css"], plain["style.css"], q)
            self.assertEqual(checks.check_site(files), [], q)

    def test_a_token_is_short_and_url_safe(self):
        t = token_of("ابغى موقع لعيادة باسم نور وجوالي 0551234567")
        self.assertLess(len(t), 1000)
        self.assertRegex(t, r"^[A-Za-z0-9_-]+$")

    def test_every_shared_page_says_it_was_made_with_sadah(self):
        self.assertIn("صُنع بأداة", share.files_of(token_of("موقع لمطعم باسم السفرة"))["index.html"])

    def test_the_name_is_escaped_in_the_shared_page(self):
        data = specio.to_dict(build("موقع لمطعم باسم السفرة").spec)
        data["name"] = "<script>alert(1)</script>"
        self.assertNotIn("<script>alert", share.files_of(share.encode(data))["index.html"])


class Hostile(unittest.TestCase):
    def test_junk_oversize_and_bombs_are_refused(self):
        bomb = base64.urlsafe_b64encode(zlib.compress(b"a" * 10_000_000)).decode().rstrip("=")
        for t in ["", "abc", "A" * 7000, bomb, "!!!", "%%%%"]:
            self.assertIsNone(share.files_of(t), t[:20])

    def test_a_token_that_decodes_to_an_invalid_spec_is_refused(self):
        for spec in ({"kind": "landing", "name": "x", "accent": "red"}, {"kind": "game", "game": "chess", "name": "x", "accent": "#112233"},
                     {"kind": "landing", "name": "x", "accent": "#112233", "theme": "neon"}, [1, 2], "text"):
            t = base64.urlsafe_b64encode(zlib.compress(json.dumps(spec).encode())).decode().rstrip("=")
            self.assertIsNone(share.files_of(t), str(spec))

    def test_an_invalid_spec_is_not_shared(self):
        self.assertIsNone(share.encode({"kind": "x"}))
        self.assertIsNone(share.encode({**specio.to_dict(build("موقع لمطعم باسم السفرة").spec), "accent": "javascript:1"}))


class Ui(unittest.TestCase):
    def test_the_page_has_the_share_button_and_the_script_calls_the_endpoint_without_innerhtml(self):
        html, js = (UI / "index.html").read_text(encoding="utf-8"), (UI / "app.js").read_text(encoding="utf-8")
        for i in ("share", "sharebox", "sharelink", "copy"):
            self.assertIn(f'id="{i}"', html)
        self.assertIn("/api/share", js)
        self.assertNotIn("innerHTML", js)
        self.assertTrue(re.search(r'share\.disabled = true', js))


if __name__ == "__main__":
    unittest.main()
