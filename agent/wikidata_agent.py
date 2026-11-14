"""[05] Wikidata agent: exact facts (capital, population, area, founder, birth date …) from Wikidata.

The answer carries the raw value and its kind, so the critic can compare it with Wikipedia's text.
"""
import httpx

from agent.base_agent import AgentResult, BaseAgent, Task
from agent.facts import fact_details, match_relation, numeric_fact

LABELS = {"P36": "العاصمة", "P1082": "عدد السكان", "P571": "تاريخ التأسيس", "P38": "العملة", "P37": "اللغة الرسمية",
          "P569": "تاريخ الميلاد", "P19": "مكان الميلاد", "P2046": "المساحة", "P112": "المؤسس", "P286": "المدرب",
          "P2048": "الارتفاع", "P2044": "الارتفاع"}


class WikidataAgent(BaseAgent):
    name = "Wikidata"
    sector = "المعرفة والبحث"
    intents = frozenset({"web"})
    keywords = r"عاصمة|سكان|مساحة|عملة|اللغة الرسمية|مؤسس|ولد|تأسس|ارتفاع|capital|population|area|currency|founded|born"
    timeout = 9.0

    def can_handle(self, task: Task) -> float:
        return 0.95 if match_relation(task.text) else 0.0

    def number(self, entity: str, prop: str, lang: str) -> tuple[str, float, str, str] | None:
        """(name, value, unit, url) for a quantity, used by comparisons."""
        try:
            return numeric_fact(entity, prop, lang)
        except (httpx.HTTPError, KeyError, ValueError):
            return None

    def handle(self, task: Task) -> AgentResult:
        rel = match_relation(task.text)
        if not rel:
            return self.fail("السؤال ليس عن خاصية معروفة في Wikidata")
        prop, entity = rel[0], rel[1]
        label = LABELS.get(prop.split("|")[0], prop)
        self.step("سَداة تسأل Wikidata", f"الكيان: {entity} · الخاصية: {label} ({prop})")
        try:
            fact = fact_details(task.text, task.lang)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            return self.fail(f"تعذّر الاتصال بـ Wikidata: {exc}")
        if not fact:
            return self.fail(f"لم أجد {label} لـ «{entity}» في Wikidata")
        self.step(f"وجدتُ القيمة: {str(fact['value'])[:80]}", fact["url"], confidence=0.9)
        data = {**fact, "entity": entity, "label": label}
        return self.ok(fact["answer"], 0.9, [fact["url"]], data, entity=fact["name"])
