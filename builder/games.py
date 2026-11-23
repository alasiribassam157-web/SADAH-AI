"""Template: small browser games (memory cards, number guess, tic-tac-toe, quiz, snake). The JavaScript is fixed, reviewed
text (builder/game_js.py): DOM only, no innerHTML, eval or network calls, and nothing is sent anywhere."""
import json
from html import escape

from builder import base, game_js, game_js2, game_js3, quizbank
from builder.spec import Spec

_STATUS = '<p id="status" role="status"></p>'
_RESTART = '<button type="button" id="restart">لعبة جديدة</button>'
MAINS = {
    "memory": f'<section id="app"><h2>الحركات: <span id="moves">0</span></h2><div id="board" class="board m"></div>{_STATUS}{_RESTART}</section>',
    "guess": ('<section id="app"><h2>المحاولات: <span id="tries">0</span></h2><form id="guess-form">'
              '<label for="guess-input">تخمينك</label><input id="guess-input" type="number" min="1" max="100">'
              f'<button type="submit">خمّن</button></form>{_STATUS}{_RESTART}</section>'),
    "xo": f'<section id="app"><h2>أنت X والجهاز O</h2><div id="board" class="board x"></div>{_STATUS}{_RESTART}</section>',
    "quiz": ('<section id="app"><h2>النقاط: <span id="score">0</span></h2><p id="question"></p><div id="choices" class="choices"></div>'
             f'{_STATUS}<button type="button" id="next" hidden>السؤال التالي</button>{_RESTART}</section>'),
    "snake": ('<section id="app"><h2>النقاط: <span id="score">0</span></h2><div id="board" class="board s"></div>'
              '<div class="pad"><span></span><button type="button" id="up" aria-label="أعلى">▲</button><span></span>'
              '<button type="button" id="left" aria-label="يسار">◀</button><button type="button" id="down" aria-label="أسفل">▼</button>'
              f'<button type="button" id="right" aria-label="يمين">▶</button></div>{_STATUS}{_RESTART}</section>'),
}
_BEST = ' · الأفضل: <span id="best">0</span>'
_PAD = ('<div class="pad"><span></span><button type="button" id="up" aria-label="أعلى">▲</button><span></span>'
        '<button type="button" id="left" aria-label="يسار">◀</button><button type="button" id="down" aria-label="أسفل">▼</button>'
        '<button type="button" id="right" aria-label="يمين">▶</button></div>')
MAINS["g2048"] = f'<section id="app"><h2>النقاط: <span id="score">0</span>{_BEST}</h2><div id="board" class="board g"></div>{_PAD}{_STATUS}{_RESTART}</section>'
MAINS["catch"] = ('<section id="app"><h2>النقاط: <span id="score">0</span> · الفرص: <span id="lives">3</span>' + _BEST + '</h2><div id="board" class="board c"></div>'
                  '<div class="pad2"><button type="button" id="left" aria-label="يسار">◀</button><button type="button" id="right" aria-label="يمين">▶</button></div>'
                  f'{_STATUS}{_RESTART}</section>')
MAINS["math"] = ('<section id="app"><h2>النقاط: <span id="score">0</span> · الوقت: <span id="time">30</span>' + _BEST + '</h2><p id="question" class="big"></p>'
                 '<form id="math-form"><label for="math-input">إجابتك</label><input id="math-input" type="number" step="1"><button type="submit">أجب</button></form>'
                 f'{_STATUS}{_RESTART}</section>')
MAINS["snake"] = MAINS["snake"].replace('</span></h2>', f'</span>{_BEST}</h2>', 1)
JS = {"memory": game_js.MEMORY, "guess": game_js.GUESS, "xo": game_js.XO, "quiz": game_js2.QUIZ, "snake": game_js2.SNAKE,
      "g2048": game_js3.G2048, "catch": game_js3.CATCH, "math": game_js3.MATH}
HINTS = {"memory": "اقلب البطاقات وطابق الأزواج بأقل عدد من الحركات", "guess": "فكّرت في رقم من 1 إلى 100، خمّنه بأقل محاولات",
         "xo": "العب إكس أو ضد الجهاز", "quiz": "ست أسئلة، اختر الإجابة الصحيحة", "snake": "كُل الطعام واكبر، ولا تصطدم بالجدار أو بنفسك",
         "g2048": "ادمج الأرقام المتشابهة حتى تصل إلى 2048", "catch": "التقط النجوم بالسلة ولا تفوّت أكثر من ثلاث",
         "math": "أجب عن أكبر عدد من المسائل في 30 ثانية"}
