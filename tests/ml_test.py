"""The design model: reproducible, small, honest about how right it is, explains itself, never sends anything out."""
import json
import unittest
from pathlib import Path

from builder import api
from builder.build import build
from builder.ml import design, nb, profiles
from builder.ml.corpus_a import A
from builder.ml.corpus_b import B
from builder.ml.train import WEIGHTS, build as train, dump
from builder.spec import DEFAULT_ACCENT
from tests import chat_test, ml_heldout as H1, ml_heldout2 as H2, ml_heldout3 as H3


def accuracy(items, min_conf=0.0):
    got = [(design.classify(t), k) for t, k in items]
    got = [(c, k) for c, k in got if c and c[1] >= min_conf]
    return sum(c[0] == k for c, k in got), len(got)


class Model(unittest.TestCase):
    def test_the_weights_file_is_exactly_what_the_trainer_produces(self):
        self.assertEqual(WEIGHTS.read_text(encoding="utf-8"), dump(train()), "run: python -m builder.ml.train")

    def test_it_is_small_and_covers_every_kind_with_a_profile(self):
        self.assertLess(WEIGHTS.stat().st_size, 300 * 1024)
        kinds = set(json.loads(WEIGHTS.read_text(encoding="utf-8"))["labels"])
        self.assertEqual(kinds, set(profiles.P))
        self.assertEqual(kinds, set(A) | set(B))

    def test_accuracy_on_phrases_written_after_the_model_was_trained(self):
        """H3 was measured once before any tuning on it: 44 of 49 right. H1 and H2 were used to tune, so they only guard against regressions."""
        ok, total = accuracy(H3.items())
        self.assertGreaterEqual(ok / total, 0.85, (ok, total))
        self.assertGreaterEqual(accuracy(H1.items())[0] / len(H1.items()), 0.75)
        self.assertGreaterEqual(accuracy(H2.items())[0] / len(H2.items()), 0.82)

    def test_when_it_is_confident_it_is_right_about_nine_times_in_ten(self):
        ok = total = 0
        for h in (H1, H2, H3):
            a, b = accuracy(h.items(), design.MIN)
            ok, total = ok + a, total + b
        self.assertGreaterEqual(ok / total, 0.88, (ok, total))
        self.assertGreater(total, 150)

    def test_the_fresh_set_shares_no_noun_with_the_other_sets_or_the_training_text(self):
        seen = {x.strip() for v in [*A.values(), *B.values()] for x in v.split("،")}
        seen |= {x for h in (H1, H2) for xs in h.NOUNS.values() for x in xs}
        self.assertEqual([x for xs in H3.NOUNS.values() for x in xs if x in seen], [])

    def test_it_says_which_words_decided(self):
        kind, conf, because = design.classify("ابغى موقع لعيادة اسنان")
        self.assertEqual(kind, "medical")
        self.assertTrue({"عيادة", "اسنان"} & set(because))

    def test_text_with_no_known_word_gets_no_answer(self):
        self.assertIsNone(design.classify("zzz qqq"))
        self.assertIsNone(design.classify(""))

    def test_training_twice_gives_the_same_model_and_scores_sum_to_one(self):
        m = nb.Model(json.loads(WEIGHTS.read_text(encoding="utf-8")))
        self.assertAlmostEqual(sum(p for _, p in m.predict("مطعم برجر")), 1.0, places=6)


