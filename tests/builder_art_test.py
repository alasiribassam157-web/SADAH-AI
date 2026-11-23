"""Decorative SVG in the hero band: chosen by kind and theme, switchable, and never a way to smuggle markup in. Offline.

Run:  python -m tests.builder_art_test
"""
import re
import unittest

from builder import art, checks, edit, specio
from builder.build import build, render
from builder.spec import KINDS, THEMES, Spec


class Motifs(unittest.TestCase):
    def test_every_kind_and_theme_gets_a_valid_page_and_only_the_flat_theme_or_the_off_switch_has_none(self):
        for kind in KINDS:
            for theme in THEMES:
                spec = Spec(kind=kind, name="تجربة", theme=theme, app="notes" if kind == "webapp" else "tasks", game="snake")
                r = render(spec)
                self.assertEqual(checks.check_site(r.files), [], f"{kind} {theme}")
                has = '<svg class="art"' in r.files["index.html"]
                self.assertEqual(has, theme != "simple", f"{kind} {theme}")
                off = render(Spec(**{**spec.__dict__, "art": False}))
                self.assertNotIn("<svg", off.files["index.html"])

    def test_the_markup_is_inert_decoration(self):
        for name in art.MOTIFS:
            svg = art.MOTIFS[name]()
            self.assertNotRegex(svg, r"<script|on\w+=|href=|http")
        html = render(Spec(kind="landing", name="x")).files["index.html"]
        self.assertIn('aria-hidden="true"', html)
        self.assertEqual(len(re.findall(r"<h1", html)), 1)

    def test_luxe_uses_the_geometric_star_and_the_motif_follows_the_kind_otherwise(self):
        self.assertEqual(art.motif(Spec(kind="landing", theme="luxe")), "stars")
        self.assertEqual(art.motif(Spec(kind="landing")), "rings")
        self.assertEqual(art.motif(Spec(kind="shop")), "dots")


class Requests(unittest.TestCase):
    def test_the_request_and_the_edit_can_turn_it_off_and_on(self):
        self.assertFalse(build("موقع لمطعم باسم السفرة بدون زخارف").spec.art)
        self.assertTrue(build("موقع لمطعم باسم السفرة").spec.art)
        spec = build("موقع لمطعم باسم السفرة").spec
        off = edit.apply(spec, "شيل الزخارف")
        self.assertEqual((off.spec.art, off.note), (False, "أزلت الزخارف."))
        self.assertTrue(edit.apply(off.spec, "رجع الزخارف").spec.art)

    def test_the_flag_must_be_a_real_boolean_when_it_comes_from_the_browser(self):
        data = specio.to_dict(build("موقع لمطعم باسم السفرة").spec)
        self.assertEqual(specio.check({**data, "art": False})[1], [])
        self.assertTrue(specio.check({**data, "art": "no"})[1])
        self.assertTrue(specio.check({**data, "art": 0})[1])


if __name__ == "__main__":
    unittest.main()
