"""Builder design and business defaults: the shared theme and the business-type matching.
Offline, no PyTorch.

Run:  python -m tests.builder_design_test
"""
import re
import unittest

from builder import checks, content, theme
from builder.build import build
from builder.spec import COLORS


class Theme(unittest.TestCase):
    def test_the_theme_is_responsive_dark_aware_printable_and_accessible(self):
        css = theme.css("#1d4ed8")
        for feature in ("prefers-color-scheme:dark", "max-width:600px", "@media print", "prefers-reduced-motion",
                        ":focus-visible", "position:sticky", "direction:rtl"):
            self.assertIn(feature, css)
        self.assertEqual(css.count("{"), css.count("}"))
        self.assertNotIn("__ACCENT__", css)

    def test_the_theme_fetches_nothing_from_outside(self):
        self.assertIsNone(re.search(r"url\(|@import|https?:", theme.CSS))

    def test_every_accent_colour_is_dark_enough_for_white_text(self):
        def luminance(hex_):
            r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
            lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
            return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
        for name, hex_ in COLORS.items():
            ratio = 1.05 / (luminance(hex_) + 0.05)
            self.assertGreaterEqual(ratio, 4.5, f"white on {name} {hex_} is {ratio:.1f}:1")

    def test_every_kind_passes_the_static_checks_with_the_theme(self):
        for q in ("موقع لمقهى باسم ركن", "لوحة بيانات باسم م يناير 10 فبراير 20", "متجر باسم الورد وفيه ورد 20",
                  "تطبيق قائمة مهام باسم مهامي", "ملف شخصي باسم ياسر", "مدونة باسم رحال", "دعوة لحفل باسم لقاء"):
            self.assertEqual(checks.check_site(build(q).files), [], q)


class Business(unittest.TestCase):
    def test_specific_kinds_win_over_general_ones(self):
        self.assertEqual(content.for_business("موقع لمغسلة سيارات باسم لمعان")[0], "مغسلة سيارات")
        self.assertEqual(content.for_business("موقع لمعرض سيارات")[0], "معرض سيارات")
        self.assertEqual(content.for_business("موقع لورشة سيارات")[0], "ورشة")

    def test_spelling_variants_and_endings_still_match_but_words_inside_other_words_do_not(self):
        self.assertEqual(content.for_business("موقع لعيادة أسنان")[0], "عيادة")
        self.assertEqual(content.for_business("مكتبي القانوني")[0], "مكتب محاماة")
        self.assertEqual(content.for_business("موقع باسم ورشتي الجديدة")[0], "مشروع")  # not a bare «ورشة»

    def test_every_default_has_a_label_a_tagline_and_three_services(self):
        for words, (label, tagline, services) in content.BUSINESS.items():
            self.assertTrue(label and tagline and len(services) == 3, words)


if __name__ == "__main__":
    unittest.main(verbosity=2)
