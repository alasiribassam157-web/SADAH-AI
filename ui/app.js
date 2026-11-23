// The one page: send the request, show the answer (a question, a refusal, or the preview), edit it, offer the zip.
(() => {
  const $ = (id) => document.getElementById(id);
  const req = $("req"), go = $("go"), zip = $("zip"), share = $("share"), sharebox = $("sharebox"), sharelink = $("sharelink"), msg = $("msg"), view = $("view");
  const ins = $("ins"), editBtn = $("edit"), editbox = $("editbox"), result = $("result");
  let spec = null;   // the project as the server understood it; edits send it back (the server keeps no state)

  const say = (text, bad) => { msg.textContent = text; msg.className = bad ? "err" : ""; };
  const post = (path, body) => fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const show = (r) => { view.srcdoc = r.preview; result.hidden = false; result.scrollIntoView({ behavior: "smooth", block: "start" }); };

  const KINDS = [
    ["موقع", "ابغى موقع لمخبز باسم فرن البلد وجوالي 0551234567"], ["متجر", "متجر باسم الورد وفيه ورد 20 وشموع 35"],
    ["لوحة بيانات", "لوحة بيانات باسم المبيعات يناير 100 فبراير 140 مارس 180"], ["تطبيق مهام", "تطبيق قائمة مهام باسم مهامي"],
    ["نموذج تسجيل", "تطبيق نموذج تسجيل باسم انطلاقة"], ["ملف أعمال", "ملف اعمال باسم سارة ومهاراتي تصوير ومونتاج"],
    ["مدونة", "مدونة باسم رحلات"], ["دعوة فعالية", "دعوة لحفل تخرج باسم دفعة 2026 يوم الخميس"],
    ["حاسبة", "حاسبة باسم حسابي"], ["عدّاد", "عداد تسبيح باسم ذكر"], ["مؤقت", "مؤقت بومودورو باسم تركيز"], ["مصروفات", "تطبيق مصروفات باسم جيبي"],
    ["ملاحظات", "تطبيق ملاحظات باسم دفتري"], ["محوّل وحدات", "محول وحدات باسم قياس"], ["عادات", "تطبيق عادات باسم نمط"],
    ["شكل فخم", "موقع فخم لمطعم باسم السفرة"], ["شكل داكن", "متجر بثيم داكن باسم ليل وفيه شاي 20 وقهوة 30"], ["شكل بسيط", "موقع مينيمال لعيادة باسم سكون"]];
  const GAMES = [["ذاكرة", "ابغى لعبة ذاكرة باسم نجوم"], ["تخمين رقم", "لعبة تخمين رقم باسم خمنها"], ["إكس أو", "لعبة اكس او ولونها اخضر"],
    ["أسئلة", "لعبة اسئلة باسم تحدي"], ["أسئلة فضاء", "لعبة اسئلة عن الفضاء باسم رواد"], ["ثعبان", "لعبة ثعبان باسم الافعى"],
    ["2048", "ابغى لعبة 2048 باسم الارقام"], ["التقاط", "لعبة التقاط النجوم باسم نجمة"], ["تحدي حساب", "ابي تحدي حساب سريع باسم ذكي"]];
  const fill = (box, list, cls) => list.forEach(([label, q]) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip " + cls; b.textContent = label;
    b.addEventListener("click", () => { req.value = q; req.focus(); });
    box.appendChild(b);
  });
  fill($("kinds"), KINDS, ""); fill($("games"), GAMES, "game");

  go.addEventListener("click", async () => {
    const text = req.value.trim();
    if (!text) { say("اكتب طلبك أولًا.", true); return; }
    go.disabled = true; zip.disabled = true; share.disabled = true; sharebox.hidden = true; result.hidden = true; say("جارٍ البناء…");
    try {
      const res = await post("/api/build", { request: text });
      if (!res.ok) throw new Error("server");
      const r = await res.json();
      if (r.ok) {
        spec = r.spec; zip.disabled = false; share.disabled = false; sharebox.hidden = true; show(r);
        say("تم بناء «" + r.name + "»." + (r.kind === "game" ? " اضغط داخل المعاينة لتلعب." : " هذه معاينة، والملفات في الـ zip."));
      } else if (r.question) say(r.question, false);
      else if (r.message) say(r.message, true);
      else say("تعذّر البناء: " + r.problems.join("، "), true);
    } catch (e) { say("تعذّر الاتصال بالخادم. حاول مرة أخرى.", true); }
    go.disabled = false;
  });
  req.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) go.click(); });

  editBtn.addEventListener("click", async () => {
    const text = ins.value.trim();
    if (!text || !spec) return;
    editBtn.disabled = true;
    try {
      const res = await post("/api/build/edit", { spec, instruction: text });
      if (!res.ok) throw new Error("server");
      const r = await res.json();
      if (r.ok && r.changed) { spec = r.spec; sharebox.hidden = true; view.srcdoc = r.preview; ins.value = ""; say(r.note); }
      else say(r.ok ? r.note : "تعذّر التعديل: " + r.problems.join("، "), !r.ok || !r.changed);
    } catch (e) { say("تعذّر الاتصال بالخادم. حاول مرة أخرى.", true); }
    editBtn.disabled = false;
  });
  ins.addEventListener("keydown", (e) => { if (e.key === "Enter") editBtn.click(); });

  share.addEventListener("click", async () => {
    if (!spec) return;
    share.disabled = true;
    try {
      const res = await post("/api/share", { spec });
      if (!res.ok) throw new Error("server");
      const { url } = await res.json();
      sharelink.href = url; sharelink.textContent = location.origin + url; sharebox.hidden = false;
      say("هذا رابط مشروعك. يشتغل عند أي شخص يفتحه، والرابط نفسه يحمل المشروع بدون حساب ولا تخزين.");
    } catch (e) { say("تعذّر إنشاء الرابط (قد يكون المشروع كبيرًا).", true); }
    share.disabled = false;
  });
  $("copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(sharelink.href); say("نُسخ الرابط."); }
    catch (e) { say("انسخ الرابط يدويًا من الأعلى.", true); }
  });

  zip.addEventListener("click", async () => {
    if (!spec) return;
    const res = await post("/api/build/zip", { spec });
    if (!res.ok) { say("تعذّر تنزيل المشروع.", true); return; }
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a"); a.href = url; a.download = "project.zip"; a.click();
    URL.revokeObjectURL(url);
  });

  const placeholders = ["ابغى موقع لمطعم باسم بيت الشواء ولونه احمر", "لعبة ثعبان باسم الافعى ولونها اخضر", "لوحة بيانات باسم المبيعات يناير 100 فبراير 140",
    "متجر باسم الورد وفيه ورد 20 وشموع 35", "ابغى لعبة ذاكرة باسم نجوم"];
  let at = 0;
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) setInterval(() => { if (!req.value) req.placeholder = placeholders[++at % placeholders.length]; }, 3500);
  req.placeholder = placeholders[0];
  const preset = new URLSearchParams(location.search).get("request");
  if (preset) { req.value = preset.slice(0, 1000); go.click(); }
})();
