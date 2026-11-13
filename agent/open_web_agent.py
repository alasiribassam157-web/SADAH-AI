"""[06] Open-web agent: recent news and information beyond Wikipedia, from trusted RSS feeds and an open,
key-less news search (Google News RSS).  Feeds are parsed with the standard library (xml.etree);
items are cleaned of HTML and ranked by how many of the question's words they contain.
"""
import html
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import httpx

from agent import kb
from agent.base_agent import AgentResult, BaseAgent, Task

HEADERS = {"User-Agent": "SADAH-Agent/2.0 (+https://sadah-app.vercel.app) python-httpx"}
SEARCH = {"ar": "https://news.google.com/rss/search?q={q}&hl=ar&gl=SA&ceid=SA:ar",
          "en": "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"}
FEEDS = {"ar": ["https://feeds.bbci.co.uk/arabic/rss.xml", "https://www.france24.com/ar/rss"],
         "en": ["https://feeds.bbci.co.uk/news/world/rss.xml", "https://www.aljazeera.com/xml/rss/all.xml"]}
_NEWS_WORDS = re.compile(r"آخر|اخر|أخبار|اخبار|مستجدات|عاجل|اليوم|الحين|حاليا|حالياً|latest|news|today|breaking|current",
                         re.I)
_TAG = re.compile(r"<[^>]+>")
MAX_ITEMS = 4


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", html.unescape(text or ""))).strip()


def parse_rss(xml_text: str) -> list[dict]:
    """[{title, summary, link, date, source}] from an RSS 2.0 document."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = []
    for it in root.iter("item"):
        title = clean(it.findtext("title"))
        if not title:
            continue
        host = (re.findall(r"//([^/]+)", it.findtext("link") or "") or [""])[0]
        source = clean(it.findtext("source")) or re.sub(r"^www\.", "", host)
        when = it.findtext("pubDate") or ""
        try:
            date = parsedate_to_datetime(when).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            date = ""
        items.append({"title": title, "summary": clean(it.findtext("description"))[:300],
                      "link": (it.findtext("link") or "").strip(), "date": date, "source": source})
    return items


def rank(items: list[dict], query: str) -> list[dict]:
    """Items that mention the question's words, best first, newest first on ties; duplicates removed."""
    wanted = set(kb.terms(_NEWS_WORDS.sub(" ", query)))
    seen, scored = set(), []
    for it in items:
        key = re.sub(r"\W+", "", it["title"])[:60]
        if key in seen:
            continue
        seen.add(key)
        words = set(kb.terms(f"{it['title']} {it['summary']}"))
        hits = len(wanted & words)
        if hits or not wanted:
            scored.append((hits / max(len(wanted), 1), it["date"], it))
    return [it for *_, it in sorted(scored, key=lambda x: (x[0], x[1]), reverse=True)]


class OpenWebAgent(BaseAgent):
    name = "OpenWeb"
    sector = "المعرفة والبحث"
    intents = frozenset({"web"})
    keywords = _NEWS_WORDS.pattern
    timeout = 7.0

    def fetch(self, url: str) -> list[dict]:
        try:
            with httpx.Client(timeout=5, headers=HEADERS, follow_redirects=True) as http:
                return parse_rss(http.get(url).text)
        except httpx.HTTPError:
            return []

    def handle(self, task: Task) -> AgentResult:
        query = re.sub(r"[؟?!.]+$", "", _NEWS_WORDS.sub(" ", task.text)).strip() or task.text
        urls = [SEARCH[task.lang].format(q=quote_plus(query))] + FEEDS[task.lang]
        self.step("سَداة تبحث في الأخبار والمصادر المفتوحة", f"«{query}» · {len(urls)} مصادر RSS")
        with ThreadPoolExecutor(max_workers=len(urls)) as pool:
            items = [it for found in pool.map(self.fetch, urls) for it in found]
        best = rank(items, query)[:MAX_ITEMS]
        if not best:
            return self.fail(f"لم أجد أخبارًا حديثة عن «{query}»")
        self.step(f"وجدتُ {len(best)} خبرًا مرتبطًا", " · ".join(b["source"] for b in best), confidence=0.65)
        head = f"📰 **آخر ما وجدته عن «{query}»:**" if task.lang == "ar" else f"📰 **Latest on «{query}»:**"
        lines = [f"• **{b['title']}**" + (f" — {b['source']}" if b["source"] and b["source"] not in b["title"] else "")
                 + (f" ({b['date']})" if b["date"] else "") for b in best]
        note = "ℹ️ عناوين من مصادر إخبارية مفتوحة؛ افتح الرابط للتفاصيل." if task.lang == "ar" else \
            "ℹ️ Headlines from open news sources; open a link for details."
        links = [b["link"] for b in best if b["link"].startswith("http")]
        return self.ok("\n".join([head, *lines, "", note]), 0.65, links, {"items": best}, entity=query)
