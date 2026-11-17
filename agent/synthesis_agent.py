"""[08] Synthesis agent: open questions («كيف»، «لماذا»، «قارن»، «حلّل») answered from real sources.

Axes come from the question's nominal core (agent/topic.py), so «كيف ابني بيت» is searched as «بناء
بيت», «بيت» and «بناء»; paragraphs come from the offline library and Wikipedia in parallel, ranked by
TextRank and woven by the stylist, which adds nothing.  Numeric comparisons go to Wikidata.
"""
import math
import re
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from agent import arabic, causal, composer, kb, topic as topics
from agent.base_agent import AgentResult, BaseAgent, Task
from agent.local_kb_agent import LocalKBAgent
from agent.research import to_topic
from agent.stylist_agent import weave
from agent.wiki_agent import WikiAgent

_VERBS = re.compile(r"^(?:تعمل|يعمل|تحدث|يحدث|حدثت|حدث|تتكون|يتكون|تؤثر|يؤثر|نشأت|نشأ|يتم|تتم|تكون|يكون|"
                    r"ظهرت|ظهر|سقطت|سقط|أسباب|اسباب|أهمية|اهمية|فوائد|أضرار|اضرار|does|do|did|is|are)\s+", re.I)
_LEAD = re.compile(r"^(?:حلل|حلّل|اشرح|وضح|وضّح|قارن بين|مقارنة بين|الفرق بين|analy[sz]e|explain|compare)\s+", re.I)
_TRAIL = re.compile(r"\s+(?:مهم|مهمة|مفيد|مفيدة|خطير|خطيرة|important|useful|dangerous)$", re.I)
_KIND = [("compare", r"قارن|مقارنة|الفرق بين|ايهما|أيهما|compare|difference between|versus|\bvs\b"),
         ("why", r"لماذا|ليش|ليه|أسباب|اسباب|why|causes?"), ("how", r"كيف|ازاي|how"),
         ("analyze", r"حلل|حلّل|تحليل|أهمية|اهمية|تأثير|analy[sz]e|impact")]
PER_AXIS, MAX_POINTS = 3, 7      # sentences kept per axis / in total


def on_axis(query: str, sentence: str) -> bool:   # «البيوت» answers «بناء بيت»: a shared root is enough
    return bool(arabic.roots(query) & arabic.roots(sentence))

def kind_of(question: str) -> str:
    return next((k for k, pat in _KIND if re.search(pat, question, re.I)), "define")


def axes(question: str, kind: str) -> tuple[str, list[tuple[str, str]]]:
    """(topic, [(heading, search query)]) — the angles the answer must cover."""
    if kind == "compare":
        rest = _LEAD.sub("", question.strip(" ؟?"))
        pair = re.split(r"\s+(?:و(?=\S)|and\s+|vs\.?\s+|versus\s+|أم\s+|ام\s+|or\s+)", rest, maxsplit=1, flags=re.I)
        if len(pair) == 2 and all(x.strip() for x in pair):
            a, b = (x.strip() for x in pair)
            return f"«{a}» و«{b}»", [(a, a), (b, b)]
    topic, previous = to_topic(question), ""
    while topic != previous:  # «حلل أهمية الذكاء الاصطناعي» -> «الذكاء الاصطناعي»
        previous, topic = topic, _TRAIL.sub("", _VERBS.sub("", _LEAD.sub("", topic))).strip()
    wide = topics.queries(question)          # «كيف ابني بيت» -> «بناء بيت», «بيت», «بناء»
    topic = topic or question
    if kind in ("how", "define") and wide:   # a request verb becomes the noun it asks about
        topic = wide[0]
    if kind == "why":   # one causal axis: the search ladder inside the agents widens it on its own
        return topic, [("الأسباب", topic)]
    if kind == "analyze":
        return topic, [("", topic), ("التأثير والأهمية", f"تأثير {topic}")]
    return topic, [("", q) for q in wide[:3]]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!؟?؛])\s+", re.sub(r"\s+", " ", text))
    return [p.strip() for p in parts if 40 <= len(p.strip()) <= 400]


def textrank(items: list[str], query: list[str], damping: float = 0.85, boost: np.ndarray | None = None) -> np.ndarray:
    """Score = 0.5 × centrality in the sentence-similarity graph + 0.5 × relevance to the question,
    times `boost` (2.5 for causal sentences in «why» questions)."""
    bags = [set(kb.terms(s)) for s in items]
    n = len(items)
    sim = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            if bags[i] and bags[j]:
                sim[i, j] = sim[j, i] = len(bags[i] & bags[j]) / (math.log(len(bags[i]) + 1) + math.log(len(bags[j]) + 1))
    rows = sim.sum(axis=1, keepdims=True)
    trans = np.divide(sim, rows, out=np.full_like(sim, 1.0 / n), where=rows > 0)
    rank = np.full(n, 1.0 / n)
    for _ in range(40):
        rank = (1 - damping) / n + damping * trans.T @ rank
    df = {t: sum(t in b for b in bags) for t in set(query)}
    rel = np.array([sum(math.log(1 + n / (1 + df[t])) for t in set(query) if t in b) for b in bags])
    norm = (lambda v: v / v.max() if v.max() > 0 else v)
    score = 0.5 * norm(rank) + 0.5 * norm(rel)
    return score if boost is None else score * boost


