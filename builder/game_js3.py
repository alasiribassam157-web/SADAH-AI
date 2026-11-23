"""Fixed, reviewed JavaScript of the 2048, star-catching and quick-maths games (same rules as game_js.py)."""
from builder.app_js import STORE

BEST = """  var bestEl = document.getElementById("best");
  function keepBest(score) {
    var b = Number(store.get("best", 0));
    if (score > b) { b = score; store.set("best", b); }
    bestEl.textContent = String(b);
  }
"""
G2048 = """"use strict";
(function () {
  __STORE____BEST__  var board = document.getElementById("board"), scoreEl = document.getElementById("score"), status = document.getElementById("status");
  var grid = [], score = 0, cells = [];
  for (var c = 0; c < 16; c++) { var d = document.createElement("div"); d.className = "g"; board.appendChild(d); cells.push(d); }
  function add() {
    var free = [];
    grid.forEach(function (v, i) { if (!v) { free.push(i); } });
    if (free.length) { grid[free[Math.floor(Math.random() * free.length)]] = Math.random() < 0.9 ? 2 : 4; }
  }
  function draw() {
    cells.forEach(function (d, i) { d.textContent = grid[i] ? String(grid[i]) : ""; d.className = "g v" + Math.min(grid[i], 2048); });
    scoreEl.textContent = String(score); keepBest(score);
  }
  function line(a) {
    var v = a.filter(Boolean), out = [];
    for (var i = 0; i < v.length; i++) {
      if (v[i] === v[i + 1]) { out.push(v[i] * 2); score += v[i] * 2; i++; } else { out.push(v[i]); }
    }
    while (out.length < 4) { out.push(0); }
    return out;
  }
  function move(dx, dy) {
    var before = grid.join(",");
    for (var k = 0; k < 4; k++) {
      var idx = [0, 1, 2, 3].map(function (j) { return dy ? j * 4 + k : k * 4 + j; });
      if (dx > 0 || dy > 0) { idx.reverse(); }
      var res = line(idx.map(function (i) { return grid[i]; }));
      idx.forEach(function (i, j) { grid[i] = res[j]; });
    }
    if (grid.join(",") === before) { return; }
    add(); draw();
    if (grid.indexOf(2048) >= 0) { status.textContent = "وصلت إلى 2048! أحسنت."; }
    else if (!canMove()) { status.textContent = "انتهت اللعبة. نقاطك " + score + "."; }
  }
  function canMove() {
    for (var i = 0; i < 16; i++) {
      if (!grid[i] || (i % 4 < 3 && grid[i] === grid[i + 1]) || (i < 12 && grid[i] === grid[i + 4])) { return true; }
    }
    return false;
  }
  function start() { grid = []; for (var i = 0; i < 16; i++) { grid.push(0); } score = 0; status.textContent = ""; add(); add(); draw(); }
  var keys = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1] };
  document.addEventListener("keydown", function (e) { var k = keys[e.key]; if (k) { e.preventDefault(); move(k[0], k[1]); } });
  [["up", 0, -1], ["down", 0, 1], ["left", -1, 0], ["right", 1, 0]].forEach(function (p) {
    document.getElementById(p[0]).addEventListener("click", function () { move(p[1], p[2]); });
  });
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
""".replace("__STORE__", STORE.strip() + "\n").replace("__BEST__", BEST)
CATCH = """"use strict";
(function () {
  __STORE____BEST__  var W = 7, H = 9, board = document.getElementById("board"), scoreEl = document.getElementById("score");
  var status = document.getElementById("status"), livesEl = document.getElementById("lives");
  var cells = [], stars = [], me = 3, score = 0, lives = 3, timer = null, tick = 0;
  for (var c = 0; c < W * H; c++) { var d = document.createElement("div"); d.className = "cell"; board.appendChild(d); cells.push(d); }
  function draw() {
    cells.forEach(function (d) { d.className = "cell"; d.textContent = ""; });
    stars.forEach(function (s) { var d = cells[s.y * W + s.x]; d.className = "cell star"; d.textContent = "★"; });
    var m = cells[(H - 1) * W + me]; m.className = "cell me"; m.textContent = "▬";
    scoreEl.textContent = String(score); livesEl.textContent = String(lives);
  }
  function step() {
    tick++;
    stars.forEach(function (s) { s.y++; });
    stars = stars.filter(function (s) {
      if (s.y < H - 1) { return true; }
      if (s.x === me) { score++; } else { lives--; }
      return false;
    });
    if (tick % 3 === 0) { stars.push({ x: Math.floor(Math.random() * W), y: 0 }); }
    draw();
    if (lives <= 0) { clearInterval(timer); timer = null; keepBest(score); status.textContent = "انتهت اللعبة. نقاطك " + score + "."; }
  }
  function go(dx) { me = Math.max(0, Math.min(W - 1, me + dx)); draw(); }
  function start() {
    if (timer) { clearInterval(timer); }
    stars = []; me = 3; score = 0; lives = 3; tick = 0; status.textContent = "حرّك السلة بالأسهم أو الأزرار."; keepBest(0); draw();
    timer = setInterval(step, 350);
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); } else if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
  });
  document.getElementById("left").addEventListener("click", function () { go(-1); });
  document.getElementById("right").addEventListener("click", function () { go(1); });
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
""".replace("__STORE__", STORE.strip() + "\n").replace("__BEST__", BEST)
MATH = """"use strict";
(function () {
  __STORE____BEST__  var form = document.getElementById("math-form"), input = document.getElementById("math-input"), q = document.getElementById("question");
  var scoreEl = document.getElementById("score"), timeEl = document.getElementById("time"), status = document.getElementById("status");
  var score = 0, left = 30, answer = 0, timer = null;
  function ask() {
    var a = 2 + Math.floor(Math.random() * 11), b = 2 + Math.floor(Math.random() * 11), t = Math.floor(Math.random() * 3);
    if (t === 0) { answer = a + b; q.textContent = a + " + " + b + " = ؟"; }
    else if (t === 1) { answer = a * b; q.textContent = a + " × " + b + " = ؟"; }
    else { if (a < b) { var x = a; a = b; b = x; } answer = a - b; q.textContent = a + " − " + b + " = ؟"; }
    input.value = ""; input.focus();
  }
  function start() {
    if (timer) { clearInterval(timer); }
    score = 0; left = 30; scoreEl.textContent = "0"; timeEl.textContent = "30"; status.textContent = ""; input.disabled = false; keepBest(0); ask();
    timer = setInterval(function () {
      left--; timeEl.textContent = String(left);
      if (left <= 0) { clearInterval(timer); timer = null; input.disabled = true; keepBest(score); status.textContent = "انتهى الوقت. نقاطك " + score + "."; }
    }, 1000);
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!timer || input.value === "") { return; }
    if (Number(input.value) === answer) { score++; scoreEl.textContent = String(score); status.textContent = "صح!"; } else { status.textContent = "خطأ، الصحيح " + answer; }
    ask();
  });
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
""".replace("__STORE__", STORE.strip() + "\n").replace("__BEST__", BEST)
