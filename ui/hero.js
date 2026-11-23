// Home hero: particles write a sentence, rebuild it as a site, then spell the sadah wordmark. Timeline runs on animation frames.
(() => {
  const cv = document.getElementById("stage"), cap = document.getElementById("caption");
  if (!cv) return;
  const ctx = cv.getContext("2d"), reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const COLS = ["#F3EEE6", "#F3EEE6", "#FFB36B", "#FF6A3D", "#FFD2A8"];
  let W = 0, H = 0, P = [], layout = null, solid = 0, solidTarget = 0, mouse = { x: -9999, y: -9999 }, started = false;
  const SENT = "ابغى موقع لمخبز باسم فرن البلد";
  const small = () => W < 700;

  function resize() {
    const dpr = Math.min(devicePixelRatio || 1, 2);
    W = cv.clientWidth; H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    P = []; const n = small() ? 1400 : 2800;
    for (let i = 0; i < n; i++) P.push({ x: Math.random() * W, y: Math.random() * H, vx: 0, vy: 0, tx: null, ty: null, c: COLS[i % 5], s: Math.random() * 1.3 + .6, a: 0, ta: .9 });
    cycleStart = 0; fired = 0;
  }
  function sample(draw, gap) {
    const o = document.createElement("canvas"); o.width = W; o.height = H;
    const c = o.getContext("2d"); c.fillStyle = c.strokeStyle = "#fff"; draw(c);
    const d = c.getImageData(0, 0, W, H).data, pts = [];
    for (let y = 0; y < H; y += gap) for (let x = 0; x < W; x += gap) if (d[(y * W + x) * 4 + 3] > 128) pts.push([x, y]);
    return pts;
  }
  const cy = () => H * .46;
  function textPts(str, font, maxW) {
    return sample(c => {
      let size = parseInt(font); c.font = font; c.textAlign = "center"; c.textBaseline = "middle"; c.direction = "rtl";
      while (c.measureText(str).width > maxW && size > 12) { size -= 2; c.font = font.replace(/\d+px/, size + "px"); }
      c.fillText(str, W / 2, cy());
    }, small() ? 3 : 4);
  }
  function siteLayout() {
    const w = Math.min(small() ? W * .9 : W * .62, 760, H * 1.55), h = w * .5, x = (W - w) / 2, y = cy() - h / 2;
    const r = (a, b, c, d) => ({ x: x + a * w, y: y + b * h, w: c * w, h: d * h });
    return { frame: r(0, 0, 1, 1), nav: r(.04, .06, .92, .08), title: r(.48, .24, .46, .2), cta: r(.72, .52, .22, .1),
      img: r(.05, .22, .38, .42), c1: r(.05, .72, .28, .2), c2: r(.36, .72, .28, .2), c3: r(.67, .72, .28, .2) };
  }
  function sitePts() {
    layout = siteLayout();
    return sample(c => {
      const L = layout; c.lineWidth = 2;
      const rr = (b, fill) => { c.beginPath(); c.roundRect(b.x, b.y, b.w, b.h, 10); fill ? c.fill() : c.stroke(); };
      rr(L.frame, false); rr(L.nav, false); rr(L.img, true); rr(L.title, true); rr(L.cta, true); rr(L.c1, false); rr(L.c2, false); rr(L.c3, false);
    }, small() ? 4 : 5);
  }
  function target(pts) {
    const idx = pts.map((_, i) => i).sort(() => Math.random() - .5);
    P.forEach((p, i) => {
      if (!pts.length) return;
      const q = pts[idx[i % idx.length]], full = i < idx.length;
      p.tx = q[0] + (full ? 0 : (Math.random() - .5) * 6); p.ty = q[1] + (full ? 0 : (Math.random() - .5) * 6); p.ta = full ? .95 : .35;
    });
  }
  function scatter(force) {
    P.forEach(p => { p.tx = p.ty = null; p.ta = .55; const a = Math.random() * 6.28, f = Math.random() * force; p.vx += Math.cos(a) * f; p.vy += Math.sin(a) * f; });
  }
  function drawSite(k) {
    const L = layout, rr = (b, col, r = 10) => { ctx.fillStyle = col; ctx.beginPath(); ctx.roundRect(b.x, b.y, b.w, b.h, r); ctx.fill(); };
    ctx.globalAlpha = k; rr(L.frame, "#FBF7F1", 16);
    ctx.fillStyle = "#2A1B0E"; ctx.textAlign = "right"; ctx.textBaseline = "middle"; ctx.direction = "rtl";
    ctx.font = `700 ${Math.round(L.nav.h * .55)}px Alexandria`; ctx.fillText("فرن البلد", L.nav.x + L.nav.w, L.nav.y + L.nav.h / 2);
    ctx.font = `300 ${Math.round(L.nav.h * .42)}px Alexandria`; ctx.textAlign = "left"; ctx.fillStyle = "#6B5340";
    ctx.fillText("من نحن · خدماتنا · تواصل معنا", L.nav.x, L.nav.y + L.nav.h / 2);
    const g = ctx.createRadialGradient(L.img.x + L.img.w * .3, L.img.y + L.img.h * .3, 4, L.img.x + L.img.w / 2, L.img.y + L.img.h / 2, L.img.w * .7);
    g.addColorStop(0, "#F6C27A"); g.addColorStop(.55, "#D98E3B"); g.addColorStop(1, "#A85D1E"); rr(L.img, g, 18);
    ctx.textAlign = "right"; ctx.fillStyle = "#2A1B0E"; ctx.font = `700 ${Math.round(L.title.h * .36)}px Alexandria`;
    ctx.fillText("خبز طازج", L.title.x + L.title.w, L.title.y + L.title.h * .28); ctx.fillText("كل صباح", L.title.x + L.title.w, L.title.y + L.title.h * .78);
    rr(L.cta, "#8A5A2B", 99); ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.font = `500 ${Math.round(L.cta.h * .42)}px Alexandria`;
    ctx.fillText("اطلب الآن", L.cta.x + L.cta.w / 2, L.cta.y + L.cta.h / 2);
    [["خبز", "#F6C27A", L.c1], ["حلويات", "#E8A0A0", L.c2], ["طلبات خاصة", "#A8C99B", L.c3]].forEach(([n, col, b]) => {
      rr(b, "#FFFFFF", 12); rr({ x: b.x + b.w - b.h * .38 - 10, y: b.y + 10, w: b.h * .32, h: b.h * .32 }, col, 7);
      ctx.fillStyle = "#2A1B0E"; ctx.textAlign = "right"; ctx.font = `400 ${Math.round(b.h * .2)}px Alexandria`; ctx.fillText(n, b.x + b.w - 10, b.y + b.h * .72);
    });
    ctx.globalAlpha = 1;
  }

  const say = (before, bold, after = "") => {   // caption: plain text around one bold word, built with DOM nodes (no HTML strings)
    const b = document.createElement("b"); b.textContent = bold;
    cap.replaceChildren(before, b, after);
    cap.classList.remove("fade"); void cap.offsetWidth; cap.classList.add("fade");
  };
  const CYCLE = 15600, big = () => small() ? 30 : 56;
  const EVENTS = [
    [0, () => { solidTarget = 0; say("تكتب ", "جملة"); target(textPts(SENT, `500 ${big()}px Alexandria`, W * .86)); }],
    [3200, () => { say("sadah ", "تفهمها"); scatter(9); }],
    [4400, () => { say("و", "تبني", " مشروعك"); target(sitePts()); }],
    [6200, () => { solidTarget = 1; }],
    [9800, () => { solidTarget = 0; scatter(7); say("موقع، أو تطبيق، أو ", "لعبة"); }],
    [11000, () => { target(textPts("sadah", `800 ${small() ? 80 : Math.min(190, H * .5)}px Syne`, W * .8)); }],
    [14500, () => { scatter(10); }],
  ];
  let cycleStart = 0, fired = 0;
  function tick(now) {
    if (!cycleStart) cycleStart = now;
    let e = now - cycleStart;
    if (e >= CYCLE) { cycleStart = now; fired = 0; e = 0; }
    while (fired < EVENTS.length && e >= EVENTS[fired][0]) EVENTS[fired++][1]();
  }
  function frame(now) {
    requestAnimationFrame(frame);
    if (!cv.clientWidth || document.hidden) return;                  // home hidden while chatting
    if (cv.clientWidth !== W || cv.clientHeight !== H) { resize(); return; }
    const t = now / 1000;
    ctx.globalCompositeOperation = "destination-out"; ctx.fillStyle = "rgba(0,0,0,.36)"; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "lighter";
    for (const p of P) {
      if (p.tx !== null) { p.vx += (p.tx - p.x) * .018; p.vy += (p.ty - p.y) * .018; p.vx *= .86; p.vy *= .86; }
      else { const a = Math.sin(p.y * .006 + t * .6) + Math.cos(p.x * .005 - t * .4); p.vx += Math.cos(a * 2) * .06; p.vy += Math.sin(a * 2) * .06; p.vx *= .97; p.vy *= .97; }
      const dx = p.x - mouse.x, dy = p.y - mouse.y, d2 = dx * dx + dy * dy;
      if (d2 < 14000) { const f = (14000 - d2) / 14000 * 2.2, d = Math.sqrt(d2) || 1; p.vx += dx / d * f; p.vy += dy / d * f; }
      p.x += p.vx; p.y += p.vy; p.a += (p.ta - p.a) * .05;
      ctx.globalAlpha = p.a * (1 - solid * .7); ctx.fillStyle = p.c; ctx.fillRect(p.x, p.y, p.s, p.s);
    }
    ctx.globalCompositeOperation = "source-over"; ctx.globalAlpha = 1;
    tick(now); solid += (solidTarget - solid) * .05;
    if (solid > .01 && layout) drawSite(solid);
  }
  const hero = document.getElementById("hero");
  hero.addEventListener("pointermove", (e) => { const r = cv.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top; });
  hero.addEventListener("pointerleave", () => { mouse.x = mouse.y = -9999; });

  const fonts = document.fonts ? Promise.all([document.fonts.load("700 20px Alexandria"), document.fonts.load("500 20px Alexandria"), document.fonts.load("800 20px Syne")]) : Promise.resolve();
  fonts.catch(() => {}).then(() => {
    resize();
    if (reduce) { layout = siteLayout(); drawSite(1); cap.textContent = "من جملة إلى موقع"; return; }
    requestAnimationFrame(frame);
  });
})();
