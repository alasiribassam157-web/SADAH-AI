"""Fixed, reviewed JavaScript of the quiz and snake games (same rules as game_js.py)."""

QUIZ = """"use strict";
(function () {
  var qs = [
    ["ما عاصمة المملكة العربية السعودية؟", ["جدة", "الرياض", "الدمام", "مكة"], 1],
    ["كم عدد أيام الأسبوع؟", ["5", "6", "7", "8"], 2],
    ["ما أكبر كوكب في المجموعة الشمسية؟", ["المشتري", "الأرض", "المريخ", "زحل"], 0],
    ["كم يساوي 12 × 3؟", ["32", "34", "36", "38"], 2],
    ["أي هذه الكائنات من الثدييات؟", ["القرش", "السلمون", "الضفدع", "الدلفين"], 3],
    ["كم عدد قارات العالم؟", ["5", "6", "7", "9"], 2]
  ];
  var qEl = document.getElementById("question"), box = document.getElementById("choices"), status = document.getElementById("status");
  var scoreEl = document.getElementById("score"), nextBtn = document.getElementById("next");
  var at = 0, score = 0, answered = false;
  function show() {
    answered = false; nextBtn.hidden = true; box.textContent = ""; status.textContent = "";
    qEl.textContent = (at + 1) + " / " + qs.length + ": " + qs[at][0];
    qs[at][1].forEach(function (text, i) {
      var b = document.createElement("button");
      b.type = "button"; b.textContent = text;
      b.addEventListener("click", function () {
        if (answered) { return; }
        answered = true;
        var right = i === qs[at][2];
        if (right) { score++; }
        b.classList.add(right ? "ok" : "no");
        status.textContent = right ? "إجابة صحيحة!" : "إجابة خاطئة. الصحيح: " + qs[at][1][qs[at][2]];
        scoreEl.textContent = String(score);
        nextBtn.hidden = false;
        nextBtn.textContent = at === qs.length - 1 ? "النتيجة" : "السؤال التالي";
      });
      box.appendChild(b);
    });
  }
  nextBtn.addEventListener("click", function () {
    if (at === qs.length - 1) {
      box.textContent = ""; nextBtn.hidden = true;
      qEl.textContent = "انتهت المسابقة. نتيجتك " + score + " من " + qs.length + ".";
      status.textContent = "";
      at = 0; score = 0; scoreEl.textContent = "0";
      document.getElementById("restart").hidden = false;
      return;
    }
    at++; show();
  });
  document.getElementById("restart").addEventListener("click", function () { this.hidden = true; show(); });
  document.getElementById("restart").hidden = true;
  show();
})();
"""
SNAKE = """"use strict";
(function () {
  var N = 14, board = document.getElementById("board"), status = document.getElementById("status"), scoreEl = document.getElementById("score");
  var cells = [], snake = [], dir = [1, 0], want = [1, 0], food = 0, timer = null, score = 0;
  for (var c = 0; c < N * N; c++) { var d = document.createElement("div"); d.className = "cell"; board.appendChild(d); cells.push(d); }
  function place() {
    do { food = Math.floor(Math.random() * N * N); } while (snake.indexOf(food) >= 0);
  }
  function draw() {
    cells.forEach(function (d) { d.className = "cell"; });
    snake.forEach(function (i) { cells[i].className = "cell snake"; });
    cells[food].className = "cell food";
  }
  function stop(text) { clearInterval(timer); timer = null; status.textContent = text; }
  function step() {
    dir = want;
    var x = snake[0] % N + dir[0], y = Math.floor(snake[0] / N) + dir[1];
    if (x < 0 || y < 0 || x >= N || y >= N || snake.indexOf(y * N + x) >= 0) { stop("انتهت اللعبة. نقاطك " + score + "."); return; }
    snake.unshift(y * N + x);
    if (snake[0] === food) { score++; scoreEl.textContent = String(score); place(); } else { snake.pop(); }
    draw();
  }
  function turn(dx, dy) { if (dx !== -dir[0] || dy !== -dir[1]) { want = [dx, dy]; } }
  function start() {
    if (timer) { clearInterval(timer); }
    snake = [Math.floor(N / 2) * N + 3, Math.floor(N / 2) * N + 2]; dir = [1, 0]; want = [1, 0]; score = 0;
    scoreEl.textContent = "0"; status.textContent = "استخدم الأسهم أو الأزرار."; place(); draw();
    timer = setInterval(step, 150);
  }
  var keys = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1] };
  document.addEventListener("keydown", function (e) {
    var k = keys[e.key];
    if (k) { e.preventDefault(); turn(k[0], k[1]); }
  });
  [["up", 0, -1], ["down", 0, 1], ["left", -1, 0], ["right", 1, 0]].forEach(function (p) {
    document.getElementById(p[0]).addEventListener("click", function () { turn(p[1], p[2]); });
  });
  document.getElementById("restart").addEventListener("click", start);
  start();
})();
"""
