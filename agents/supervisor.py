"""Supervisor: sends a question to independent agents, lets the Critic compare them, then answers.

A fact (capital, population, founding date …) is asked to Wikidata and, at the same time, to Wikipedia.
The Critic marks it ✅ verified (both agree), ℹ️ single source, or ⚠️ conflict (they disagree).
"""
import re

from agent.facts import match_relation
from agent.tools import ToolResult, _clip
from agents import consensus, knowledge
from agents.bus import Bus
from agents.message import ANSWER, CONFIRM, OBJECT, Message

BADGE = {
    "ar": {consensus.VERIFIED: "✅ **موثوق:** مصدران مستقلان متفقان (Wikidata وويكيبيديا).",
           consensus.SINGLE: "ℹ️ **مصدر واحد:** لم أجد مصدرًا ثانيًا يؤكد المعلومة أو ينفيها.",
           consensus.CONFLICT: "⚠️ **المصادر مختلفة:** يذكر Wikidata «{v}» بينما تذكر ويكيبيديا «{s}». تحقّق قبل الاعتماد عليها."},
    "en": {consensus.VERIFIED: "✅ **Verified:** two independent sources agree (Wikidata and Wikipedia).",
           consensus.SINGLE: "ℹ️ **Single source:** no second source confirmed or contradicted this.",
           consensus.CONFLICT: "⚠️ **Sources disagree:** Wikidata says «{v}» but Wikipedia says «{s}». Double-check it."},
}
CRITIC_NOTE = {consensus.VERIFIED: "المصدران متفقان", consensus.SINGLE: "لا يوجد تأكيد من مصدر ثانٍ",
               consensus.CONFLICT: "المصدران مختلفان"}


def research(question: str) -> ToolResult:
    """Answer a «web» question through the agents; the conversation is returned in ToolResult.trace."""
    lang = "ar" if re.search(r"[؀-ۿ]", question) else "en"
    bus = Bus(deadline=12)
    rel = match_relation(question)
    if rel:
        req = {"text": question, "topic": rel[1], "lang": lang}
        replies = bus.ask({"Wikidata": knowledge.wikidata, "Wikipedia": knowledge.wikipedia}, req, primary="Wikidata")
        fact = replies["Wikidata"]
        if fact.kind == ANSWER:
            return _cross_checked(fact, replies["Wikipedia"], bus, lang)
    reply = bus.ask({"Researcher": knowledge.researcher}, {"text": question, "lang": lang})["Researcher"]
    if reply.kind != ANSWER:
        return ToolResult(False, reply.content, trace=bus.steps())
    title = reply.data["title"]
    text = f"**{title}**\n\n{reply.content}\n\n🔗 {reply.evidence}"
    return ToolResult(True, _clip(text), entity=title, trace=bus.steps())


def _cross_checked(fact: Message, witness: Message, bus: Bus, lang: str) -> ToolResult:
    status, seen = consensus.judge(fact.data, witness.content if witness.kind == ANSWER else "")
    kind = OBJECT if status == consensus.CONFLICT else CONFIRM
    detail = f"Wikidata: {fact.value} · Wikipedia: {seen or '—'}"
    bus.post(Message("Critic", kind, content=detail, value=CRITIC_NOTE[status],
                     confidence={"verified": 0.95, "single": 0.7, "conflict": 0.4}[status]))
    badge = BADGE[lang][status].format(v=fact.value, s=seen)
    links = [f"🔗 {fact.evidence}"]
    if status != consensus.SINGLE and witness.evidence:
        links.append(f"🔗 {witness.evidence}")
    text = f"{fact.content}\n\n{badge}\n\n" + "\n".join(links)
    return ToolResult(True, text, entity=fact.data.get("name", ""), trace=bus.steps())
