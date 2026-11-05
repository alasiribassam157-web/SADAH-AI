// Conversation drawer: chats saved in this browser only (localStorage), plus theme control.
const store = {
  get: (k, d) => { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};
const MAX_CHATS = 40;

const History = {
  all() {
    try { return JSON.parse(store.get("nexus_chats", "[]")); } catch { return []; }
  },
  save(chats) { store.set("nexus_chats", JSON.stringify(chats.slice(0, MAX_CHATS))); },
  get(id) { return this.all().find((c) => c.id === id); },
  // Append one message to a conversation, creating it (titled by its first question) if needed.
  add(id, message) {
    const chats = this.all();
    let chat = chats.find((c) => c.id === id);
    if (!chat) {
      chat = { id, title: message.text.slice(0, 60), updated: Date.now(), messages: [] };
      chats.unshift(chat);
    }
    chat.messages.push(message);
    chat.updated = Date.now();
    chats.sort((a, b) => b.updated - a.updated);
    this.save(chats);
  },
  remove(id) { this.save(this.all().filter((c) => c.id !== id)); },
};

function renderHistory(activeId) {
  const chats = History.all();
  const startOfDay = new Date().setHours(0, 0, 0, 0);
  const row = (c) => `<div class="hist-row ${c.id === activeId ? "on" : ""}" data-chat="${c.id}">
      ${svg("chat")}<span dir="auto">${esc(c.title)}</span>
      <button class="hist-del" data-del="${c.id}" aria-label="${t("del")}">×</button></div>`;
  const today = chats.filter((c) => c.updated >= startOfDay), earlier = chats.filter((c) => c.updated < startOfDay);
  $("history").innerHTML = !chats.length ? `<p class="hist-empty">${t("empty")}</p>`
    : (today.length ? `<p class="hist-group">${t("today")}</p>${today.map(row).join("")}` : "")
      + (earlier.length ? `<p class="hist-group">${t("earlier")}</p>${earlier.map(row).join("")}` : "");
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  store.set("nexus_theme", theme);
  $("btn-theme").title = theme === "dark" ? t("light") : t("dark");
}

function toggleDrawer(open) { document.body.classList.toggle("drawer-open", open); }
