// CV builder panel: upload files → review the extracted fields → open the finished CV.
const CV_T = {
  ar: { title: "السيرة الذاتية", drop: "ارفع ملفاتك: سيرة قديمة، شهادات، أو أي ملف عنك",
        types: "PDF أو Word (.docx) أو نص، حتى 5 ملفات و5MB لكل ملف. تُقرأ ولا تُحفظ.",
        read: "اقرأ الملفات", reading: "جاري القراءة…", make: "أنشئ السيرة", cvLang: "لغة السيرة",
        review: "راجع البيانات وعدّل اللي تبي، كل سطر عنصر مستقل.", back: "ملفات أخرى",
        name: "الاسم", jobTitle: "المسمى الوظيفي", email: "البريد", phone: "الجوال", links: "روابط",
        summary: "نبذة", experience: "الخبرات", education: "التعليم", skills: "المهارات",
        certificates: "الدورات والشهادات", languages: "اللغات", projects: "المشاريع", fail: "تعذّرت القراءة" },
  en: { title: "CV builder", drop: "Upload your files: an old CV, certificates, anything about you",
        types: "PDF, Word (.docx) or text, up to 5 files, 5MB each. Read, never stored.",
        read: "Read files", reading: "Reading…", make: "Create CV", cvLang: "CV language",
        review: "Review and edit the details, one item per line.", back: "Other files",
        name: "Name", jobTitle: "Job title", email: "Email", phone: "Phone", links: "Links",
        summary: "Profile", experience: "Experience", education: "Education", skills: "Skills",
        certificates: "Courses & certificates", languages: "Languages", projects: "Projects", fail: "Could not read" },
};
const CV_TEXT = [["name", "name"], ["title", "jobTitle"], ["email", "email"], ["phone", "phone"]];
const CV_LISTS = ["summary", "experience", "education", "skills", "certificates", "languages", "projects", "links"];
const ct = (k) => CV_T[lang][k] || k;

function cvShell() {
  let box = $("cv-panel");
  if (box) return box;
  box = document.createElement("div");
  box.id = "cv-panel";
  box.className = "cv-panel";
  box.innerHTML = `<div class="cv-card" role="dialog" aria-modal="true">
    <div class="cv-head"><b id="cv-title"></b><button class="tb-icon" id="cv-close" aria-label="close">×</button></div>
    <div id="cv-body"></div></div>`;
  document.body.appendChild(box);
  box.onclick = (e) => { if (e.target === box) cvClose(); };
  $("cv-close").onclick = cvClose;
  return box;
}

function cvClose() { $("cv-panel")?.classList.remove("open"); }

function cvUpload() {
  $("cv-title").textContent = ct("title");
  $("cv-body").innerHTML = `<label class="cv-drop" id="cv-drop">
      <input type="file" id="cv-files" multiple accept=".pdf,.docx,.txt,.md" hidden />
      <svg viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>
      <b>${ct("drop")}</b><span>${ct("types")}</span><em id="cv-picked"></em></label>
    <p class="cv-err" id="cv-err"></p>
    <button class="cv-go" id="cv-read" disabled>${ct("read")}</button>`;
  const input = $("cv-files"), drop = $("cv-drop");
  const pick = (files) => {
    input.files = files;
    $("cv-picked").textContent = [...files].map((f) => f.name).join(" · ");
    $("cv-read").disabled = !files.length;
  };
  input.onchange = () => pick(input.files);
  drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = (e) => { e.preventDefault(); drop.classList.remove("over"); pick(e.dataTransfer.files); };
  $("cv-read").onclick = () => cvRead(input.files);
}

async function cvRead(files) {
  const btn = $("cv-read"), form = new FormData();
  [...files].forEach((f) => form.append("files", f));
  form.append("lang", lang);
  btn.disabled = true; btn.textContent = ct("reading");
  try {
    const r = await fetch("/api/cv/extract", { method: "POST", body: form });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || ct("fail"));
    cvReview(data.fields);
  } catch (err) {
    $("cv-err").textContent = `${ct("fail")}: ${err.message}`;
    btn.disabled = false; btn.textContent = ct("read");
  }
}

function cvReview(f) {
  const text = CV_TEXT.map(([k, label]) =>
    `<label class="cv-f"><span>${ct(label)}</span><input data-k="${k}" value="${esc(f[k] || "")}" dir="auto" /></label>`).join("");
  const lists = CV_LISTS.map((k) =>
    `<label class="cv-f wide"><span>${ct(k)}</span><textarea data-k="${k}" rows="${k === "summary" ? 3 : 4}" dir="auto">${esc((f[k] || []).join("\n"))}</textarea></label>`).join("");
  $("cv-body").innerHTML = `<p class="cv-note">${ct("review")}</p><div class="cv-grid">${text}${lists}</div>
    <div class="cv-actions"><button class="cv-ghost" id="cv-back">${ct("back")}</button>
      <label class="cv-lang">${ct("cvLang")} <select id="cv-lang"><option value="ar">العربية</option><option value="en">English</option></select></label>
      <button class="cv-go" id="cv-make">${ct("make")}</button></div>`;
  $("cv-lang").value = lang;
  $("cv-back").onclick = cvUpload;
  $("cv-make").onclick = cvMake;
}

async function cvMake() {
  const fields = {};
  document.querySelectorAll("#cv-body [data-k]").forEach((el) => {
    fields[el.dataset.k] = el.tagName === "TEXTAREA" ? el.value.split("\n").map((s) => s.trim()).filter(Boolean) : el.value.trim();
  });
  const tab = window.open("", "_blank");  // open now: browsers block pop-ups opened after an await
  const r = await fetch("/api/cv/render", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fields, lang: $("cv-lang").value }),
  });
  const url = URL.createObjectURL(new Blob([await r.text()], { type: "text/html" }));
  if (tab) tab.location = url; else location.href = url;
}

function openCV() { toggleDrawer(false); cvShell().classList.add("open"); cvUpload(); }
$("btn-cv").onclick = openCV;
if (location.hash === "#cv") openCV();  // shareable link straight to the CV builder
