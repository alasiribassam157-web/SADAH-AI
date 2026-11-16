"""Live-data skills: weather (Open-Meteo), exchange rates (open.er-api.com), date/time + Hijri (aladhan)."""
import os
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from agent.currencies import CURRENCIES
from agent.tools import ToolResult

TZ = ZoneInfo(os.getenv("SADAH_TZ", "Asia/Riyadh"))
HEADERS = {"User-Agent": "SADAH-Agent/1.0 (https://github.com/alasiribassam157-web/SADAH-AI)"}
_WMO = [((0,), "صافٍ ☀️", "Clear ☀️"), ((1, 2), "غائم جزئياً ⛅", "Partly cloudy ⛅"), ((3,), "غائم ☁️", "Overcast ☁️"),
        ((45, 48), "ضباب 🌫", "Fog 🌫"), ((51, 53, 55, 56, 57), "رذاذ 🌦", "Drizzle 🌦"),
        ((61, 63, 65, 66, 67, 80, 81, 82), "مطر 🌧", "Rain 🌧"), ((71, 73, 75, 77, 85, 86), "ثلج ❄️", "Snow ❄️"),
        ((95, 96, 99), "عاصفة رعدية ⛈", "Thunderstorm ⛈")]
# Tried in order: "... في جدة" / "... in Tokyo", then "طقس دبي", then "Cairo weather".
_CITY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in (
    r"(?:\s|^)(?:في|بـ|in|at|for)\s+(.+)$", r"(?:طقس|الطقس|الجو|weather|temperature)\s+(.+)$",
    r"^(.+?)\s+(?:weather|forecast)$")]
_NOISE = re.compile(r"\b(اليوم|الحين|الان|الآن|today|now|right now|بكرة|tomorrow)\b|[؟?!.]", re.IGNORECASE)


def _lang(text: str) -> str:
    return "ar" if re.search(r"[؀-ۿ]", text) else "en"


def weather(question: str) -> ToolResult:
    lang = _lang(question)
    text = " ".join(_NOISE.sub(" ", question).split())
    match = next((m for p in _CITY_PATTERNS if (m := p.search(text))), None)
    city = (match.group(1).strip() if match else "") or ("الرياض" if lang == "ar" else "Riyadh")
    try:
        with httpx.Client(timeout=15, headers=HEADERS) as http:
            places = http.get("https://geocoding-api.open-meteo.com/v1/search",
                              params={"name": city, "count": 1, "language": lang}).json().get("results")
            if not places:
                return ToolResult(False, f"ما لقيت مدينة باسم «{city}»." if lang == "ar" else f"City not found: {city}")
            p = places[0]
            w = http.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": p["latitude"], "longitude": p["longitude"], "timezone": "auto", "forecast_days": 1,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max"}).json()
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return ToolResult(False, f"Weather service error: {exc}")
    c, d = w["current"], w["daily"]
    desc = next((ar if lang == "ar" else en for codes, ar, en in _WMO if c["weather_code"] in codes), "")
    rain = (d.get("precipitation_probability_max") or [None])[0]
    if lang == "ar":
        text = (f"**{p['name']}** الآن: **{round(c['temperature_2m'])}°م** · {desc}\n"
                f"العظمى {round(d['temperature_2m_max'][0])}° · الصغرى {round(d['temperature_2m_min'][0])}°"
                f"{f' · احتمال المطر {rain}%' if rain is not None else ''}\n"
                f"الرطوبة {c['relative_humidity_2m']}% · الرياح {round(c['wind_speed_10m'])} كم/س")
    else:
        text = (f"**{p['name']}** now: **{round(c['temperature_2m'])}°C** · {desc}\n"
                f"High {round(d['temperature_2m_max'][0])}° · Low {round(d['temperature_2m_min'][0])}°"
                f"{f' · Rain chance {rain}%' if rain is not None else ''}\n"
                f"Humidity {c['relative_humidity_2m']}% · Wind {round(c['wind_speed_10m'])} km/h")
    return ToolResult(True, f"{text}\n\n🔗 https://open-meteo.com", entity=p["name"])


