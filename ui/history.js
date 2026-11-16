// Conversation drawer: chats saved in this browser only (localStorage), one identity (Royal Obsidian), so there is no theme control.
const store = {
  get: (k, d) => { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
};
const MAX_CHATS = 40;
// One-time move of this browser's saved data from the pre-SADAH key names, so nobody loses chats, language or city.
for (const [from, to] of [["nexus_chats", "sadah_chats"], ["nexus_lang", "sadah_lang"], ["nexus_city", "sadah_city"]]) {
  if (store.get(to, null) === null && store.get(from, null) !== null) store.set(to, store.get(from, ""));
}

const History = {
  all() {
    try { return JSON.parse(store.get("sadah_chats", "[]")); } catch { return []; }
  },
  save(chats) { store.set("sadah_chats", JSON.stringify(chats.slice(0, MAX_CHATS))); },
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

function toggleDrawer(open) { document.body.classList.toggle("drawer-open", open); }
