"""[08] Synthesis agent: open questions («كيف»، «لماذا»، «قارن»، «حلّل») answered from real sources.

1. split the question into axes (each side of a comparison, causes, how it works …)
2. gather paragraphs for every axis: the offline library (BM25) and Wikipedia, in parallel
3. rank the sentences with TextRank (NumPy power iteration) mixed with BM25-style relevance
4. hand the best sentences to the stylist, which links them without adding anything
Numeric comparisons («قارن بين سكان مصر والسعودية») go to Wikidata through composer.compare.
"""
import math
import re
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from agent import composer, kb
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
         ("analyze", r"حلل|حلّل|تحليل|أهمية|اهمية|تأثير|analy[sz]e|impact|importance")]
PER_AXIS = 3      # sentences kept per axis
MAX_POINTS = 7


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
    topic = topic or question
    if kind == "why":
        return topic, [("", topic), ("الأسباب", f"أسباب {topic}")]
    if kind == "analyze":
        return topic, [("", topic), ("التأثير والأهمية", f"تأثير {topic}")]
    return topic, [("", topic)]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!؟?؛])\s+", re.sub(r"\s+", " ", text))
    return [p.strip() for p in parts if 40 <= len(p.strip()) <= 400]


def textrank(items: list[str], query: list[str], damping: float = 0.85) -> np.ndarray:
    """Score = 0.5 × centrality in the sentence-similarity graph + 0.5 × relevance to the question."""
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
    return 0.5 * norm(rank) + 0.5 * norm(rel)


class SynthesisAgent(BaseAgent):
    name = "Synthesis"
    sector = "الاستنتاج والصياغة"
    intents = frozenset({"web"})
    keywords = r"^(?:كيف|لماذا|ليش|حلل|قارن)|الفرق بين|أسباب|^(?:how|why|compare|analy[sz]e)"
    timeout = 9.0

    def __init__(self, local: LocalKBAgent | None = None, wiki: WikiAgent | None = None):
        super().__init__()
        self.local, self.wiki = local or LocalKBAgent(), wiki or WikiAgent()

    def gather(self, query: str, lang: str) -> list[tuple[str, str]]:
        """[(sentence, source url)] for one axis: library paragraphs plus the Wikipedia article."""
        found = [(s, p["url"]) for p in self.local.passages(query, lang, 4) if p["coverage"] >= 0.5
                 for s in sentences(p["text"])]
        try:
            page = self.wiki.search(query, lang, 10)
        except Exception:  # Wikipedia down: the library alone still answers
            page = None
        if page:
            found += [(s, page[2]) for s in sentences(page[1])]
        return found

    def handle(self, task: Task) -> AgentResult:
        kind = kind_of(task.text)
        if kind == "compare" and any(re.search(p, task.text, re.I) for p, *_ in composer.PROPERTIES):
            self.step("مقارنة رقمية: سَداة تجلب القيمتين من Wikidata")
            res = composer.compare(task.text)
            if res.ok:
                url = re.findall(r"https?://\S+", res.output)
                return self.ok(res.output, 0.85, url, {"kind": kind}, entity=res.entity)
        topic, plan = axes(task.text, kind)
        count = {1: "محور واحد", 2: "محورين"}.get(len(plan), f"{len(plan)} محاور")
        self.step(f"سَداة قسّمت السؤال إلى {count}", " | ".join(q for _, q in plan))
        with ThreadPoolExecutor(max_workers=len(plan)) as pool:
            pools = list(pool.map(lambda ax: self.gather(ax[1], task.lang), plan))
        sections, sources, used = [], [], set()
        for (heading, query), found in zip(plan, pools):
            need = set(kb.terms(query))
            found = [(s, u) for s, u in found if s not in used
                     and len(need & set(kb.terms(s))) >= max(1, math.ceil(len(need) / 2))]   # stay on the axis
            if not found:
                continue
            texts = [s for s, _ in found]
            scores = textrank(texts, kb.terms(f"{task.text} {query}"))
            best = sorted(np.argsort(-scores)[:PER_AXIS])          # best sentences, in their original order
            sections.append((heading or (query if kind == "compare" else ""), [texts[i] for i in best]))
            used.update(texts[i] for i in best)
            sources += [found[i][1] for i in best]
        self.step("رتّبتُ الجمل بخوارزمية TextRank", f"{sum(len(s) for _, s in sections)} جملة من {len(set(sources))} مصدر")
        sections = [(h, s[:MAX_POINTS]) for h, s in sections]
        text = weave(kind, topic, sections, task.lang)
        if not text:
            return self.fail("لم أجد في المصادر جملًا كافية للإجابة عن هذا السؤال المفتوح")
        conf = 0.75 if len(sections) == len(plan) else 0.6
        return self.ok(text, conf, list(dict.fromkeys(sources)), {"kind": kind, "sections": sections}, entity=topic)
