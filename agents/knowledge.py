"""Knowledge agents: each one asks a single source and replies with a Message (claim + evidence).

Wikidata    — structured facts (capital, population, founder …): the primary answer.
Wikipedia   — reads the whole introduction of the subject's article: the independent witness.
Researcher  — local library (BM25), then Wikipedia: answers «what is …» questions.
"""
import re

import httpx

from agent.facts import fact_details
from agent.research import intro, lookup
from agents.message import ANSWER, FAIL, Message

_NET_ERRORS = (httpx.HTTPError, KeyError, ValueError)
_DIACRITICS = re.compile(r"[ً-ْٰـ]")


def wikidata(req: dict) -> Message:
    try:
        fact = fact_details(req["text"], req["lang"])
    except _NET_ERRORS as exc:
        return Message("Wikidata", FAIL, content=f"تعذّر الاتصال: {exc}")
    if not fact:
        return Message("Wikidata", FAIL, content="لا توجد معلومة مطابقة")
    return Message("Wikidata", ANSWER, content=fact["answer"], value=re.sub(r"\*", "", str(fact["value"])),
                   evidence=fact["url"], confidence=0.9, data=fact)


def wikipedia(req: dict) -> Message:
    """The witness: fetch the subject's article independently of Wikidata."""
    try:
        page = intro(req["topic"], req["lang"], timeout=5)
    except _NET_ERRORS as exc:
        return Message("Wikipedia", FAIL, content=f"تعذّر الاتصال: {exc}")
    if not page:
        return Message("Wikipedia", FAIL, content=f"لا توجد مقالة عن «{req['topic']}»")
    title, text, url = page
    return Message("Wikipedia", ANSWER, content=_DIACRITICS.sub("", text), value=title, evidence=url,
                   confidence=0.7)


def researcher(req: dict) -> Message:
    """Definitions and general questions: local library first, then Wikipedia (agent/research.py)."""
    try:
        found = lookup(req["text"], req["lang"])
    except _NET_ERRORS as exc:
        return Message("Researcher", FAIL, content=f"Web request failed: {exc}")
    if not found:
        return Message("Researcher", FAIL, content="لم أجد إجابة لهذا السؤال." if req["lang"] == "ar"
                       else "I couldn't find an answer to that.")
    title, text, url = found
    return Message("Researcher", ANSWER, content=text, value=title, evidence=url, confidence=0.6,
                   data={"title": title})