_ALIASES = sorted(((a, code) for code, (_, _, al) in CURRENCIES.items() for a in al), key=lambda x: -len(x[0]))
_RATES: dict[str, tuple[float, dict]] = {}


def _find(text: str) -> list[tuple[int, int, str]]:
    low, found = text.lower(), []
    for alias, code in _ALIASES:
        # Arabic words take attached prefixes: الدولار، بالريال، والريال، للدولار
        prefix = r"(?:ال|بال|وال|لل|ب)?" if re.match(r"[؀-ۿ]", alias) else ""
        pattern = rf"(?<![\w]){prefix}{re.escape(alias)}(?![\w])" if alias[0].isalnum() else re.escape(alias)
        for m in re.finditer(pattern, low):
            if not any(s <= m.start() < e for s, e, _ in found):
                found.append((m.start(), m.end(), code))
    return sorted(found)


def find_currencies(text: str) -> list[str]:
    return [code for _, _, code in _find(text)]


def currency(question: str) -> ToolResult:
    lang = _lang(question)
    question = question.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    found = _find(question)
    codes = list(dict.fromkeys(code for _, _, code in found))
    if not codes:
        return ToolResult(False, "حدد العملة، مثلاً: كم سعر الدولار بالريال" if lang == "ar" else "Name a currency, e.g. 100 USD to EUR")
    amount_m = re.search(r"\d+(?:[.,]\d+)?", question)
    amount = float(amount_m.group().replace(",", ".")) if amount_m else 1.0
    src = codes[0]
    if amount_m:  # «how many euros for 500 dollars»: the currency right after the number is the source
        after = [code for start, _, code in found if start >= amount_m.end()]
        src = after[0] if after else src
    others = [c for c in codes if c != src]
    dst = others[0] if others else ("SAR" if src != "SAR" else "USD")
    try:
        stamp, rates = _RATES.get(src, (0, {}))
        if time.time() - stamp > 3600:
            data = httpx.get(f"https://open.er-api.com/v6/latest/{src}", timeout=10, headers=HEADERS).json()
            rates = data["rates"]
            _RATES[src] = (time.time(), rates)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return ToolResult(False, f"Exchange-rate service error: {exc}")
    value = amount * rates[dst]
    i = 0 if lang == "ar" else 1
    shown = f"{amount:g}"
    text = f"**{shown} {CURRENCIES[src][i]} = {value:,.2f} {CURRENCIES[dst][i]}**"
    note = "الأسعار تتحدّث كل يوم" if lang == "ar" else "Rates update daily"
    return ToolResult(True, f"💱 {text}\n{note}\n\n🔗 https://www.exchangerate-api.com")


AR_DAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def date_time(question: str) -> ToolResult:
    lang = _lang(question)
    now = datetime.now(TZ)
    hijri = ""
    try:
        h = httpx.get(f"https://api.aladhan.com/v1/gToH/{now:%d-%m-%Y}", timeout=8, headers=HEADERS).json()["data"]["hijri"]
        hijri = f"{int(h['day'])} {h['month']['ar']} {h['year']} هـ" if lang == "ar" else \
            f"{int(h['day'])} {h['month']['en']} {h['year']} AH"
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    if lang == "ar":
        clock = now.strftime("%I:%M").lstrip("0") + (" ص" if now.hour < 12 else " م")
        text = (f"🕐 الساعة الآن **{clock}** (توقيت {TZ.key.split('/')[-1].replace('Riyadh', 'الرياض')})\n"
                f"📅 **{AR_DAYS[now.weekday()]} {now.day} {AR_MONTHS[now.month - 1]} {now.year}**")
        return ToolResult(True, text + (f"\n🌙 **{hijri}**" if hijri else ""))
    text = f"🕐 It's **{now:%I:%M %p}** ({TZ.key})\n📅 **{now:%A, %B} {now.day}, {now.year}**"
    return ToolResult(True, text + (f"\n🌙 **{hijri}**" if hijri else ""))