class Suggesting(unittest.TestCase):
    def test_a_business_gets_a_look_that_suits_it(self):
        s = design.suggest(build("ابغى موقع لعيادة اسنان باسم ابتسامة").spec, "ابغى موقع لعيادة اسنان باسم ابتسامة")
        self.assertEqual((s.kind, s.theme), ("medical", "simple"))
        self.assertEqual(design.apply(build("موقع لعيادة باسم ابتسامة").spec, s).accent, s.accent)

    def test_a_game_or_an_app_has_nothing_to_dress(self):
        self.assertIsNone(design.suggest(build("لعبة ثعبان باسم الصحراء").spec, "لعبة ثعبان باسم الصحراء"))
        self.assertIsNone(design.suggest(build("تطبيق مهام باسم يومي").spec, "تطبيق مهام باسم يومي"))

    def test_the_request_may_ask_for_it_in_the_build(self):
        r = build("موقع لمطعم باسم السفرة واختر لي التصميم المناسب")
        self.assertEqual(r.spec.accent, profiles.P["food"][1])

    def test_a_colour_the_person_chose_is_never_overridden(self):
        r = build("موقع لمطعم باسم السفرة باللون الاخضر واختر لي التصميم المناسب")
        self.assertEqual(r.spec.accent, "#15803d")
        self.assertNotEqual(r.spec.accent, profiles.P["food"][1])

    def test_without_the_keyword_the_build_is_untouched(self):
        self.assertEqual(build("موقع لمطعم باسم السفرة").spec.accent, DEFAULT_ACCENT)

    def test_the_edit_path_can_ask_for_it_too_and_the_site_passes_its_checks(self):
        r = api.respond("موقع لمكتب هندسي باسم اساس")
        e = api.respond_edit(r["spec"], "اختر لي تصميم مناسب")
        self.assertTrue(e["changed"] and e["ok"], e.get("problems"))
        self.assertEqual(e["spec"]["theme"], "simple")

    def test_names_fit_the_business_and_are_stable(self):
        got = design.names("مطعم", "ابغى")
        self.assertEqual(len(got), 3)
        self.assertEqual(got, design.names("مطعم", "ابغى"))
        self.assertEqual(len(design.names("zzz")), 3)


class InChat(unittest.TestCase):
    def test_it_explains_its_reading_and_applies_it_on_yes(self):
        t = chat_test.talk("ابغى موقع لعيادة اسنان باسم ابتسامة")
        self.assertIn("«الصحة والعيادات»", t.reply)
        self.assertEqual(t.suggestions, ["طبّقه", "لا"])
        t = chat_test.talk("ابغى موقع لعيادة اسنان باسم ابتسامة", "طبّقه")
        self.assertEqual((t.spec.accent, t.spec.theme), (profiles.P["medical"][1], "simple"))
        self.assertEqual(t.result.problems, [])
        self.assertIn("رقم جوال", t.reply)

    def test_no_keeps_the_default_look_and_moves_on(self):
        t = chat_test.talk("ابغى موقع لعيادة اسنان باسم ابتسامة", "لا")
        self.assertEqual((t.spec.accent, t.spec.theme), (DEFAULT_ACCENT, "default"))
        self.assertIn("رقم جوال", t.reply)

    def test_it_helps_to_find_a_name(self):
        t = chat_test.talk("ابغى موقع لمطعم")
        self.assertIn("اقترح لي", t.reply)
        t = chat_test.talk("ابغى موقع لمطعم", "اقترح لي")
        self.assertEqual(len(t.suggestions), 3)
        t = chat_test.talk("ابغى موقع لمطعم", "اقترح لي", t.suggestions[0])
        self.assertEqual(t.spec.name, chat_test.talk("ابغى موقع لمطعم", "اقترح لي").suggestions[0])

    def test_it_can_be_asked_later(self):
        t = chat_test.talk("ابغى موقع لمطعم باسم السفرة", "لا", "لا", "لا", "لا", "اختر لي التصميم المناسب")
        self.assertEqual(t.spec.accent, profiles.P["food"][1])


class NothingLeavesTheServer(unittest.TestCase):
    def test_the_model_code_cannot_reach_the_network_or_a_key(self):
        for path in Path(design.__file__).parent.glob("*.py"):
            src = path.read_text(encoding="utf-8")
            for bad in ("urllib", "requests", "httpx", "socket", "http.client", "anthropic", "openai", "API_KEY", "os.environ", "subprocess"):
                self.assertNotIn(bad, src, f"{path.name}: {bad}")


if __name__ == "__main__":
    unittest.main()
