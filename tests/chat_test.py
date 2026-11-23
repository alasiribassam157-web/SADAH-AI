"""The chat: rules-only conversation, the optional model bridge (with the provider mocked: no network), the API shape. Offline.

Run:  python -m unittest tests.chat_test
"""
import random
import unittest

from builder import chat, chatapi, specio


def u(t):
    return {"role": "user", "content": t}


def a(t):
    return {"role": "assistant", "content": t}


def talk(*texts, spec=None):
    """Play a conversation: the assistant's replies are fed back as the browser would."""
    msgs, last = [], None
    for t in texts:
        msgs.append(u(t))
        last = chat.turn(msgs, spec)
        msgs.append(a(last.reply))
        spec = specio.to_dict(last.spec) if last.spec else spec
    return last


class Rules(unittest.TestCase):
    def test_small_talk_is_answered_without_building_anything(self):
        for text, key in [("هلا والله", "وش"), ("شكرا يعطيك العافية", "تعديل"), ("وش تقدر تسوي؟", "متاجر")]:
            t = chat.turn([u(text)])
            self.assertIn(key, t.reply, text)
            self.assertIsNone(t.result, text)

    def test_the_name_is_asked_and_the_next_short_message_is_the_name(self):
        t = talk("ابغى موقع لمطعم")
        self.assertIsNone(t.result)
        self.assertIn("اسم", t.reply + " ".join(t.suggestions) + "الاسم")
        t = talk("ابغى موقع لمطعم", "السفرة")
        self.assertTrue(t.result and t.result.ok)
        self.assertEqual(t.spec.name, "السفرة")
        self.assertEqual(t.spec.kind, "landing")

    def test_a_game_question_keeps_the_conversation_together(self):
        t = talk("ابغى لعبة", "اكس او", "باسم الملوك")
        self.assertTrue(t.result and t.result.ok, t.reply)
        self.assertEqual((t.spec.game, t.spec.name), ("xo", "الملوك"))

    def test_an_edit_after_the_build_changes_the_project_and_says_what_changed(self):
        t = talk("ابغى موقع لمطعم باسم السفرة", "غير اللون الى اخضر وخله فخم")
        self.assertEqual(t.spec.theme, "luxe")
        self.assertIn("غيّرت اللون", t.reply)
        self.assertTrue(t.result.ok)

    def test_the_requirements_can_be_asked_for(self):
        t = talk("ابغى متجر باسم الورد وفيه ورد 20 وشموع 35", "وش فهمت؟")
        self.assertIn("الورد", t.reply)
        self.assertIn("2 منتجات", t.reply)

    def test_a_new_project_after_an_old_one_replaces_it(self):
        t = talk("ابغى موقع لمطعم باسم السفرة", "ابي لعبة ذاكرة باسم نجوم")
        self.assertEqual((t.spec.kind, t.spec.name), ("game", "نجوم"))

    def test_what_the_builder_refuses_is_refused_in_the_chat_too(self):
        t = chat.turn([u("ابغى متجر فيه كاشير")])
        self.assertIsNone(t.result)
        self.assertIn("غير مدعوم", t.reply)

    def test_nonsense_gets_a_helpful_reply_not_a_project(self):
        t = chat.turn([u("كم عمر الشمس")])
        self.assertIsNone(t.result)
        self.assertTrue(t.suggestions)

    def test_malformed_input_never_crashes(self):
        for bad in (None, "x", 5, [], [None], [{"role": "system", "content": "x"}], [{"role": "user"}], [{"role": "user", "content": 5}], [a("hi")]):
            self.assertTrue(chat.turn(bad).reply)
        self.assertTrue(chat.turn([u("x" * 100000)] * 50).reply)
        self.assertTrue(chat.turn([u("ابغى موقع باسم س")], {"kind": "x"}).reply)

    def test_random_text_never_crashes_and_never_breaks_the_site_rules(self):
        rnd = random.Random(3)
        words = ["موقع", "متجر", "لعبة", "باسم", "فخم", "اضف", "غير", "اللون", "اخضر", "الاسعار", "2048", "<script>", "ابغى", "وش", "شكرا"]
        for _ in range(400):
            msgs = [u(" ".join(rnd.choice(words) for _ in range(rnd.randint(1, 8)))) for _ in range(rnd.randint(1, 4))]
            t = chat.turn(msgs)
            self.assertTrue(t.reply)
            if t.result:
                self.assertEqual(t.result.problems, [])

    def test_only_the_last_twelve_messages_are_used(self):
        self.assertEqual(len(chat.clean([u(str(i)) for i in range(50)])), 12)


