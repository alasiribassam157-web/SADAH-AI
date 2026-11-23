"""The page body and extra CSS of the small apps beyond the task list and the sign-up form."""
from builder import app_js, app_js2

_OUT = '<p id="status" role="status"></p>'
MAINS = {
    "calculator": '<section id="app"><h2>الحاسبة</h2><div id="calc"><output id="calc-screen" aria-live="polite">0</output><div id="calc-keys" class="keys"></div></div></section>',
    "counter": ('<section id="app"><h2>العدّاد</h2><p id="count" class="big">0</p><div class="row"><button type="button" id="minus" aria-label="إنقاص">−</button>'
                '<button type="button" id="plus">+1</button><button type="button" id="reset">تصفير</button></div><label for="goal">الهدف (اختياري)</label>'
                f'<input id="goal" type="number" min="0">{_OUT}</section>'),
    "timer": ('<section id="app"><h2>المؤقت</h2><p id="time" class="big">25:00</p><div class="row"><button type="button" id="start">ابدأ</button>'
              '<button type="button" id="reset">إعادة</button></div><div class="row"><button type="button" id="p25">25 دقيقة</button>'
              '<button type="button" id="p15">15 دقيقة</button><button type="button" id="p5">5 دقائق</button></div><label for="mins">الدقائق</label>'
              f'<input id="mins" type="number" min="1" max="600" value="25">{_OUT}</section>'),
    "expenses": ('<section id="app"><h2>المصروفات: <span id="total">0</span></h2><form id="exp-form"><label for="exp-what">البند</label>'
                 '<input id="exp-what" type="text" maxlength="60" required><label for="exp-amount">المبلغ</label>'
                 '<input id="exp-amount" type="number" min="0" step="any" required><button type="submit">إضافة</button></form><ul id="list"></ul></section>'),
    "notes": ('<section id="app"><h2>ملاحظاتك</h2><form id="note-form"><label for="note-text">ملاحظة جديدة</label>'
              '<textarea id="note-text" rows="3" maxlength="300" required></textarea><button type="submit">حفظ</button></form><ul id="list"></ul></section>'),
    "converter": ('<section id="app"><h2>محوّل الوحدات</h2><label for="kind">النوع</label><select id="kind"><option value="length">الطول</option>'
                  '<option value="weight">الوزن</option><option value="temp">الحرارة</option></select><label for="value">القيمة</label>'
                  '<input id="value" type="number" step="any"><label for="from">من</label><select id="from"></select><label for="to">إلى</label>'
                  '<select id="to"></select><p id="result" class="big" role="status"></p></section>'),
    "habits": ('<section id="app"><h2>عاداتك اليومية</h2><form id="habit-form"><label for="habit-name">عادة جديدة</label>'
               '<input id="habit-name" type="text" maxlength="60" required><button type="submit">إضافة</button></form><ul id="list"></ul></section>'),
}
JS = {"calculator": app_js.CALC, "counter": app_js.COUNTER, "timer": app_js.TIMER, "expenses": app_js2.EXPENSES, "notes": app_js2.NOTES,
      "converter": app_js2.CONVERTER, "habits": app_js2.HABITS}
CSS = """.big{font-size:3rem;font-weight:800;text-align:center;color:var(--accent-text);margin:0 0 12px;line-height:1.3}
.row{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:8px}
#app{max-width:560px}
#app h2{display:inline-block}
select,textarea{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:10px;font:inherit;background:var(--card);color:var(--ink)}
#status{font-weight:700;text-align:center;min-height:1.9em}
#calc{max-width:340px;margin:0 auto}
#calc-screen{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 18px;font-size:2rem;text-align:left;direction:ltr;margin-bottom:12px;min-height:64px;overflow:hidden}
.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;direction:ltr}
.keys button{margin:0;padding:16px 0;font-size:1.3rem;border-radius:14px}
.keys .wide{grid-column:span 4}
"""
