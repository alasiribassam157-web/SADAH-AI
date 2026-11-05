// NAWL user chat: bento home (home.js) and a focused conversation, with saved chats (history.js).
const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const sharedQuestion = params.get("q");  // shareable links: /?q=...  and  /?theme=dark
if (["dark", "light"].includes(params.get("theme"))) store.set("nexus_theme", params.get("theme"));
if (location.search) history.replaceState(null, "", "/");
let lang = store.get("nexus_lang", "ar");
let busy = false, cat = "web";
let chatId = newId();
const t = (k) => T[lang][k];

function newId() {
  try { return crypto.randomUUID(); } catch { return String(Date.now()) + Math.random().toString(16).slice(2); }
}

// ---------- Markdown (safe subset) ----------
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
function inline(s) {
  return esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`\n]+)`/g, "<code>$1</code>")
    .replace(/\s*🔗\s*(https?:\/\/[^\s<]+)/g, (_, url) => `<div><a class="src" href="${url}" target="_blank" rel="noopener">${svg("link")}${t("source")} · ${new URL(url).hostname.replace("www.", "")}</a></div>`)
    .replace(/\n/g, "<br>");
}
function md(text) {
  return String(text).split(/```(\w*)\n?([\s\S]*?)```/g).map((part, i, all) => {
    if (i % 3 === 0) return inline(part.replace(/^\n+|\n+$/g, ""));
    if (i % 3 === 1) return "";
    return `<div class="code"><header><span>${esc(all[i - 1] || "code")}</span><button class="mini" data-copy-code>${svg("copy")}${t("copy")}</button></header><pre>${esc(part.trim())}</pre></div>`;
  }).join("");
}

// ---------- Rendering ----------
function applyLang() {
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-t]").forEach((el) => (el.textContent = t(el.dataset.t)));
  $("input").placeholder = t("placeholder");
  $("btn-lang").textContent = t("langBtn");
  document.querySelectorAll("[data-label]").forEach((el) => el.setAttribute("aria-label", t(el.dataset.label)));
  $("send").setAttribute("aria-label", t("send")); $("btn-lang").setAttribute("aria-label", lang === "ar" ? "English" : "العربية");
  applyTheme(document.documentElement.dataset.theme || "light");
  renderHello(); renderCats(); renderHistory(chatId); loadHome();
}
function renderCats() {
  $("cats").innerHTML = Object.keys(POPULAR).map((k) =>
    `<button class="pill ${k === cat ? "on" : ""}" role="tab" aria-selected="${k === cat}" data-cat="${k}">${svg(k)}${t("cats")[k]}</button>`).join("");
  const qs = POPULAR[cat].map(([ar, en]) => (lang === "ar" ? ar : en));
  const daily = typeof homeData !== "undefined" && homeData && homeData.code;
  if (cat === "code" && daily && !qs.includes(daily.question)) qs.unshift(daily.question);  // code of the day first
  $("examples").innerHTML = qs.slice(0, 4).map((q) =>
    `<button class="example" data-q="${esc(q)}">${svg(cat)}<span>${esc(q)}</span>${svg("arrow").replace("<svg", '<svg class="go"')}</button>`).join("");
}
function userBubble(text) { return `<div class="msg-user" dir="auto">${esc(text)}</div>`; }
function botBubble(answer, intent) {
  const skill = t("cats")[intent] || t("skills")[intent];
  return `<div class="msg-bot"><div class="bot-meta"><img class="avatar" src="/ui/logo.svg" alt="" />${t("brand")}${skill
    ? `<span class="badge" data-i="${esc(intent)}">${skill}</span>` : ""}</div><div class="bot-body">
    <div class="answer" dir="auto">${md(answer)}</div>
    <div class="actions"><button class="mini" data-copy-answer>${svg("copy")}${t("copy")}</button></div></div></div>`;
}
function setMode(chatting) {
  document.body.classList.toggle("chatting", chatting);
  (chatting ? $("dock") : $("home-slot")).prepend($("composer"));
}
const scrollDown = () => ($("main").scrollTop = $("main").scrollHeight);
function autosize() { const el = $("input"); el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 200) + "px"; }
function refreshSend() { $("send").disabled = busy || !$("input").value.trim(); }