class SynthesisAgent(BaseAgent):
    name = "Synthesis"
    sector = "الاستنتاج والصياغة"
    intents = frozenset({"web"})
    keywords = r"^(?:كيف|لماذا|ليش|حلل|قارن)|الفرق بين|أسباب|^(?:how|why|compare|analy[sz]e)"
    timeout = 9.0

    def __init__(self, local: LocalKBAgent | None = None, wiki: WikiAgent | None = None):
        super().__init__()
        self.local, self.wiki = local or LocalKBAgent(), wiki or WikiAgent()

    def gather(self, query: str, lang: str, why: bool = False, question: str = "") -> list[tuple[str, str]]:
        """[(sentence, source url)] for one axis: library paragraphs plus the Wikipedia article.  A
        library paragraph can be about anything, so only sentences covering the question are taken."""
        found = []
        for q in ([query, causal.expand(query, lang)] if why else [query]):
            found += [(s, p["url"]) for p in self.local.passages(q, lang, 4) if p["coverage"] >= 0.6
                      for s in sentences(p["text"]) if topics.covers(question or query, s)]
        try:
            page = self.wiki.search(query, lang, 10)
        except Exception:  # Wikipedia down: the library alone still answers
            page = None
        found += [(s, page[2]) for s in sentences(page[1])] if page else []
        return list(dict.fromkeys(found))

    def handle(self, task: Task) -> AgentResult:
        kind = kind_of(task.text)
        if kind == "compare" and any(re.search(p, task.text, re.I) for p, *_ in composer.PROPERTIES):
            self.step("مقارنة رقمية: سَداة تجلب القيمتين من Wikidata")
            res = composer.compare(task.text)
            if not res.ok:   # a numeric comparison without both numbers: no sentence-picking guesswork
                return self.fail(res.output)
            url = re.findall(r"https?://\S+", res.output)
            return self.ok(res.output, 0.85, url, {"kind": kind}, entity=res.entity)
        topic, plan = axes(task.text, kind)
        count = {1: "محور واحد", 2: "محورين"}.get(len(plan), f"{len(plan)} محاور")
        self.step(f"سَداة قسّمت السؤال إلى {count}", " | ".join(q for _, q in plan))
        with ThreadPoolExecutor(max_workers=len(plan)) as pool:
            pools = list(pool.map(lambda ax: self.gather(ax[1], task.lang, kind == "why", task.text), plan))
        sections, sources, used = [], [], set()
        for (heading, query), found in zip(plan, pools):
            why = kind == "why"
            fresh = [(s, u) for s, u in found if s not in used]
            # the best sentences answer the whole question; then those on this axis; and if the sources
            # had nothing so precise, their opening sentences — but never an apology.
            found = ([p for p in fresh if topics.covers(task.text, p[0])]
                     or [p for p in fresh if on_axis(query, p[0])] or fresh[:PER_AXIS])
            if not found:
                continue
            texts = [s for s, _ in found]
            scores = textrank(texts, kb.terms(f"{task.text} {causal.expand(query, task.lang) if why else query}"),
                              boost=causal.weights(texts) if why else None)
            best = causal.pick(texts, scores, PER_AXIS) if why else sorted(np.argsort(-scores)[:PER_AXIS])  # reading order
            sections.append((heading or (query if kind == "compare" else ""), [texts[i] for i in best]))
            used.update(texts[i] for i in best)
            sources += [found[i][1] for i in best]
        self.step("رتّبتُ الجمل بخوارزمية TextRank", f"{sum(len(s) for _, s in sections)} جملة من {len(set(sources))} مصدر")
        sections = [(h, s[:MAX_POINTS]) for h, s in sections]
        text = weave(kind, topic, sections, task.lang)
        if not text:
            return self.fail("لم أجد في المصادر جملًا كافية للإجابة عن هذا السؤال المفتوح")
        conf = 0.75 if len(sections) == len(plan) else 0.6
        if kind == "why" and not any(causal.is_causal(x) for _, sec in sections for x in sec):
            conf = 0.5   # no sentence states a reason: the answer is only background, and its confidence says so
        return self.ok(text, conf, list(dict.fromkeys(sources)), {"kind": kind, "sections": sections}, entity=topic)
