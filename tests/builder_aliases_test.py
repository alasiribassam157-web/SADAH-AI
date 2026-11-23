"""How people really write a request: emoji, stretched letters, English words, a correction in the middle, Latin names. Offline.

Run:  python -m tests.builder_aliases_test
"""
import unittest

from builder import aliases
from builder.build import build
from builder.norm import n


class Clean(unittest.TestCase):
    def test_emoji_are_dropped(self):
        self.assertEqual(aliases.clean("موقع 🌹 باسم وردة 🌹💐"), "موقع باسم وردة")

    def test_a_correction_keeps_what_comes_after_and_the_name_given_before(self):
        self.assertEqual(aliases.clean("موقع لمطعم لا بالاصح متجر باسم الحلا"), "متجر باسم الحلا")
        self.assertEqual(aliases.clean("موقع باسم نور لا بالاصح متجر"), "متجر باسم نور")

    def test_a_word_that_merely_ends_in_a_correction_word_is_left_alone(self):
        self.assertEqual(aliases.clean("متجر باسم عسل الجبل"), "متجر باسم عسل الجبل")
        self.assertEqual(aliases.clean("دعوة باسم مستقبل التقنية"), "دعوة باسم مستقبل التقنية")


class Read(unittest.TestCase):
    def test_stretched_letters_are_collapsed_but_a_doubled_letter_is_kept(self):
        self.assertEqual(aliases.read("ابغااااا"), "ابغا")
        self.assertEqual(aliases.read("الله"), "الله")

    def test_english_words_become_the_arabic_ones_the_rules_know(self):
        self.assertIn("موقع", aliases.read("website لمطعم"))
        self.assertIn(n("صفحة هبوط"), aliases.read("landing page"))
        self.assertIn(n("تطبيق"), aliases.read("ابغى app"))
        self.assertIn("موقع", aliases.read(n("سو لي سايت")))
        self.assertEqual(aliases.read("taskly"), "taskly")   # a Latin name is not an English word


class Requests(unittest.TestCase):
    def test_whatsapp_style_requests_build_what_was_meant(self):
        for q, kind, name in [("ابغااااا موقع لمقهى باسم ركن الهدوء", "landing", "ركن الهدوء"),
                              ("ابغى app للمهام باسم Doit", "webapp", "Doit"),
                              ("ابغى موقع لمحل ورد 🌹 باسم وردة 🌹💐", "landing", "وردة"),
                              ("ابغى موقع لمطعم لا بالاصح متجر باسم الحلا وفيه كيكة 50", "shop", "الحلا"),
                              ("ابغى متجر باسم 3oud وفيه عود 250 وبخور 90", "shop", "3oud"),
                              ("لو سمحت ابي موقع لعيادة باسم الشفاء وجزاك الله خير", "landing", "الشفاء")]:
            r = build(q)
            self.assertEqual((r.ok, r.spec.kind, r.spec.name), (True, kind, name), q)

    def test_latin_script_arabic_is_not_guessed_at(self):
        r = build("abgha mawqe3 le mat3am esmo bayt alshawa")
        self.assertFalse(r.ok)
        self.assertTrue(r.question)


if __name__ == "__main__":
    unittest.main()
