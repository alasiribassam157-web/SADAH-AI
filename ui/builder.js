// Builder page: send the request, show the answer (a question, a refusal or the preview), offer the zip.
(() => {
  const $ = (id) => document.getElementById(id);
  const req = $("req"), go = $("go"), zip = $("zip"), msg = $("msg"), view = $("view");
  let last = "";

  const say = (text, bad) => { msg.textContent = text; msg.className = bad ? "err" : ""; };

  async function post(path, request) {
    return fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request }) });
  }

  go.addEventListener("click", async () => {
    const text = req.value.trim();
    if (!text) { say("اكتب طلبك أولًا.", true); return; }
    go.disabled = true; zip.disabled = true; view.hidden = true; say("جارٍ البناء…");
    try {
      const res = await post("/api/build", text);
      if (!res.ok) throw new Error("server");
      const r = await res.json();
      if (r.ok) {
        last = text; view.srcdoc = r.preview; view.hidden = false; zip.disabled = false;
        say("تم بناء «" + r.name + "». هذه معاينة، والملفات في الـ zip.");
      } else if (r.question) say(r.question, false);
      else if (r.message) say(r.message, true);
      else say("تعذّر البناء: " + r.problems.join("، "), true);
    } catch (e) { say("تعذّر الاتصال بالخادم. حاول مرة أخرى.", true); }
    go.disabled = false;
  });

  zip.addEventListener("click", async () => {
    if (!last) return;
    const res = await post("/api/build/zip", last);
    if (!res.ok) { say("تعذّر تنزيل المشروع.", true); return; }
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a"); a.href = url; a.download = "project.zip"; a.click();
    URL.revokeObjectURL(url);
  });
})();
