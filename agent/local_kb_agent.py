"""[03] Local knowledge agent: BM25 search over the offline library (data/kb/kb.jsonl.gz, kb.py).

No network: answers in milliseconds, and also hands ranked paragraphs to the synthesis agent.
"""
from agent import kb
from agent.base_agent import AgentResult, BaseAgent, Task
from agent.research import answer_length, to_topic

COVERAGE_FLOOR = 0.6   # a loose paragraph must contain most of the question's words to be used
LOOSE_CONFIDENCE = 0.45  # below the supervisor's 0.5 bar: Wikipedia is tried first, synthesis may still use it


class LocalKBAgent(BaseAgent):
    name = "LocalKB"
    sector = "المعرفة والبحث"
    intents = frozenset({"web"})
    keywords = r"ما هو|ما هي|عرف|اشرح|what is|define|explain"
    timeout = 4.0

    def passages(self, query: str, lang: str, k: int = 6) -> list[dict]:
        """The k best paragraphs for a query: {title, heading, text, url, score, coverage}."""
        ix = kb._get()
        if not ix["n"]:
            return []
        words = kb.terms(query)
        wanted = set(words)
        out = []
        for score, i in kb._bm25(ix, words, lang)[:k]:
            art_i, heading, text, tf = ix["paras"][i]
            art = ix["arts"][art_i]
            coverage = sum(t in tf for t in wanted) / max(len(wanted), 1)
            out.append({"title": art["title"], "heading": heading, "text": text, "url": art["url"],
                        "score": round(score, 3), "coverage": round(coverage, 2)})
        return out

    def handle(self, task: Task) -> AgentResult:
        topic = to_topic(task.text)
        self.step("سَداة تبحث في المكتبة المحلية", f"الموضوع: {topic} · خوارزمية BM25")
        hit = kb.lookup(task.text, topic, task.lang, answer_length(task.text))
        if hit:
            title, text, url = hit
            self.step("وجدتُ المقالة المطابقة", title, confidence=0.8)
            return self.ok(f"**{title}**\n\n{text}", 0.8, [url], {"title": title, "text": text}, entity=title)
        best = next(iter(self.passages(task.text, task.lang, 1)), None)
        if best and best["coverage"] >= COVERAGE_FLOOR and len(set(kb.terms(task.text))) >= 2:
            title = f"{best['title']} · {best['heading']}" if best["heading"] else best["title"]
            text = " ".join(best["text"].split(". ")[:3])
            self.step("وجدتُ فقرة قريبة من السؤال", f"{title} · تغطية {best['coverage']:.0%}",
                      confidence=LOOSE_CONFIDENCE)
            data = {"title": title, "text": best["text"]}
            return self.ok(f"**{title}**\n\n{text}", LOOSE_CONFIDENCE, [best["url"]], data, entity=best["title"])
        return self.fail("الموضوع غير موجود في المكتبة المحلية")
