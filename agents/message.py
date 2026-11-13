"""The one message format every SADAH agent speaks on the bus.

A message is not free text: it carries the claim, the evidence behind it and how sure the sender is,
so other agents can check it instead of trusting it.
"""
from dataclasses import dataclass, field

REQUEST, ANSWER, CONFIRM, OBJECT, FAIL = "request", "answer", "confirm", "object", "fail"
KIND_AR = {REQUEST: "طلب", ANSWER: "جواب", CONFIRM: "تأكيد", OBJECT: "اعتراض", FAIL: "تعذّر"}


@dataclass
class Message:
    sender: str                 # agent name, e.g. "Wikidata"
    kind: str                   # request / answer / confirm / object / fail
    content: str = ""           # the claim in words (markdown for answers)
    value: str = ""             # the bare value, comparable by other agents ("طوكيو", "123300000")
    evidence: str = ""          # source url or the calculation steps
    confidence: float = 0.0     # 0..1, the sender's own estimate
    data: dict = field(default_factory=dict)  # anything else (raw number, kind, entity name)
    ms: int = 0                 # how long the sender took

    def line(self) -> str:
        """One readable line for the thinking steps."""
        text = self.value or self.content
        text = text if len(text) <= 120 else text[:117] + "…"
        src = f" · {self.evidence}" if self.evidence else ""
        return f"{self.sender} → {KIND_AR.get(self.kind, self.kind)}: {text}{src} ({self.ms} ms)"
