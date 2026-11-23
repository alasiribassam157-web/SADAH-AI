"""Fixed, reviewed JavaScript of the expenses, notes, converter and habits apps (same rules as app_js.py)."""
from builder.app_js import STORE

LIST = """  function row(listEl, text, onDelete) {
    var li = document.createElement("li"), span = document.createElement("span"), del = document.createElement("button");
    span.textContent = text; del.type = "button"; del.textContent = "حذف"; del.addEventListener("click", onDelete);
    li.appendChild(span); li.appendChild(del); listEl.appendChild(li);
  }
"""
EXPENSES = """"use strict";
(function () {
  __STORE____LIST__  var items = store.get("items", []), list = document.getElementById("list"), total = document.getElementById("total");
  var form = document.getElementById("exp-form"), what = document.getElementById("exp-what"), amount = document.getElementById("exp-amount");
  function draw() {
    list.textContent = ""; var sum = 0;
    items.forEach(function (it, i) {
      sum += it.amount;
      row(list, it.what + " — " + it.amount, function () { items.splice(i, 1); store.set("items", items); draw(); });
    });
    total.textContent = String(Math.round(sum * 100) / 100); store.set("items", items);
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var a = Number(amount.value), w = what.value.trim();
    if (!w || !isFinite(a) || a <= 0) { return; }
    items.push({ what: w.slice(0, 60), amount: a }); what.value = ""; amount.value = ""; draw();
  });
  draw();
})();
""".replace("__STORE__", STORE.strip() + "\n").replace("__LIST__", LIST)
NOTES = """"use strict";
(function () {
  __STORE____LIST__  var notes = store.get("notes", []), list = document.getElementById("list");
  var form = document.getElementById("note-form"), text = document.getElementById("note-text");
  function draw() {
    list.textContent = "";
    notes.forEach(function (n, i) { row(list, n, function () { notes.splice(i, 1); store.set("notes", notes); draw(); }); });
    store.set("notes", notes);
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var t = text.value.trim();
    if (!t) { return; }
    notes.unshift(t.slice(0, 300)); text.value = ""; draw();
  });
  draw();
})();
""".replace("__STORE__", STORE.strip() + "\n").replace("__LIST__", LIST)
CONVERTER = """"use strict";
(function () {
  var groups = {
    length: { names: ["متر", "كيلومتر", "ميل", "قدم"], to: [1, 1000, 1609.344, 0.3048] },
    weight: { names: ["كيلوغرام", "غرام", "رطل"], to: [1, 0.001, 0.45359237] },
    temp: { names: ["مئوية", "فهرنهايت", "كلفن"], to: [] }
  };
  var kind = document.getElementById("kind"), from = document.getElementById("from"), to = document.getElementById("to");
  var input = document.getElementById("value"), out = document.getElementById("result");
  function fill(sel, names) {
    sel.textContent = "";
    names.forEach(function (n, i) { var o = document.createElement("option"); o.value = String(i); o.textContent = n; sel.appendChild(o); });
  }
  function celsius(v, unit) { return unit === 0 ? v : unit === 1 ? (v - 32) * 5 / 9 : v - 273.15; }
  function fromCelsius(c, unit) { return unit === 0 ? c : unit === 1 ? c * 9 / 5 + 32 : c + 273.15; }
  function convert() {
    var g = groups[kind.value], v = Number(input.value), a = Number(from.value), b = Number(to.value);
    if (input.value === "" || !isFinite(v)) { out.textContent = ""; return; }
    var r = kind.value === "temp" ? fromCelsius(celsius(v, a), b) : v * g.to[a] / g.to[b];
    out.textContent = String(Math.round(r * 1e6) / 1e6) + " " + g.names[b];
  }
  function reload() { var g = groups[kind.value]; fill(from, g.names); fill(to, g.names); to.value = "1"; convert(); }
  kind.addEventListener("change", reload);
  [from, to, input].forEach(function (el) { el.addEventListener("input", convert); });
  reload();
})();
"""
HABITS = """"use strict";
(function () {
  __STORE__
  var habits = store.get("habits", []), list = document.getElementById("list");
  var form = document.getElementById("habit-form"), name = document.getElementById("habit-name");
  function day(offset) { return new Date(Date.now() - offset * 86400000).toISOString().slice(0, 10); }
  function streak(h) {
    var n = 0, start = h.days.indexOf(day(0)) >= 0 ? 0 : 1;
    while (h.days.indexOf(day(start + n)) >= 0) { n++; }
    return n;
  }
  function draw() {
    list.textContent = "";
    habits.forEach(function (h, i) {
      var li = document.createElement("li"), span = document.createElement("span"), done = document.createElement("button"), del = document.createElement("button");
      var today = h.days.indexOf(day(0)) >= 0;
      span.textContent = h.name + " — " + streak(h) + " يوم متتالي";
      done.type = "button"; done.textContent = today ? "تم اليوم ✓" : "تم اليوم";
      done.addEventListener("click", function () {
        if (today) { h.days = h.days.filter(function (d) { return d !== day(0); }); } else { h.days.push(day(0)); }
        draw();
      });
      del.type = "button"; del.textContent = "حذف"; del.addEventListener("click", function () { habits.splice(i, 1); draw(); });
      li.appendChild(span); li.appendChild(done); li.appendChild(del); list.appendChild(li);
    });
    store.set("habits", habits);
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var n = name.value.trim();
    if (!n) { return; }
    habits.push({ name: n.slice(0, 60), days: [] }); name.value = ""; draw();
  });
  draw();
})();
""".replace("__STORE__", STORE.strip())
