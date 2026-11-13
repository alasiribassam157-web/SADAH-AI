"""[09] Stylist agent: turns the agents' findings into fluent, connected Arabic (or English) text.

It never adds a fact: it only cleans sentences, removes repeats, and links them with fixed rhetorical
templates and connectors.  Every sentence it outputs came from a source agent.
"""
import re

from agent.base_agent import AgentResult, BaseAgent, Task

_CLUTTER = re.compile(r"\s*\((?:[^()]*[a-zA-Z0-9][^()]*)\)|\[\d+\]")
_SPACES = re.compile(r"\s{2,}")
CONNECTORS = {"ar": ["", "كذلك، ", "وإضافةً إلى ذلك، ", "ومن جهة أخرى، ", "علاوةً على ذلك، ", "وأخيرًا، "],
              "en": ["", "Moreover, ", "In addition, ", "On the other hand, ", "It is also worth noting that ",
                     "Finally, "]}
INTRO = {  # kind -> opening line ({t} = topic)
    "ar": {"how": "هذا ما تشرحه المصادر عن طريقة عمل «{t}»:", "why": "هذه أبرز الأسباب والعوامل المتعلقة بـ «{t}»:",
           "compare": "مقارنة بين {t} بحسب ما ورد في المصادر:", "analyze": "تحليل «{t}» من عدة جوانب:",
           "define": "هذا ما تقوله المصادر عن «{t}»:", "merge": "جمعتُ لك الإجابات التالية:"},
    "en": {"how": "Here is how «{t}» works, according to the sources:", "why": "The main causes and factors behind «{t}»:",
           "compare": "A comparison of {t}, based on the sources:", "analyze": "An analysis of «{t}» from several angles:",
           "define": "What the sources say about «{t}»:", "merge": "Here are the answers I gathered:"},
}
OUTRO = {"ar": "ℹ️ صاغت سَداة هذه الإجابة من جمل المصادر نفسها دون إضافة معلومات من عندها.",
         "en": "ℹ️ SADAH built this answer from the sources' own sentences, adding no information of her own."}


def polish(sentence: str) -> str:
    """Clean one sentence: no citation marks or Latin clutter in brackets, tidy spaces and punctuation."""
    s = _SPACES.sub(" ", _CLUTTER.sub("", sentence)).strip(" ،,;؛")
    s = re.sub(r"\s+([،,.؟?!:])", r"\1", s)
    if s and s[-1] not in ".!؟?:":
        s += "."
    return s


def _key(sentence: str) -> frozenset:
    return frozenset(w for w in re.findall(r"\w+", sentence.lower()) if len(w) > 2)


def dedupe(sentences: list[str], limit: float = 0.6) -> list[str]:
    """Drop sentences that repeat an earlier one (word overlap above `limit`)."""
    kept, keys = [], []
    for s in sentences:
        k = _key(s)
        if k and all(len(k & o) / max(len(k | o), 1) < limit for o in keys):
            kept.append(s)
            keys.append(k)
    return kept


def connect(sentences: list[str], lang: str) -> list[str]:
    """Link consecutive sentences with connectors (the first and an already-connected one stay as they are)."""
    out, words = [], CONNECTORS[lang]
    for i, s in enumerate(sentences):
        lead = words[min(i, len(words) - 1)] if i else ""
        if i == len(sentences) - 1 and i > 1:
            lead = words[-1]
        starts_linked = s.startswith(("و", "ف")) or re.match(r"^(?:كما|إضافة|لكن|بينما|moreover|however|also|but)\b",
                                                             s, re.I)
        out.append(s if not lead or starts_linked else lead + s[0].lower() + s[1:] if lang == "en" else lead + s)
    return out


def weave(kind: str, topic: str, sections: list[tuple[str, list[str]]], lang: str) -> str:
    """Opening line, then one block per section (heading + connected points), then the honesty note."""
    blocks = [INTRO[lang].get(kind, INTRO[lang]["define"]).format(t=topic)]
    for heading, sentences in sections:
        points = connect(dedupe([polish(s) for s in sentences if s.strip()]), lang)
        if not points:
            continue
        body = "\n".join(f"• {p}" for p in points)
        blocks.append(f"**{heading}**\n{body}" if heading else body)
    if len(blocks) == 1:
        return ""
    return "\n\n".join(blocks + [OUTRO[lang]])


class StylistAgent(BaseAgent):
    name = "Stylist"
    sector = "الاستنتاج والصياغة"
    timeout = 1.0

    def merge(self, results: list[AgentResult], lang: str) -> str:
        """Several agents' answers in one connected reply (used for multi-part questions)."""
        good = [r for r in results if r.ok and r.answer.strip()]
        if len(good) == 1:
            return good[0].answer
        return "\n\n".join([INTRO[lang]["merge"]] + [r.answer.strip() for r in good])

    def handle(self, task: Task) -> AgentResult:
        """task.context: kind, topic, sections=[(heading, [sentences])] — or results=[AgentResult]."""
        if task.context.get("results"):
            self.step("سَداة تدمج إجابات الوكلاء في رد واحد")
            text = self.merge(task.context["results"], task.lang)
        else:
            self.step("سَداة تصوغ الجمل في نص مترابط", "تنظيف · حذف التكرار · أدوات ربط")
            text = weave(task.context.get("kind", "define"), task.context.get("topic", task.text),
                         task.context.get("sections", []), task.lang)
        return self.ok(text, 0.9) if text else self.fail("لا توجد جمل كافية للصياغة")
