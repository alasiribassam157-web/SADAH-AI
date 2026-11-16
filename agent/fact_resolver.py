"""One door for fact questions: pre-baked core facts (no network) → live Wikidata → silent text fallback."""
from agent import core_facts, fact_fallback
from agent.facts import fact_details, match_relation


def resolve(question: str, lang: str) -> dict | None:
    """The best available fact for a supported question; None only when no source knows it."""
    rel = match_relation(question)
    if not rel:
        return None
    prop, entity, tpl_ar, tpl_en = rel
    tpl = tpl_ar if lang == "ar" else tpl_en
    return (core_facts.lookup(prop, entity, tpl, lang) or fact_details(question, lang)
            or fact_fallback.rescue(prop, entity, tpl, lang))
