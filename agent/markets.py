"""Live markets: gold & silver (gold-api.com) and crypto (CoinGecko). Free, no keys.

Prices are cached for 5 minutes.  Quotes only: no forecasts or investment advice.
"""
import re
import time

import httpx

from agent.tools import ToolResult

HEADERS = {"User-Agent": "SADAH-Agent/1.0 (https://github.com/alasiribassam157-web/SADAH-AI)"}
OUNCE_G = 31.1035
USD_SAR = 3.75                     # the riyal is pegged to the dollar
KARATS = (24, 22, 21, 18)
METALS = {"XAU": (["ذهب", "الذهب", "دهب", "gold"], "الذهب", "Gold"),
          "XAG": (["فضة", "الفضة", "فضه", "الفضه", "silver"], "الفضة", "Silver")}
COINS = {
    "bitcoin": (["بيتكوين", "بتكوين", "البيتكوين", "البتكوين", "bitcoin", "btc"], "بيتكوين", "Bitcoin"),
    "ethereum": (["ايثيريوم", "إيثيريوم", "ايثريوم", "الايثيريوم", "ethereum", "eth"], "إيثيريوم", "Ethereum"),
    "binancecoin": (["بينانس", "bnb", "binance coin"], "BNB", "BNB"),
    "solana": (["سولانا", "solana", "sol"], "سولانا", "Solana"),
    "ripple": (["ريبل", "xrp", "ripple"], "ريبل XRP", "XRP"),
    "dogecoin": (["دوجكوين", "دوج كوين", "dogecoin", "doge"], "دوجكوين", "Dogecoin"),
    "cardano": (["كاردانو", "cardano", "ada"], "كاردانو", "Cardano"),
    "tether": (["تيثر", "tether", "usdt"], "تيثر USDT", "Tether"),
}
_CACHE: dict[str, tuple[float, dict]] = {}
_CRYPTO_WORDS = re.compile(r"عملات رقمية|العملات الرقمية|عملات مشفرة|كريبتو|crypto", re.I)


def _has(text: str, words: list[str]) -> bool:
    # Arabic words take attached prefixes: والذهب، بالبيتكوين، للفضة
    return any(re.search(rf"(?<!\w){'(?:و|ب|ال|وال|بال|لل)?' if '؀' <= w[0] <= 'ۿ' else ''}"
                         rf"{re.escape(w)}(?!\w)", text, re.I) for w in words)


def handles(question: str) -> bool:
    return (any(_has(question, w) for w, _, _ in METALS.values())
            or any(_has(question, w) for w, _, _ in COINS.values()) or bool(_CRYPTO_WORDS.search(question)))


PRICE = re.compile(r"سعر|اسعار|أسعار|بكم|كم|قيمة|قيمه|غرام|جرام|عيار|اونصة|أونصة|الحين|اليوم|"
                    r"price|prices|cost|worth|value|quote|today|now|ounce|gram|how much", re.I)


def asks_price(question: str) -> bool:
    """«كم سعر الذهب» / «bitcoin price» — but not «ما هو البيتكوين» (that is a knowledge question)."""
    return handles(question) and bool(PRICE.search(question))


def _get(url: str, params: dict | None = None) -> dict:
    key = url + str(params)
    stamp, data = _CACHE.get(key, (0, {}))
    if time.time() - stamp > 300:
        data = httpx.get(url, params=params, timeout=10, headers=HEADERS).json()
        _CACHE[key] = (time.time(), data)
    return data


def _metal(code: str, ar: bool) -> str:
    usd = float(_get(f"https://api.gold-api.com/price/{code}")["price"])
    gram_sar = usd * USD_SAR / OUNCE_G
    _, name_ar, name_en = METALS[code]
    if ar:
        lines = [f"**سعر {name_ar} الآن:** {usd:,.2f} دولار للأونصة"]
        if code == "XAU":
            lines += [f"• عيار {k}: **{gram_sar * k / 24:,.2f} ريال** للجرام" for k in KARATS]
        else:
            lines.append(f"• الجرام: **{gram_sar:,.2f} ريال**")
    else:
        lines = [f"**{name_en} now:** ${usd:,.2f} per ounce"]
        if code == "XAU":
            lines += [f"• {k}K: **{gram_sar * k / 24:,.2f} SAR** per gram" for k in KARATS]
        else:
            lines.append(f"• Per gram: **{gram_sar:,.2f} SAR**")
    return "\n".join(lines)


def _crypto(ids: list[str], ar: bool) -> str:
    data = _get("https://api.coingecko.com/api/v3/simple/price",
                {"ids": ",".join(ids), "vs_currencies": "usd", "include_24hr_change": "true"})
    lines = []
    for cid in ids:
        if cid not in data:
            continue
        usd, change = data[cid]["usd"], data[cid].get("usd_24h_change") or 0
        arrow = "🟢 +" if change >= 0 else "🔴 "
        name = COINS[cid][1] if ar else COINS[cid][2]
        sar = f" ({usd * USD_SAR:,.2f} ريال)" if ar else f" ({usd * USD_SAR:,.2f} SAR)"
        tail = "خلال 24 ساعة" if ar else "in 24h"
        lines.append(f"• **{name}:** ${usd:,.2f}{sar} · {arrow}{change:.2f}% {tail}")
    return "\n".join(lines)


def quote(question: str) -> ToolResult:
    ar = bool(re.search(r"[؀-ۿ]", question))
    metals = [c for c, (w, _, _) in METALS.items() if _has(question, w)]
    coins = [c for c, (w, _, _) in COINS.items() if _has(question, w)]
    if not metals and not coins:   # "اسعار العملات الرقمية" → the main coins
        coins = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
    try:
        parts = [_metal(c, ar) for c in metals]
        if coins:
            parts.append(("**العملات الرقمية:**\n" if ar else "**Crypto:**\n") + _crypto(coins, ar))
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return ToolResult(False, f"Market data error: {exc}")
    note = ("⚠️ أسعار لحظية للمعلومة فقط، وليست نصيحة استثمارية." if ar
            else "⚠️ Live quotes for information only, not investment advice.")
    src = []
    if metals:
        src.append("https://gold-api.com")
    if coins:
        src.append("https://www.coingecko.com")
    links = "\n".join("🔗 " + s for s in src)
    return ToolResult(True, "\n\n".join(parts) + f"\n\n{note}\n\n{links}")
