"""Fixed, reviewed JavaScript of the calculator, counter and timer apps. DOM only (textContent, createElement): no innerHTML,
eval or network. `STORE` keeps data in this browser's localStorage when the page allows it and falls back to memory."""

STORE = """var store = {
  key: function (name) { return "sadah:" + document.title + ":" + name; },
  get: function (name, fallback) {
    try { var v = window.localStorage.getItem(store.key(name)); return v === null ? fallback : JSON.parse(v); } catch (e) { return fallback; }
  },
  set: function (name, value) { try { window.localStorage.setItem(store.key(name), JSON.stringify(value)); } catch (e) { } }
};
"""
CALC = """"use strict";
(function () {
  var screen = document.getElementById("calc-screen"), keys = document.getElementById("calc-keys");
  var acc = null, op = "", cur = "0", fresh = true;
  var layout = [["C", "C"], ["÷", "/"], ["×", "*"], ["−", "-"], ["7", "7"], ["8", "8"], ["9", "9"], ["+", "+"], ["4", "4"], ["5", "5"], ["6", "6"],
    ["=", "="], ["1", "1"], ["2", "2"], ["3", "3"], [".", "."], ["0", "0"]];
  function fmt(x) { return isFinite(x) ? String(Math.round(x * 1e9) / 1e9) : "خطأ"; }
  function calc(a, b, o) {
    if (o === "+") { return a + b; }
    if (o === "-") { return a - b; }
    if (o === "*") { return a * b; }
    return b === 0 ? NaN : a / b;
  }
  function press(k) {
    if (cur === "خطأ") { acc = null; op = ""; cur = "0"; fresh = true; }
    if (k >= "0" && k <= "9" && k.length === 1) { cur = fresh || cur === "0" ? k : cur + k; fresh = false; }
    else if (k === ".") { if (fresh) { cur = "0."; fresh = false; } else if (cur.indexOf(".") < 0) { cur += "."; } }
    else if (k === "C") { acc = null; op = ""; cur = "0"; fresh = true; }
    else if (k === "=") {
      if (op && !fresh) { cur = fmt(calc(acc, Number(cur), op)); }
      acc = null; op = ""; fresh = true;
    } else {
      if (op && !fresh) { acc = calc(acc, Number(cur), op); cur = fmt(acc); } else if (!op) { acc = Number(cur); }
      op = k; fresh = true;
    }
    screen.textContent = cur;
  }
  layout.forEach(function (p) {
    var b = document.createElement("button");
    b.type = "button"; b.textContent = p[0]; b.setAttribute("aria-label", p[0]);
    if (p[1] === "0") { b.className = "wide"; }
    b.addEventListener("click", function () { press(p[1]); });
    keys.appendChild(b);
  });
  document.addEventListener("keydown", function (e) {
    var k = e.key === "Enter" ? "=" : e.key === "Escape" ? "C" : e.key;
    if ("0123456789.+-*/=C".indexOf(k) >= 0 && k.length === 1) { e.preventDefault(); press(k); }
  });
})();
"""
COUNTER = """"use strict";
(function () {
  __STORE__
  var n = Number(store.get("count", 0)), target = Number(store.get("target", 0));
  var out = document.getElementById("count"), status = document.getElementById("status"), goal = document.getElementById("goal");
  function show() {
    out.textContent = String(n); store.set("count", n);
    status.textContent = target > 0 && n >= target ? "وصلت إلى الهدف " + target + "!" : "";
  }
  document.getElementById("plus").addEventListener("click", function () { n++; show(); });
  document.getElementById("minus").addEventListener("click", function () { if (n > 0) { n--; show(); } });
  document.getElementById("reset").addEventListener("click", function () { n = 0; show(); });
  goal.value = target > 0 ? String(target) : "";
  goal.addEventListener("input", function () { target = Math.max(0, Math.floor(Number(goal.value) || 0)); store.set("target", target); show(); });
  show();
})();
""".replace("__STORE__", STORE.strip())
TIMER = """"use strict";
(function () {
  var mins = document.getElementById("mins"), out = document.getElementById("time"), status = document.getElementById("status");
  var startBtn = document.getElementById("start"), left = 25 * 60000, endAt = 0, tick = null;
  function show() {
    var s = Math.max(0, Math.ceil(left / 1000));
    out.textContent = String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
  }
  function stop() { clearInterval(tick); tick = null; startBtn.textContent = "ابدأ"; }
  function run() {
    left = Math.max(0, endAt - Date.now()); show();
    if (left <= 0) { stop(); status.textContent = "انتهى الوقت!"; }
  }
  function set(m) { stop(); left = Math.max(1, Math.min(600, m)) * 60000; status.textContent = ""; show(); }
  startBtn.addEventListener("click", function () {
    if (tick) { stop(); status.textContent = "متوقف مؤقتًا"; return; }
    if (left <= 0) { set(Number(mins.value) || 25); }
    endAt = Date.now() + left; status.textContent = ""; startBtn.textContent = "إيقاف مؤقت";
    tick = setInterval(run, 250);
  });
  document.getElementById("reset").addEventListener("click", function () { set(Number(mins.value) || 25); });
  mins.addEventListener("change", function () { set(Number(mins.value) || 25); });
  [["p25", 25], ["p5", 5], ["p15", 15]].forEach(function (p) {
    document.getElementById(p[0]).addEventListener("click", function () { mins.value = String(p[1]); set(p[1]); });
  });
  show();
})();
"""
