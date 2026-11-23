"""Themes: five looks, chosen from the request or an edit, readable in every accent colour. Offline.

Run:  python -m tests.builder_themes_test
"""
import re
import unittest

from builder import checks, edit, themes, themeword
from builder.build import build, render
from builder.spec import COLORS, THEMES, Spec, problems
from builder import specio, theme


class Contrast(unittest.TestCase):
    ACCENTS = [*COLORS.values(), themes.LUXE_GOLD]

    def test_text_on_the_accent_and_the_accent_as_text_reach_4_5_to_1_in_every_theme(self):
        for accent in self.ACCENTS:
            self.assertGreaterEqual(themes.contrast(themes.on(accent), accent), 4.5, accent)
            for name, pal in themes.PALETTE.items():
                self.assertGreaterEqual(themes.contrast(themes.text(accent, pal["bg"]), pal["bg"]), 4.5, f"{accent} {name}")

    def test_every_palette_reads(self):
        for name, p in themes.PALETTE.items():
            for fg in ("ink", "muted"):
                for bg in ("bg", "soft", "card"):
                    self.assertGreaterEqual(themes.contrast(p[fg], p[bg]), 4.5, f"{name} {fg} on {bg}")

    def test_the_default_theme_keeps_the_light_values_that_were_already_shipped_readable(self):
        self.assertGreaterEqual(themes.contrast("#6b7280", "#ffffff"), 4.5)


class Sites(unittest.TestCase):
    def test_every_kind_in_every_theme_passes_the_static_checks(self):
        for t in THEMES:
            for kind, extra in (("landing", {}), ("shop", {"items": [("شاي", "20 ريال")]}), ("dashboard", {"data": [("أ", 1.0), ("ب", 2.0)]}),
                                ("webapp", {"app": "notes"}), ("game", {"game": "snake"}), ("portfolio", {}), ("blog", {}), ("event", {})):
                r = render(Spec(kind=kind, name="تجربة", theme=t, **extra))
                self.assertEqual(r.problems, [], f"{kind} {t}")
                self.assertEqual(checks.check_site(r.files), [], f"{kind} {t}")

    def test_each_theme_writes_its_own_css(self):
        css = {t: theme.css("#1d4ed8", t) for t in THEMES}
        self.assertEqual(len(set(css.values())), len(THEMES))
        self.assertIn("border-bottom:2px solid var(--accent)", css["luxe"])
        self.assertIn(".hero{background:var(--bg)", css["simple"])

    def test_an_unknown_theme_is_a_problem_and_is_rejected_from_the_browser(self):
        self.assertTrue(problems(Spec(kind="landing", name="x", theme="neon")))
        _, bad = specio.check({**specio.to_dict(Spec(kind="landing", name="x")), "theme": "x" * 40})
        self.assertTrue(bad)


class Requests(unittest.TestCase):
    def test_the_look_comes_from_the_request(self):
        for q, want in [("موقع فخم لمطعم باسم السفرة", "luxe"), ("متجر بثيم داكن باسم ليل", "dark"), ("موقع مينيمال لعيادة باسم سكون", "simple"),
                        ("موقع بتصميم فاتح لعيادة باسم نور", "light"), ("موقع لعيادة باسم نور", "default")]:
            self.assertEqual(build(q).spec.theme, want, q)

    def test_the_same_words_in_a_name_or_a_colour_or_a_small_app_do_not_change_the_look(self):
        for q in ["موقع لعيادة باسم الراقي", "موقع لعيادة باسم نور ولونه ازرق داكن", "تطبيق بسيط للمهام باسم خفيف"]:
            self.assertEqual(build(q).spec.theme, "default", q)

    def test_luxe_is_gold_unless_a_colour_is_named(self):
        self.assertEqual(build("موقع فخم لمطعم باسم السفرة").spec.accent, themes.LUXE_GOLD)
        self.assertEqual(build("موقع فخم لمطعم باسم السفرة ولونه احمر").spec.accent, COLORS["أحمر"])

    def test_an_edit_switches_the_look_and_a_colour_edit_keeps_it(self):
        spec = build("موقع لمطعم باسم السفرة").spec
        e = edit.apply(spec, "خله فخم")
        self.assertEqual((e.spec.theme, e.spec.accent), ("luxe", themes.LUXE_GOLD))
        e = edit.apply(e.spec, "غير الشكل الى داكن")
        self.assertEqual(e.spec.theme, "dark")
        e = edit.apply(e.spec, "غير اللون الى اخضر")
        self.assertEqual((e.spec.theme, e.spec.accent), ("dark", COLORS["أخضر"]))
        self.assertFalse(edit.apply(spec, "غير اللون الى ازرق داكن").spec.theme != "default")

    def test_detect_ignores_a_shade_of_a_colour(self):
        self.assertEqual(themeword.detect("ازرق داكن"), "default")


if __name__ == "__main__":
    unittest.main()
