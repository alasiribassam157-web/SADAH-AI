"""Builder games: five games, each a fixed reviewed script that passes the static checks. Offline, no PyTorch.

Run:  python -m tests.builder_games_test
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from builder import checks, edit, games, specio
from builder.build import build, render
from builder.spec import GAMES, Spec, problems


def make(game: str, name: str = "تجربة") -> dict:
    return games.render(Spec(kind="game", name=name, game=game))


class Templates(unittest.TestCase):
    def test_every_game_passes_the_static_checks_and_uses_only_the_three_allowed_files(self):
        for g in GAMES:
            files = make(g)
            self.assertEqual(sorted(files), ["app.js", "index.html", "style.css"], g)
            self.assertEqual(checks.check_site(files), [], g)

    def test_every_game_script_is_valid_javascript(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        for g in GAMES:
            with tempfile.TemporaryDirectory() as d:
                path = Path(d) / "app.js"
                path.write_text(make(g)["app.js"], encoding="utf-8")
                done = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, f"{g}: {done.stderr}")

    def test_the_name_is_escaped(self):
        for g in GAMES:
            html = make(g, '<script>alert(1)</script>')["index.html"]
            self.assertNotIn("<script>alert", html)

    def test_each_game_has_the_elements_its_script_looks_up(self):
        for g in GAMES:
            files = make(g)
            ids = {w.split('"')[0] for w in files["app.js"].split('getElementById("')[1:]}
            for i in ids:
                self.assertIn(f'id="{i}"', files["index.html"], f"{g}: #{i}")


class Spec_(unittest.TestCase):
    def test_an_unknown_game_is_a_problem(self):
        self.assertTrue(problems(Spec(kind="game", name="x", game="chess")))
        self.assertEqual(problems(Spec(kind="game", name="x", game="snake")), [])

    def test_a_game_spec_survives_the_json_round_trip_and_a_bad_game_is_rejected(self):
        spec = Spec(kind="game", name="نجوم", game="quiz", accent="#15803d")
        again, bad = specio.check(specio.to_dict(spec))
        self.assertEqual((bad, again.game), ([], "quiz"))
        _, bad = specio.check({**specio.to_dict(spec), "game": "x" * 99})
        self.assertTrue(bad)
        self.assertTrue(render(Spec(kind="game", name="x", game="chess")).problems)


class Requests(unittest.TestCase):
    def test_each_game_is_found_from_its_arabic_words(self):
        for q, game in [("ابغى لعبة ذاكرة", "memory"), ("لعبة خمن الرقم", "guess"), ("لعبة اكس او", "xo"),
                        ("لعبة اسئلة", "quiz"), ("لعبة ثعبان", "snake")]:
            r = build(q)
            self.assertTrue(r.ok, q)
            self.assertEqual((r.spec.kind, r.spec.game), ("game", game), q)

    def test_no_name_means_the_game_title_not_a_question(self):
        r = build("لعبة ثعبان")
        self.assertEqual(r.spec.name, "لعبة الثعبان")
        self.assertEqual(build("لعبة ثعبان باسم الافعى").spec.name, "الافعى")

    def test_no_game_named_asks_which_one_and_builds_nothing(self):
        for q in ("ابغى لعبة", "ابغى لعبة سباق سيارات"):
            r = build(q)
            self.assertFalse(r.ok)
            self.assertIn("أي لعبة", r.question)
            self.assertFalse(r.files)

    def test_a_site_or_shop_about_games_is_not_a_game(self):
        self.assertEqual(build("موقع لشركة العاب باسم مرح").spec.kind, "landing")
        self.assertEqual(build("متجر العاب باسم ركن وفيه دمية 30 وسيارة 20").spec.kind, "shop")

    def test_online_scores_and_3d_are_refused_plainly(self):
        for q in ("لعبة اونلاين خمن الرقم", "لعبة ثعبان بلوحة متصدرين", "ابغى لعبة ثلاثية الابعاد"):
            r = build(q)
            self.assertFalse(r.ok)
            self.assertIn("غير مدعوم", r.message, q)


class Edits(unittest.TestCase):
    base = build("ابغى لعبة ذاكرة باسم نجوم").spec

    def test_colour_and_name_edits_work_on_a_game(self):
        e = edit.apply(self.base, "غير اللون الى احمر وغير الاسم الى فلاش")
        self.assertTrue(e.changed)
        self.assertEqual((e.spec.accent, e.spec.name, e.spec.game), ("#b91c1c", "فلاش", "memory"))

    def test_the_game_can_be_switched_and_the_default_title_follows_but_a_chosen_name_stays(self):
        e = edit.apply(self.base, "غير اللعبة الى ثعبان")
        self.assertEqual((e.spec.game, e.spec.name), ("snake", "نجوم"))
        d = edit.apply(build("لعبة ثعبان").spec, "بدل اللعبة الى اكس او")
        self.assertEqual((d.spec.game, d.spec.name), ("xo", "إكس أو"))
        self.assertTrue(render(e.spec).ok)

    def test_sections_cannot_be_added_to_a_game(self):
        e = edit.apply(self.base, "اضف قسم الاسعار")
        self.assertFalse(e.changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
