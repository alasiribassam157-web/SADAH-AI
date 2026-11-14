"""[07] Translation agent: Arabic ⇄ English through translate.py (built-in dictionary, then Wikidata labels).

It also unifies terms for the other agents: term() gives the dictionary equivalent of a word with no
network call, so a search can try «machine learning» when «تعلم الآلة» finds nothing.
"""
import re

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.translate import AR_TO_EN, EN_TO_AR, _norm, translate

_AR = re.compile(r"[؀-ۿ]")


def term(word: str) -> str | None:
    """The other language's word for `word` from the built-in dictionary only (instant, offline)."""
    key = _norm(word)
    table = AR_TO_EN if _AR.search(word) else EN_TO_AR
    hit = table.get(key) or table.get(re.sub(r"^ال", "", key))
    if hit or len(key.split()) < 2:
        return hit
    words = key.split()
    return " ".join(table[w] for w in words) if all(w in table for w in words) else None


class TranslationAgent(BaseAgent):
    name = "Translation"
    sector = "المعرفة والبحث"
    intents = frozenset({"translate"})
    keywords = r"ترجم|ترجمة|معنى|بالانجليزي|بالإنجليزي|بالعربي|translate|in english|in arabic|how do you say"
    timeout = 8.0

    def handle(self, task: Task) -> AgentResult:
        self.step("سَداة تبحث عن الترجمة", "القاموس المدمج أولًا، ثم تسميات Wikidata")
        res = translate(task.text)
        if not res.ok:
            return self.fail(res.output)
        from_dictionary = "wikidata.org" not in res.output
        conf = 0.9 if from_dictionary else 0.75
        self.step("وجدتُ الترجمة في " + ("القاموس المدمج" if from_dictionary else "Wikidata"), confidence=conf)
        sources = [] if from_dictionary else ["https://www.wikidata.org"]
        return self.ok(res.output, conf, sources, {"source": "dictionary" if from_dictionary else "wikidata"},
                       entity=res.entity)