CSS = """.board.g{grid-template-columns:repeat(4,1fr);gap:8px;max-width:360px;background:var(--line);padding:8px;border-radius:14px}
.g{aspect-ratio:1;display:grid;place-items:center;border-radius:10px;font-weight:800;font-size:1.6rem;background:var(--card);color:var(--ink)}
.g.v2{background:#fde68a;color:#1f2937}.g.v4{background:#fcd34d;color:#1f2937}.g.v8{background:#fb923c;color:#fff}.g.v16{background:#f97316;color:#fff}
.g.v32{background:#ef4444;color:#fff}.g.v64{background:#dc2626;color:#fff}.g.v128{background:#a855f7;color:#fff}.g.v256{background:#7c3aed;color:#fff}
.g.v512{background:#2563eb;color:#fff}.g.v1024{background:#0891b2;color:#fff;font-size:1.2rem}.g.v2048{background:#15803d;color:#fff;font-size:1.2rem}
.board.c{grid-template-columns:repeat(7,1fr);gap:1px;max-width:340px;background:var(--line);border:2px solid var(--line)}
.cell.star{color:#f59e0b;text-align:center;font-size:1.3rem;line-height:1.6}
.cell.me{background:var(--accent);border-radius:6px;color:#fff;text-align:center;line-height:1.6}
.pad2{display:flex;gap:12px;justify-content:center;direction:ltr;margin-bottom:14px}
.pad2 button{margin:0;padding:12px 34px;border-radius:12px}
#question.big{font-size:3rem;font-weight:800;color:var(--accent);line-height:1.4}
.board{display:grid;gap:10px;margin:0 auto 18px;max-width:440px;direction:ltr}
.board.m{grid-template-columns:repeat(4,1fr)}
.board.x{grid-template-columns:repeat(3,1fr);max-width:330px}
.board.s{grid-template-columns:repeat(14,1fr);gap:1px;max-width:420px;background:var(--line);border:2px solid var(--line)}
.tile,.xcell{aspect-ratio:1;margin:0;padding:0;font-size:2rem;border-radius:12px;display:grid;place-items:center}
.tile{background:var(--accent);color:#fff}
.tile.open,.tile.done{background:var(--card);color:var(--ink);border:2px solid var(--accent)}
.tile.done{opacity:.55}
.xcell{background:var(--card);color:var(--accent);border:2px solid var(--line);font-size:2.4rem;font-weight:800}
.cell{aspect-ratio:1;background:var(--card)}
.cell.snake{background:var(--accent)}
.cell.food{background:#dc2626;border-radius:50%}
.pad{display:grid;grid-template-columns:repeat(3,64px);gap:8px;justify-content:center;direction:ltr;margin-bottom:14px}
.pad button{margin:0;padding:12px 0;border-radius:12px}
.choices{display:grid;gap:10px;max-width:480px;margin:0 auto 14px}
.choices button{margin:0;border-radius:12px;text-align:right}
.choices button.ok{background:#15803d}
.choices button.no{background:#b91c1c}
#question{font-size:1.2rem;font-weight:700;text-align:center}
#status{font-weight:700;text-align:center;min-height:1.9em}
#app{text-align:center}
#app h2{display:inline-block}
#app form{max-width:320px;margin:0 auto}
[hidden]{display:none!important}
"""


def render(spec: Spec) -> dict[str, str]:
    hint = HINTS[spec.game] if spec.game != "quiz" or spec.topic == "general" else f"ست أسئلة عن {quizbank.TOPICS[spec.topic][0]}، اختر الإجابة الصحيحة"
    js = JS[spec.game]
    if spec.game == "quiz":
        js = js.replace("__QS__", json.dumps(quizbank.TOPICS[spec.topic][1], ensure_ascii=False))
    hero = f'<div class="hero"><h1>{escape(spec.name)}</h1><p>{hint}</p></div>'
    return {"index.html": base.page(spec, '<a href="#app">اللعبة</a>', hero, MAINS[spec.game], script=True),
            "style.css": base.css(spec) + CSS, "app.js": js}
