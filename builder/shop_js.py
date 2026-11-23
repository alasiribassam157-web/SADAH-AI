"""The shop's cart: one app.js, no network and no payment. It adds, counts, totals and writes the order text the customer copies and sends."""

JS = """"use strict";
(function () {
  var KEY = "sadah-cart";
  var shop = document.title;
  var cards = document.querySelectorAll(".card[data-name]");
  var linesEl = document.getElementById("cart-lines");
  var emptyEl = document.getElementById("cart-empty");
  var totalEl = document.getElementById("cart-total");
  var countEl = document.getElementById("cart-count");
  var orderEl = document.getElementById("cart-order");
  var statusEl = document.getElementById("cart-status");
  var products = [];
  var cart = [];
  var unit = "ريال";

  for (var i = 0; i < cards.length; i++) {
    var price = parseFloat(cards[i].getAttribute("data-price"));
    var u = cards[i].getAttribute("data-unit");
    if (u) { unit = u; }
    products.push({ name: cards[i].getAttribute("data-name"), price: isNaN(price) ? null : price });
  }
  function find(list, name) {
    for (var k = 0; k < list.length; k++) { if (list[k].name === name) { return list[k]; } }
    return null;
  }
  function load() {
    try {
      var saved = JSON.parse(localStorage.getItem(KEY) || "[]");
      for (var k = 0; k < saved.length; k++) {
        var p = find(products, saved[k].name);
        var q = Math.floor(Number(saved[k].qty));
        if (p && q > 0 && q < 100 && !find(cart, p.name)) { cart.push({ name: p.name, price: p.price, qty: q }); }
      }
    } catch (e) { cart = []; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(cart)); } catch (e) { return; }
  }
  function money(n) { return String(Math.round(n * 100) / 100) + " " + unit; }
  function button(text, label, fn) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = text;
    b.setAttribute("aria-label", label);
    b.addEventListener("click", fn);
    return b;
  }
  function change(name, by) {
    var line = find(cart, name);
    if (!line) { return; }
    line.qty = Math.min(99, line.qty + by);
    if (line.qty < 1) { cart.splice(cart.indexOf(line), 1); }
    draw();
  }
  function draw() {
    var total = 0, count = 0, priced = true, text = ["طلب من " + shop + ":"];
    linesEl.textContent = "";
    for (var k = 0; k < cart.length; k++) {
      var line = cart[k];
      var li = document.createElement("li");
      li.className = "cart-line";
      var label = document.createElement("span");
      label.className = "cart-name";
      label.textContent = line.name + (line.price === null ? "" : " — " + money(line.price));
      var qty = document.createElement("span");
      qty.className = "qty";
      var num = document.createElement("strong");
      num.textContent = String(line.qty);
      qty.appendChild(button("+", "زيادة " + line.name, change.bind(null, line.name, 1)));
      qty.appendChild(num);
      qty.appendChild(button("−", "إنقاص " + line.name, change.bind(null, line.name, -1)));
      li.appendChild(label);
      li.appendChild(qty);
      linesEl.appendChild(li);
      count += line.qty;
      if (line.price === null) { priced = false; } else { total += line.price * line.qty; }
      text.push("- " + line.name + " × " + line.qty + (line.price === null ? "" : " = " + money(line.price * line.qty)));
    }
    emptyEl.hidden = cart.length > 0;
    countEl.textContent = String(count);
    totalEl.textContent = cart.length === 0 ? "0" : money(total) + (priced ? "" : " (+ منتجات سعرها عند التواصل)");
    text.push("المجموع: " + totalEl.textContent);
    orderEl.value = cart.length === 0 ? "" : text.join("\\n");
    save();
  }
  function say(message) { statusEl.textContent = message; }

  document.getElementById("products").addEventListener("click", function (e) {
    var target = e.target.closest ? e.target.closest("button[data-add]") : null;
    if (!target) { return; }
    var name = target.getAttribute("data-add");
    var line = find(cart, name), p = find(products, name);
    if (line) { line.qty = Math.min(99, line.qty + 1); } else if (p) { cart.push({ name: p.name, price: p.price, qty: 1 }); }
    draw();
    say("أضفت «" + name + "» إلى السلة.");
  });
  document.getElementById("cart-clear").addEventListener("click", function () { cart = []; draw(); say("فرّغت السلة."); });
  document.getElementById("cart-copy").addEventListener("click", function () {
    if (!orderEl.value) { say("السلة فارغة."); return; }
    var sent = "نسخت الطلب. أرسله لنا برقم التواصل أدناه.";
    function manual() {
      var done = false;
      orderEl.select();
      try { done = document.execCommand("copy"); } catch (e) { done = false; }
      say(done ? sent : "حدّد النص وانسخه يدويًا.");
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(orderEl.value).then(function () { say(sent); }, manual);
    } else { manual(); }
  });
  load();
  draw();
})();
"""