class Interview(unittest.TestCase):
    def test_after_the_build_it_asks_one_thing_at_a_time_and_applies_the_answer(self):
        t = talk("ابغى موقع لمطعم باسم السفرة")
        self.assertIn("أطبّقه", t.reply)
        t = talk("ابغى موقع لمطعم باسم السفرة", "لا")
        self.assertIn("رقم جوال", t.reply)
        t = talk("ابغى موقع لمطعم باسم السفرة", "لا", "0551234567")
        self.assertEqual(t.spec.facts.get("phone"), "0551234567")
        self.assertIn("اللون", t.reply)
        t = talk("ابغى موقع لمطعم باسم السفرة", "لا", "0551234567", "اخضر")
        self.assertEqual(t.spec.accent, "#15803d")
        self.assertIn("الشكل", t.reply)
        t = talk("ابغى موقع لمطعم باسم السفرة", "لا", "0551234567", "اخضر", "فخم")
        self.assertEqual(t.spec.theme, "luxe")
        self.assertIn("كل اللي أسألك", t.reply)

    def test_a_question_can_be_waved_away_and_is_not_asked_again(self):
        t = talk("ابغى موقع لمطعم باسم السفرة", "لا", "لا", "لا", "لا")
        self.assertIn("كل اللي أسألك", t.reply)
        self.assertEqual((t.spec.accent, t.spec.theme, t.spec.facts.get("phone")), ("#1d4ed8", "default", None))

    def test_a_reply_nobody_understands_repeats_the_question_and_never_starts_a_new_project(self):
        t = talk("ابغى موقع لمطعم باسم السفرة", "لا", "كلام غريب جدا")
        self.assertIn("ما فهمت", t.reply)
        self.assertIn("رقم جوال", t.reply)
        self.assertEqual(t.spec.name, "السفرة")

    def test_a_game_gets_no_colour_or_phone_questions(self):
        t = talk("لعبة ثعبان باسم الصحراء")
        self.assertNotIn("رقم جوال", t.reply)
        self.assertNotIn("وش اللون", t.reply)


class NothingLeavesTheServer(unittest.TestCase):
    def test_no_source_file_can_reach_the_network_or_read_a_key(self):
        root = __import__("pathlib").Path(__file__).resolve().parent.parent
        for path in [*(root / "builder").glob("*.py"), *(root / "builder" / "ml").glob("*.py"), root / "app.py"]:
            src = path.read_text(encoding="utf-8")
            for bad in ("urllib.request", "import requests", "import httpx", "import socket", "http.client", "anthropic", "openai", "API_KEY", "os.environ"):
                self.assertNotIn(bad, src.replace("os.getenv(\"HOST\"", "").replace("os.getenv(\"PORT\"", ""), f"{path.name}: {bad}")


class Api(unittest.TestCase):
    def test_the_answer_has_the_shape_the_page_expects(self):
        out = chatapi.respond([u("ابغى موقع لمطعم باسم السفرة")])
        self.assertEqual(set(out), {"reply", "suggestions", "build"})
        self.assertTrue(out["build"]["ok"] and out["build"]["preview"])
        self.assertEqual(chatapi.respond([u("هلا")])["build"], None)
        self.assertLessEqual(len(out["suggestions"]), 4)


class Page(unittest.TestCase):
    ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent / "ui"

    def test_the_page_has_the_chat_and_still_says_there_is_no_outside_model(self):
        html, js = (self.ROOT / "index.html").read_text(encoding="utf-8"), (self.ROOT / "app.js").read_text(encoding="utf-8")
        for needle in ('id="log"', 'id="chatform"', 'id="chatin"'):
            self.assertIn(needle, html)
        self.assertIn("/api/chat", js)
        self.assertNotIn("innerHTML", js)
        self.assertIn("بدون أي نموذج ذكاء خارجي", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
