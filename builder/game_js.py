"""The fixed, reviewed JavaScript of each game. DOM only: textContent and classList, no innerHTML, eval or network."""

MEMORY = """"use strict";
(function () {
  var icons = ["🍎", "🚀", "⭐", "🎈", "🐱", "🌙", "🔥", "🎵"];
  var board = document.getElementById("board"), movesEl = document.getElementById("moves"), status = document.getElementById("status");
  var first = null, lock = false, moves = 0, found = 0;
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function flip(b) {
    if (lock || b === first || b.classList.contains("open")) { return; }
    b.classList.add("open"); b.textContent = b.dataset.icon;
    if (!first) { first = b; return; }
    moves++; movesEl.textContent = String(moves);
    if (first.dataset.icon === b.dataset.icon) {
      found++; first.classList.add("done"); b.classList.add("done"); first = null;
      if (found === icons.length) { status.textContent = "أحسنت! أنهيت اللعبة وعدد حركاتك " + moves + "."; }
      return;
    }
    lock = true;
    var a = first; first = null;
    setTimeout(function () { a.classList.remove("open"); b.classList.remove("open"); a.textContent = ""; b.textContent = ""; lock = false; }, 800);
  }
  function start() {
    board.textContent = ""; first = null; lock = false; moves = 0; found = 0; movesEl.textContent = "0"; status.textContent = "";
    shuffle(icons.concat(icons)).forEach(function (icon) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "tile"; b.setAttribute("aria-label", "بطاقة"); b.dataset.icon = icon;
      b.addEventListener("click", function () { flip(b); });
      board.appendChild(b);
    });
  }
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
"""
GUESS = """"use strict";
(function () {
  var form = document.getElementById("guess-form"), input = document.getElementById("guess-input");
  var status = document.getElementById("status"), triesEl = document.getElementById("tries");
  var target = 0, tries = 0, over = false;
  function start() {
    target = 1 + Math.floor(Math.random() * 100); tries = 0; over = false;
    triesEl.textContent = "0"; status.textContent = "فكرت في رقم من 1 إلى 100. خمّنه!"; input.value = "";
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (over) { return; }
    var g = Number(input.value);
    if (!input.value || g < 1 || g > 100) { status.textContent = "اكتب رقمًا من 1 إلى 100."; return; }
    tries++; triesEl.textContent = String(tries);
    if (g === target) { over = true; status.textContent = "صح! الرقم " + target + " وعدد محاولاتك " + tries + "."; }
    else { status.textContent = g < target ? "الرقم أكبر من " + g : "الرقم أصغر من " + g; }
    input.value = ""; input.focus();
  });
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
"""
XO = """"use strict";
(function () {
  var board = document.getElementById("board"), status = document.getElementById("status");
  var cells = [], state = [], over = false;
  var lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
  function winner(s) {
    for (var i = 0; i < lines.length; i++) {
      var l = lines[i];
      if (s[l[0]] && s[l[0]] === s[l[1]] && s[l[0]] === s[l[2]]) { return s[l[0]]; }
    }
    return "";
  }
  function spot(mark) {
    for (var i = 0; i < lines.length; i++) {
      var l = lines[i], own = 0, free = -1;
      for (var k = 0; k < 3; k++) { if (state[l[k]] === mark) { own++; } else if (!state[l[k]]) { free = l[k]; } }
      if (own === 2 && free >= 0) { return free; }
    }
    return -1;
  }
  function put(i, mark) { state[i] = mark; cells[i].textContent = mark; cells[i].disabled = true; }
  function finish() {
    var w = winner(state);
    if (w) { over = true; status.textContent = w === "X" ? "فزت! أحسنت." : "فاز الجهاز. جرّب مرة ثانية."; return true; }
    if (state.every(Boolean)) { over = true; status.textContent = "تعادل."; return true; }
    return false;
  }
  function computer() {
    var i = spot("O");
    if (i < 0) { i = spot("X"); }
    if (i < 0 && !state[4]) { i = 4; }
    if (i < 0) { var free = []; state.forEach(function (v, k) { if (!v) { free.push(k); } }); i = free[Math.floor(Math.random() * free.length)]; }
    put(i, "O");
    finish();
  }
  function start() {
    board.textContent = ""; cells = []; state = []; over = false; status.textContent = "دورك: أنت X.";
    for (var i = 0; i < 9; i++) {
      (function (k) {
        var b = document.createElement("button");
        b.type = "button"; b.className = "xcell"; b.setAttribute("aria-label", "خانة " + (k + 1));
        b.addEventListener("click", function () { if (over) { return; } put(k, "X"); if (!finish()) { computer(); } });
        state.push(""); cells.push(b); board.appendChild(b);
      })(i);
    }
  }
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
"""
