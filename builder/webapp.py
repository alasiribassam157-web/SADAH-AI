"""Template: small client-side web apps (task list, registration form). The JavaScript is fixed, reviewed text:
it never uses innerHTML, eval, network calls or inline handlers, and nothing is sent anywhere."""
from html import escape

from builder import base
from builder.spec import Spec

TASKS_JS = """"use strict";
(function () {
  var form = document.getElementById("task-form");
  var input = document.getElementById("task-input");
  var list = document.getElementById("task-list");
  var count = document.getElementById("task-count");
  function update() { count.textContent = String(list.children.length); }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) { return; }
    var li = document.createElement("li");
    var span = document.createElement("span");
    span.textContent = text;
    var del = document.createElement("button");
    del.type = "button";
    del.textContent = "حذف";
    del.addEventListener("click", function () { li.remove(); update(); });
    li.appendChild(span);
    li.appendChild(del);
    list.appendChild(li);
    input.value = "";
    update();
  });
})();
"""
REGISTER_JS = """"use strict";
(function () {
  var form = document.getElementById("reg-form");
  var msg = document.getElementById("reg-msg");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    msg.textContent = form.checkValidity() ? "البيانات صحيحة. لم يُرسل شيء لأي جهة." : "تأكد من تعبئة الحقول بشكل صحيح.";
  });
})();
"""
TASKS_MAIN = ('<section id="app"><h2>مهامك (<span id="task-count">0</span>)</h2>'
              '<form id="task-form"><label for="task-input">مهمة جديدة</label>'
              '<input id="task-input" type="text" required><button type="submit">إضافة</button></form>'
              '<ul id="task-list"></ul></section>')
REGISTER_MAIN = ('<section id="app"><h2>نموذج التسجيل</h2><form id="reg-form" novalidate>'
                 '<label for="reg-name">الاسم</label><input id="reg-name" type="text" required>'
                 '<label for="reg-email">البريد الإلكتروني</label><input id="reg-email" type="email" required>'
                 '<label for="reg-phone">الجوال</label><input id="reg-phone" type="tel" required>'
                 '<button type="submit">تسجيل</button></form><p id="reg-msg" role="status"></p></section>')


def render(spec: Spec) -> dict[str, str]:
    main, js = (TASKS_MAIN, TASKS_JS) if spec.app == "tasks" else (REGISTER_MAIN, REGISTER_JS)
    hero = f'<div class="hero"><h1>{escape(spec.name)}</h1></div>'
    return {"index.html": base.page(spec, '<a href="#app">التطبيق</a>', hero, main, script=True),
            "style.css": base.css(spec), "app.js": js}
