// Builder page: send the request, show the answer (a question, a refusal or the preview), offer the zip.
(() => {
  const $ = (id) => document.getElementById(id);
  const req = $("req"), go = $("go"), zip = $("zip"), msg = $("msg"), view = $("view");
  const ins = $("ins"), editBtn = $("edit"), editbox = $("editbox");
  let spec = null;   // `spec` is the project as the server understood it; edits send it back (the server keeps no state)

  const say = (text, bad) => { msg.textContent = text; msg.className = bad ? "err" : ""; };

  async function post(path, body) {
    return fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }

  go.addEventListener("click", async () => {
    const text = req.value.trim();
    if (!text) { say("اكتب طلبك أولًا.", true); return; }
    go.disabled = true; zip.disabled = true; view.hidden = true; editbox.hidden = true; say("جارٍ البناء…");
    try {
      const res = await post("/api/build", { request: text });
      if (!res.ok) throw new Error("server");
      const r = await res.json();
      if (r.ok) {
        spec = r.spec; view.srcdoc = r.preview; view.hidden = false; zip.disabled = false; editbox.hidden = false;
        say("تم بناء «" + r.name + "». هذه معاينة، والملفات في الـ zip.");
      } else if (r.question) say(r.question, false);
      else if (r.message) say(r.message, true);
      else say("تعذّر البناء: " + r.problems.join("، "), true);
    } catch (e) { say("تعذّر الاتصال بالخادم. حاول مرة أخرى.", true); }
    go.disabled = false;
  });

  editBtn.addEventListener("click", async () => {
    const text = ins.value.trim();
    if (!text || !spec) return;
    editBtn.disabled = true;
    try {
      const res = await post("/api/build/edit", { spec, instruction: text });
      if (!res.ok) throw new Error("server");
      const r = await res.json();
      if (r.ok && r.changed) { spec = r.spec; view.srcdoc = r.preview; ins.value = ""; say(r.note); }
      else say(r.ok ? r.note : "تعذّر التعديل: " + r.problems.join("، "), !r.ok || !r.changed);
    } catch (e) { say("تعذّر الاتصال بالخادم. حاول مرة أخرى.", true); }
    editBtn.disabled = false;
  });
  ins.addEventListener("keydown", (e) => { if (e.key === "Enter") editBtn.click(); });

  zip.addEventListener("click", async () => {
    if (!spec) return;
    const res = await post("/api/build/zip", { spec });
    if (!res.ok) { say("تعذّر تنزيل المشروع.", true); return; }
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a"); a.href = url; a.download = "project.zip"; a.click();
    URL.revokeObjectURL(url);
  });
  const preset = new URLSearchParams(location.search).get("request");   // link from the chat
  if (preset) { req.value = preset.slice(0, 1000); go.click(); }
})();
