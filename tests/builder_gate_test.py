"""Chat -> builder gate: which messages count as «make me a site», what the chat answers, how the link is built.
Offline; needs neither the router brain nor httpx.

Run:  python -m tests.builder_gate_test
"""
import re
import unittest
import urllib.parse
from pathlib import Path

from agent import builder_gate as gate

ROOT = Path(__file__).resolve().parents[1]


class Recognition(unittest.TestCase):
    def test_make_me_requests_are_recognised(self):
        for q in ("اصنع لي موقع", "سوّ لي موقع لمطعم باسم بيت الشواء", "صمم لي متجر باسم الورد وفيه ورد 20",
                  "اعمل لي تطبيق قائمة مهام باسم مهامي", "ابغى مدونة باسم رحال", "ابغى موقع لمطعم باسم النخبة",
                  "ابي دعوة لحفل تخرج باسم دفعة النور", "ودي بلوحة بيانات باسم المبيعات", "انشئ لي ملف شخصي باسم سارة"):
            self.assertTrue(gate.is_build_request(q), q)

    def test_questions_about_places_and_other_requests_are_left_to_the_router(self):
        for q in ("وين موقع المطار", "ابغى موقع المطار", "ابغى متجر قريب مني", "كم سعر تطبيق", "ما هو الموقع الجغرافي لمكة",
                  "اصنع لي قهوة", "سو لي حساب 5 ضرب 7", "طقس الرياض", "ابغى رابط الموقع", "اعمل لي ملف اسمه ideas.txt",
                  "hello", "build me a website"):
            self.assertFalse(gate.is_build_request(q), q)

    def test_diacritics_and_hamza_variants_do_not_matter(self):
        self.assertTrue(gate.is_build_request("سَوِّ لي مَوقع"))  # a diacritic-heavy spelling still has the verb
        self.assertTrue(gate.is_build_request("أصنع لي موقع"))


class Replies(unittest.TestCase):
    def test_a_request_without_a_name_asks_for_it_with_an_example(self):
        out = gate.reply("اصنع لي موقع")
        self.assertIn("ما اسم المشروع؟", out)
        self.assertIn(gate.EXAMPLE, out)

    def test_an_understood_request_names_the_kind_and_links_the_builder_with_the_request(self):
        q = "سوّ لي موقع لمطعم باسم بيت الشواء"
        out = gate.reply(q)
        self.assertIn("موقع تعريفي", out)
        self.assertIn("بيت الشواء", out)
        link = re.search(r"\(/builder\?request=([^)]+)\)", out).group(1)
        self.assertEqual(urllib.parse.unquote(link), q)
        self.assertRegex(link, r"^[A-Za-z0-9%._~-]+$")  # what the chat's link rule accepts

    def test_unsupported_features_are_refused_in_the_chat_too(self):
        self.assertIn("غير مدعوم", gate.reply("ابغى مدونة فيها دردشة"))
        self.assertIn("غير مدعوم", gate.reply("اصنع لي تطبيق اندرويد"))

    def test_other_messages_get_no_reply_from_the_gate(self):
        self.assertEqual(gate.reply("كم الساعة"), "")


class Wiring(unittest.TestCase):
    def test_the_orchestrator_asks_the_gate_before_the_router(self):
        src = (ROOT / "agent" / "orchestrator.py").read_text(encoding="utf-8")
        self.assertIn("builder_gate.reply(task.text)", src)
        self.assertLess(src.index("builder_gate.reply"), src.index("self.supervisor.perceive"))

    def test_chat_renders_only_our_own_builder_link_and_the_builder_reads_it(self):
        chat = (ROOT / "ui" / "chat.js").read_text(encoding="utf-8")
        self.assertIn("/builder\\?request=", chat)
        self.assertNotIn("(https?", chat.split("builder")[1][:80])  # the new rule does not accept arbitrary URLs
        self.assertIn('get("request")', (ROOT / "ui" / "builder.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