async function send(text) {
  text = (text || "").trim();
  if (!text || busy) return;
  if (/سير[ةه] ذاتي|\bcv\b|\bresume\b/i.test(text) && text.length < 60) { $("input").value = ""; return openCV(); }
  setMode(true); toggleDrawer(false);
  busy = true;
  $("input").value = ""; autosize(); refreshSend();
  $("thread").insertAdjacentHTML("beforeend", userBubble(text));
  History.add(chatId, { role: "user", text });
  renderHistory(chatId);
  const pending = document.createElement("div");
  pending.className = "msg-bot pending";
  pending.innerHTML = `<div class="bot-meta"><img class="avatar" src="/ui/logo.svg" alt="" />${t("brand")}</div><div class="bot-body"><div class="typing"><i></i><i></i><i></i><span>${t("thinking")}</span></div></div>`;
  $("thread").appendChild(pending); scrollDown();
  try {
    const res = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" },
                                           body: JSON.stringify({ message: text, session: chatId }) });
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    pending.outerHTML = botBubble(data.answer, data.intent);
    History.add(chatId, { role: "bot", text: data.answer, intent: data.intent });
  } catch {
    pending.outerHTML = botBubble(t("error"), "");
  } finally {
    busy = false; refreshSend(); scrollDown(); $("input").focus();
  }
}

function openChat(id) {
  const chat = History.get(id);
  if (!chat) return;
  chatId = id;
  $("thread").innerHTML = chat.messages.map((m) => (m.role === "user" ? userBubble(m.text) : botBubble(m.text, m.intent))).join("");
  setMode(true); toggleDrawer(false); renderHistory(chatId); scrollDown();
}
function newChat() {
  chatId = newId(); $("thread").innerHTML = "";
  setMode(false); toggleDrawer(false); renderHistory(chatId); $("main").scrollTop = 0; $("input").focus();
}
function flash(btn) {
  const old = btn.innerHTML;
  btn.innerHTML = `${svg("check")}${t("copied")}`;
  setTimeout(() => (btn.innerHTML = old), 1500);
}

// ---------- Events ----------
document.addEventListener("click", (e) => {
  const el = (sel) => e.target.closest(sel);
  if (el("[data-del]")) {
    const id = el("[data-del]").dataset.del;
    History.remove(id); if (id === chatId) newChat(); return renderHistory(chatId);
  }
  if (el("[data-chat]")) return openChat(el("[data-chat]").dataset.chat);
  if (el("select") || el("label.city")) return;
  if (el("[data-q]")) return send(el("[data-q]").dataset.q);
  if (el("[data-cat]")) { cat = el("[data-cat]").dataset.cat; return renderCats(); }
  if (el("[data-close]")) return toggleDrawer(false);
  if (el("[data-copy-code]")) {
    const b = el("[data-copy-code]");
    navigator.clipboard?.writeText(b.closest(".code").querySelector("pre").textContent).then(() => flash(b));
  }
  if (el("[data-copy-answer]")) {
    const b = el("[data-copy-answer]");
    navigator.clipboard?.writeText(b.closest(".bot-body").querySelector(".answer").innerText).then(() => flash(b));
  }
});
document.addEventListener("keydown", (e) => {
  if ((e.key === "Enter" || e.key === " ") && e.target.matches(".tile[data-q]")) { e.preventDefault(); send(e.target.dataset.q); }
});
$("input").addEventListener("input", () => { autosize(); refreshSend(); });
$("input").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(e.target.value); } });
$("composer").onsubmit = (e) => { e.preventDefault(); send($("input").value); };
$("city").onchange = () => { store.set("nexus_city", $("city").value); loadHome(); };
document.querySelectorAll("[data-new]").forEach((b) => (b.onclick = newChat));
$("btn-theme").onclick = () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
$("btn-lang").onclick = () => { lang = lang === "ar" ? "en" : "ar"; store.set("nexus_lang", lang); applyLang(); };
$("btn-history").onclick = () => toggleDrawer(!document.body.classList.contains("drawer-open"));
$("scrim").onclick = () => toggleDrawer(false);

document.documentElement.dataset.theme = store.get("nexus_theme", matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
applyLang(); setMode(false); refreshSend();
if (sharedQuestion) send(sharedQuestion);
