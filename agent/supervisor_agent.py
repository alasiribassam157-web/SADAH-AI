"""[02] Supervisor agent: understands the question, splits it, and decides which agents answer.

Perception comes from the router brain (core/fast_brain.py through core/inference.py, NumPy only);
compound questions are split by composer.py.  Each sub-question gets a plan:
    primary   — the agent that answers
    witnesses — independent agents asked at the same time, so the critic can cross-check
    fallback  — agents tried in order if the primary fails
"""
import re

from agent import composer, markets, math_engine
from agent.base_agent import AgentResult, BaseAgent, Task
from agent.critic_rules import keyword_intent
from agent.facts import match_relation
from agent.message_bus import MessageBus
from core.inference import BrainInference

_OPEN = re.compile(r"^(?:كيف|لماذا|ليش|ليه|اشرح|وضح|وضّح|حلل|حلّل|ما (?:أسباب|اسباب|أهمية|اهمية|فوائد|أضرار|اضرار|الفرق)|"
                   r"why|how (?:does|do|did|can)|explain|analy[sz]e|what (?:causes|are the (?:causes|benefits|effects)))",
                   re.IGNORECASE)
_NEWS = re.compile(r"أخبار|اخبار|آخر (?:الأخبار|المستجدات)|مستجدات|حدث اليوم|عاجل|news|latest|breaking|today'?s", re.I)
_SYMBOLIC = set(math_engine.STRONG_OPS)
# intent -> (primary, witnesses, fallback)
ROUTES = {
    "chat": ("Companion", [], []),
    "translate": ("Translation", [], ["Wiki"]),
    "units": ("Units", [], ["NumericMath"]),
    "datetime": ("Chrono", [], []),
    "weather": ("EnvPrayer", [], []),
    "prayer": ("EnvPrayer", [], []),
    "code": ("CodeArchitect", [], ["CodeSynthesizer"]),
    "file": ("Sandbox", [], []),
    "system": ("Sandbox", [], []),
}


class SupervisorAgent(BaseAgent):
    name = "Supervisor"
    sector = "القيادة والتواصل"
    timeout = 3.0

    def __init__(self):
        super().__init__()
        self.brain = BrainInference("router")

    def perceive(self, text: str) -> tuple[str, float, dict]:
        """(intent, confidence, distribution) from the neural router; keywords if the brain is missing."""
        if self.brain.ready or self.brain.reload():
            return self.brain.predict(text)
        intent = keyword_intent(text) or "web"
        return intent, 0.5, {intent: 0.5}

    def route(self, text: str, intent: str) -> dict:
        """The plan for one sub-question once its intent is known (after the critic's review)."""
        if intent in ROUTES:
            primary, witnesses, fallback = ROUTES[intent]
        elif intent == "python":
            symbolic = math_engine.detect(text) in _SYMBOLIC
            primary, witnesses, fallback = ("SymbolicMath", [], ["NumericMath"]) if symbolic else \
                ("NumericMath", [], ["SymbolicMath"])
        elif intent == "currency":
            gold = markets.handles(text) or markets.asks_price(text) and not re.search(r"دولار|ريال|يورو|\$", text)
            primary, witnesses, fallback = ("Markets", [], ["Forex"]) if gold else ("Forex", [], ["Markets"])
        elif _NEWS.search(text):
            primary, witnesses, fallback = "OpenWeb", [], ["Wiki"]
        elif composer.is_comparison(text) or _OPEN.search(text.strip()):
            primary, witnesses, fallback = "Synthesis", [], ["LocalKB", "Wiki", "OpenWeb"]
        elif match_relation(text):
            primary, witnesses, fallback = "Wikidata", ["Wiki"], ["LocalKB", "Wiki"]
        else:
            primary, witnesses, fallback = "LocalKB", [], ["Wiki", "Wikidata", "OpenWeb"]
        return {"text": text, "intent": intent, "primary": primary, "witnesses": witnesses, "fallback": fallback}

    def handle(self, task: Task) -> AgentResult:
        """Split the question and perceive each part; the plan travels in data["parts"]."""
        parts = composer.split_compound(task.text)
        if len(parts) > 1:
            count = "جزأين" if len(parts) == 2 else f"{len(parts)} أجزاء"
            self.step(f"سَداة قسّمت السؤال إلى {count}", " | ".join(parts))
        plans = []
        for part in parts:
            intent, conf, dist = self.perceive(part)
            top = " · ".join(f"{k} {v:.0%}" for k, v in sorted(dist.items(), key=lambda kv: -kv[1])[:3])
            self.step(f"العقل الموجّه: {intent}", top, confidence=conf)
            plans.append({"text": part, "intent": intent, "confidence": conf})
        return AgentResult(self.name, True, "", max(p["confidence"] for p in plans), data={"parts": plans})

    def execute(self, bus: MessageBus, task: Task, plan: dict) -> tuple[AgentResult, dict[str, AgentResult]]:
        """Ask the primary with its witnesses in parallel; if it fails, walk the fallback chain."""
        sub = Task(plan["text"], task.lang, plan["intent"], task.session, task.allow_exec, dict(task.context))
        names = [plan["primary"]] + [w for w in plan["witnesses"] if w != plan["primary"]]
        bus.note(self.name, f"سَداة وجّهت «{sub.text}» إلى {' + '.join(names)}")
        replies = bus.broadcast(names, sub, self.name, primary=plan["primary"])
        best = replies[plan["primary"]]
        if not (best.ok and best.confidence >= 0.5):
            chain = [n for n in plan["fallback"] if n not in replies]
            alt = bus.first_success(chain, sub, "Critic") if chain else None
            if alt:
                best, replies[alt.agent] = alt, alt
        return best, replies
