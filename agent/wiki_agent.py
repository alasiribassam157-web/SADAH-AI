"""[04] Wikipedia agent: reads Arabic (or English) Wikipedia directly, independently of the library.

Two roles:
  answer  — «ما هو …» questions: a short, clean summary of the right article
  witness — fact questions: the subject's whole introduction, so the critic can check Wikidata's value
"""
import re

import httpx

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.facts import match_relation
from agent.research import HEADERS, _english_fallback, _query, _strip_al, answer_length, intro, to_topic

_CLUTTER = re.compile(r"\s*\([^()]*\)")
_DIACRITICS = re.compile(r"[ً-ْٰـ]")
# words that sit in the sentence stating each property
_PROP_WORDS = {"P36": r"عاصم|capital", "P1082": r"سكان|نسمة|population|inhabitants", "P2046": r"مساح|كم²|كم2|كيلومتر|area|km",
               "P38": r"عمل|currency", "P37": r"لغ|language", "P571": r"تأسس|أسس|founded|established",
               "P569": r"ولد|وُلد|born", "P19": r"ولد|وُلد|born", "P112": r"أسس|مؤسس|founded", "P2048": r"ارتفاع|طول|height",
               "P2044": r"ارتفاع|متر|elevation"}


def clean(text: str) -> str:
    text = _CLUTTER.sub("", _DIACRITICS.sub("", text))
    return re.sub(r"\s{2,}", " ", text).strip()


def relevant(text: str, prop: str, limit: int = 2) -> str:
    """The sentences of an introduction that talk about the property (or its first sentences)."""
    sentences = re.split(r"(?<=[.!؟?])\s+", text)
    words = _PROP_WORDS.get(prop.split("|")[0])
    hits = [s for s in sentences if words and re.search(words, s, re.IGNORECASE)]
    return " ".join((hits or sentences)[:limit])


class WikiAgent(BaseAgent):
    name = "Wiki"
    sector = "المعرفة والبحث"
    intents = frozenset({"web"})
    keywords = r"ويكيبيديا|wikipedia|من هو|من هي|who is|who was"
    timeout = 7.0

    def search(self, question: str, lang: str, sentences: int) -> tuple[str, str, str] | None:
        """(title, text, url) straight from Wikipedia: exact title, title without «ال», then search."""
        topic = to_topic(question)
        attempts = [{"titles": topic}]
        if lang == "ar":
            attempts.append({"titles": _strip_al(topic)})
        attempts.append({"generator": "search", "gsrsearch": topic, "gsrlimit": 1})
        if topic != question:
            attempts.append({"generator": "search", "gsrsearch": question, "gsrlimit": 1})
        with httpx.Client(timeout=6, headers=HEADERS, follow_redirects=True) as http:
            page = next((p for params in attempts if (p := _query(http, lang, params, sentences))), None)
            if not page and lang == "ar":
                page = _english_fallback(http, topic, sentences)
        return (page["title"], clean(page["extract"]), page.get("fullurl", "")) if page else None

    def handle(self, task: Task) -> AgentResult:
        rel = match_relation(task.text)
        try:
            if rel:
                return self._witness(task, rel[0], rel[1])
            self.step("سَداة تبحث في ويكيبيديا", to_topic(task.text))
            found = self.search(task.text, task.lang, answer_length(task.text))
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            return self.fail(f"تعذّر الاتصال بويكيبيديا: {exc}")
        if not found:
            return self.fail("لم أجد مقالة مناسبة في ويكيبيديا")
        title, text, url = found
        self.step("وجدتُ المقالة", title, confidence=0.7)
        return self.ok(f"**{title}**\n\n{text}", 0.7, [url], {"title": title, "text": text}, entity=title)

    def _witness(self, task: Task, prop: str, entity: str) -> AgentResult:
        """Read the subject's whole introduction; answer with the sentences about the property."""
        self.step("سَداة تقرأ مقالة الكيان في ويكيبيديا كشاهد مستقل", entity)
        page = intro(entity, task.lang, timeout=5)
        if not page:
            return self.fail(f"لا توجد مقالة عن «{entity}»")
        title, text, url = page
        text = clean(text)
        part = relevant(text, prop)
        self.step("قرأتُ المقدمة كاملة", f"{title} · {len(text)} حرف", confidence=0.6)
        return self.ok(f"**{title}**\n\n{part}", 0.6, [url], {"title": title, "text": text}, entity=title)
