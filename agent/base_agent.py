"""SADAH 2.0 — the base every micro-agent inherits: one task in, one result (with its thinking) out."""
import re
import threading
import time
from dataclasses import dataclass, field

_AR = re.compile(r"[؀-ۿ]")


@dataclass
class Task:
    text: str                                   # the question (or sub-question) to answer
    lang: str = ""                              # "ar" / "en"; detected when empty
    intent: str = ""                            # the router brain's intent, if known
    session: str = ""                           # conversation id (memory, companion)
    allow_exec: bool = False                    # real code execution: developer's machine only
    context: dict = field(default_factory=dict)  # results of earlier agents, entity, hints

    def __post_init__(self):
        self.text = (self.text or "").strip()
        self.lang = self.lang or ("ar" if _AR.search(self.text) else "en")


@dataclass
class TraceStep:
    agent: str
    title: str          # «سداة تبحث في ويكيبيديا…»
    detail: str = ""
    status: str = "ok"  # ok / warn / error
    confidence: float = 0.0
    ms: int = 0

    def as_step(self, stage: str = "tool") -> dict:
        """Same shape as the orchestrator's thinking steps (shown under the answer)."""
        conf = f" · {self.confidence:.0%}" if self.confidence else ""
        return {"stage": stage, "title": f"{self.agent}: {self.title}{conf} ({self.ms} ms)",
                "detail": self.detail, "status": self.status}


@dataclass
class AgentResult:
    agent: str
    ok: bool
    answer: str = ""                              # markdown shown to the person
    confidence: float = 0.0                       # 0..1
    sources: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)      # raw values other agents can check
    trace: list[TraceStep] = field(default_factory=list)
    entity: str = ""                              # main subject, for follow-up questions
    ms: int = 0


class BaseAgent:
    """Subclasses set name/sector/intents/keywords and implement handle(task)."""
    name = "BaseAgent"
    sector = ""
    intents: frozenset = frozenset()              # router intents this agent serves
    keywords: str = ""                            # regex of words that point to this agent
    timeout = 8.0                                 # seconds the bus waits for this agent

    def __init__(self):
        self._kw = re.compile(self.keywords, re.IGNORECASE) if self.keywords else None
        self._local = threading.local()           # each request keeps its own thinking steps

    def can_handle(self, task: Task) -> float:
        """0..1: how well this agent fits the task (intent match, then keywords)."""
        score = 0.7 if task.intent and task.intent in self.intents else 0.0
        if self._kw and self._kw.search(task.text):
            score += 0.3
        return min(score, 1.0)

    def handle(self, task: Task) -> AgentResult:
        raise NotImplementedError(f"{self.name} must implement handle()")

    def run(self, task: Task) -> AgentResult:
        """Time the agent, keep its thinking steps, and turn any crash into an honest failure."""
        self._local.trace, self._local.t0 = [], time.time()
        try:
            result = self.handle(task)
        except Exception as exc:  # an agent must never take the whole answer down
            result = self.fail(f"تعذّر عليّ إكمال المهمة: {type(exc).__name__}: {exc}")
        result.ms = int((time.time() - self._local.t0) * 1000)
        result.trace = self._local.trace + result.trace
        return result

    # --- helpers for subclasses
    def step(self, title: str, detail: str = "", status: str = "ok", confidence: float = 0.0):
        if not hasattr(self._local, "trace"):
            self._local.trace, self._local.t0 = [], time.time()
        ms = int((time.time() - self._local.t0) * 1000)   # time since this agent started
        self._local.trace.append(TraceStep(self.name, title, detail, status, confidence, ms))

    def ok(self, answer: str, confidence: float, sources=(), data=None, entity: str = "") -> AgentResult:
        self.step("تحققتُ من النتيجة", ", ".join(sources)[:300], "ok", confidence)
        return AgentResult(self.name, True, answer, confidence, list(sources), data or {}, entity=entity)

    def fail(self, reason: str, data=None) -> AgentResult:
        self.step("لم أجد إجابة موثوقة", reason[:300], "warn")
        return AgentResult(self.name, False, reason, 0.0, data=data or {})
