// Home: greeting, Hijri date, city picker and the "today" board (weather, next prayer, dollar).
let homeData = null;

function cityName() {
  const pair = CITIES[Number(store.get("nexus_city", "0"))] || CITIES[0];
  return lang === "ar" ? pair[0] : pair[1];
}

// «الخميس ١٤ جمادى الأولى ١٤٤٨ هـ» from the browser's Umm al-Qura calendar
function hijriToday() {
  try {
    return new Intl.DateTimeFormat(lang === "ar" ? "ar-SA-u-ca-islamic-umalqura" : "en-u-ca-islamic-umalqura",
      { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(new Date());
  } catch { return new Date().toLocaleDateString(); }
}

function renderHello() {
  $("hello").textContent = new Date().getHours() < 12 ? t("morning") : t("evening");
  $("hijri").textContent = hijriToday();
  $("city").innerHTML = CITIES.map(([ar, en], i) => `<option value="${i}">${esc(lang === "ar" ? ar : en)}</option>`).join("");
  $("city").value = store.get("nexus_city", "0");
}

// «بعد ساعتين و10 دقائق» / "in 2h 10m"
function countdown(h, m) {
  if (lang !== "ar") return `in ${h ? `${h}h ` : ""}${m}m`;
  const hours = h === 0 ? "" : h === 1 ? "ساعة" : h === 2 ? "ساعتين" : h <= 10 ? `${h} ساعات` : `${h} ساعة`;
  const mins = m === 0 ? "" : m === 1 ? "دقيقة" : m === 2 ? "دقيقتين" : m <= 10 ? `${m} دقائق` : `${m} دقيقة`;
  const parts = [hours, mins].filter(Boolean).join(" و");
  return parts ? `بعد ${parts}` : "الآن";
}

const label = (icon, text) => `<span class="lbl">${svg(icon)}${text}</span>`;
const missing = () => `<span class="na">${t("unavailable")}</span>`;
function cell(id, icon, text, body, q) {
  $(id).innerHTML = label(icon, text) + body;
  if (q) $(id).dataset.q = q; else delete $(id).dataset.q;
}

function renderTiles() {
  const d = homeData, city = d ? d.city : cityName();
  const w = d && d.weather, p = d && d.prayer, fx = d && d.usd_sar;
  cell("tile-weather", "weather", t("weatherNow"), w
    ? `<b class="val">${w.temp}°</b><span class="sub">${esc(city)} · ${esc(w.desc)} · <bdi>↑${w.high}° ↓${w.low}°</bdi></span>` : missing(),
    lang === "ar" ? `كيف الجو في ${city}؟` : `Weather in ${city}`);
  cell("tile-prayer", "prayer", t("nextPrayer"), p
    ? `<b class="val gold">${esc(p.name)}</b><span class="sub"><bdi>${esc(p.time)}</bdi> · ${countdown(p.in_hours, p.in_minutes)}</span>` : missing(),
    lang === "ar" ? `مواقيت الصلاة في ${city}` : `Prayer times in ${city}`);
  cell("tile-fx", "currency", t("dollar"), fx
    ? `<b class="val">${fx.toFixed(2)}</b><span class="sub">${t("sar")} · <bdi>1 USD</bdi></span>` : missing(),
    lang === "ar" ? "كم سعر الدولار بالريال؟" : "Convert 1 USD to SAR");
}

async function loadHome() {
  [["tile-weather", "weather", "weatherNow"], ["tile-prayer", "prayer", "nextPrayer"], ["tile-fx", "currency", "dollar"]].forEach(([id, icon, k]) =>
    cell(id, icon, t(k), `<span class="shimmer"></span><span class="shimmer short"></span>`));
  try {
    const res = await fetch(`/api/home?city=${encodeURIComponent(cityName())}&lang=${lang}`);
    homeData = res.ok ? await res.json() : null;
  } catch { homeData = null; }
  renderTiles();
  if (typeof renderCats === "function") renderCats();  // code of the day joins the code ideas
}
