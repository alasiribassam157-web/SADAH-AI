"""Internal critic: validates plans before execution and results after, with self-repair."""
import re

from agent import composer, date_math, markets, math_engine, units
from agent.chat_replies import is_small_talk
from agent.code_kb import detect_language
from agent.critic_rules import (CONFIDENCE_FLOOR, _CODE_TASK, _DEFINE, _MATH, _STRONG_MATH, _TIME_WORDS,
                                 keyword_intent)
from agent.live_skills import find_currencies
from agent.tools import WORKSPACE, ToolResult, _BLOCKED


def review_intent(msg: str, intent: str, confidence: float) -> tuple[str, str]:
    """Return (final_intent, note). Overrides the network only when it is unsure or implausible."""
    final, note = _review_confidence(msg, intent, confidence)
    text = msg.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    # SADAH v5 reasoning skills take precedence when the question clearly needs them.
    op = math_engine.detect(msg)
    if op and math_engine.has_math(msg) and final != "code" and (op in math_engine.STRONG_OPS or final not in ("units", "currency")):
        return "python", note + " Symbolic math problem — solving it step by step."
    if date_math.handles(msg) and (final in ("web", "python", "chat", "units", "datetime")
                                   or (final == "prayer" and date_math.mentions_event(msg))):
        return "datetime", note + " Date reasoning (days until / age / gap between dates)."
    if final in ("datetime", "weather", "prayer", "translate") and _DEFINE.match(msg.strip()) \
            and keyword_intent(msg) != final and not _TIME_WORDS.search(msg):
        return "web", note + " A «what is …» question with no live-data words — looking it up."
    if markets.asks_price(msg) and final != "code":
        return "currency", note + " A live market price (gold / silver / crypto)."
    if composer.is_comparison(msg) and final in ("web", "chat", "python", "units"):
        return "web", note + " A comparison — looking up both sides and comparing."
    if final == "python" and not _MATH.search(text):
        if detect_language(msg):
            return "code", note + " A programming language is named but no math — answering as a coding question."
        # «1 inch to cm» / «حول لي 2000 ين» look numeric but are conversions
        fallback = "currency" if find_currencies(msg) else "units" if units.is_conversion(msg) else "web"
        return fallback, note + f" No arithmetic in the question — answering with {fallback} instead."
    if final == "units" and not units.is_conversion(msg) and not find_currencies(msg) and _MATH.search(text):
        return "python", note + " Arithmetic, not a unit conversion — calculating."
    if final in ("web", "chat", "currency", "units") and _STRONG_MATH.search(text):
        return "python", note + " The question contains arithmetic — calculating instead."
    if final in ("weather", "datetime", "currency", "units") and detect_language(msg):
        return "code", note + " A programming language is named — answering as a coding question."
    if final == "code" and not detect_language(msg) and keyword_intent(msg) != "code":
        return "web", note + " No programming language or coding words — answering via web search instead."
    if final in ("web", "chat") and _CODE_TASK.search(msg):
        return "code", note + " A clear coding task (loop, function, class…) — answering as a coding question."
    if final in ("web", "chat", "weather") and units.is_conversion(msg):
        return "units", note + " A number with two compatible units — converting instead of searching."
    named = set(find_currencies(msg))
    if final in ("units", "web", "chat", "translate") and (len(named) >= 2 or (named and markets.PRICE.search(msg))):
        return "currency", note + " A currency is named with a price question — converting money."
    if final == "chat" and not is_small_talk(msg):
        return "web", note + " Not small talk — answering via web search instead."
    return final, note


def _review_confidence(msg: str, intent: str, confidence: float) -> tuple[str, str]:
    if confidence >= CONFIDENCE_FLOOR:
        return intent, f"Neural confidence {confidence:.0%} ≥ {CONFIDENCE_FLOOR:.0%} — accepted."
    alt = keyword_intent(msg)
    if alt and alt != intent:
        return alt, f"Low confidence ({confidence:.0%}); keyword cross-check prefers '{alt}'."
    if not alt and intent == "chat":
        # An unrecognised question is better answered by a search than by the canned greeting.
        return "web", f"Low confidence ({confidence:.0%}) and no keyword match — answering via web search."
    return intent, f"Low confidence ({confidence:.0%}) but no better alternative — proceeding."


def _repair_python(code: str) -> tuple[str, list[str]]:
    fixes = []
    if "^" in code and "**" not in code:
        code, fixes = code.replace("^", "**"), fixes + ["'^' → '**' (power operator)"]
    code2 = re.sub(r"(\d)\s*\(", r"\1*(", code)
    if code2 != code:
        code, fixes = code2, fixes + ["implicit multiplication made explicit"]
    return code, fixes


def review_plan(plan: dict) -> tuple[bool, dict, list[str]]:
    """Pre-execution check. Returns (approved, possibly-corrected plan, notes)."""
    tool, args, notes = plan["tool"], plan["args"], []
    if tool == "python":
        code = args["code"]
        if plan.get("source") == "expr" and "^" in code:
            # Valid Python, but in natural-language math '^' means power, not XOR.
            args["code"] = code = code.replace("^", "**")
            notes.append("Semantic fix: '^' interpreted as power (**), not bitwise XOR.")
        try:
            compile(code, "<sadah>", "exec")
            notes.append("Syntax check passed.")
        except SyntaxError as err:
            fixed, fixes = _repair_python(code)
            try:
                compile(fixed, "<sadah>", "exec")
                args["code"] = fixed
                notes.append(f"Syntax error ({err.msg}) self-corrected: " + "; ".join(fixes))
            except SyntaxError:
                return False, plan, [f"Syntax error not repairable: {err.msg} (line {err.lineno})"]
    elif tool == "file":
        if plan["action"] in ("create", "read", "delete") and not args.get("name"):
            return False, plan, ["No file name detected — please specify e.g. notes.txt"]
        notes.append(f"Target path confined to {WORKSPACE.name}/ — OK.")
    elif tool == "system":
        cmd = args.get("command", "")
        if not cmd:
            return False, plan, ["No command detected — wrap it in backticks, e.g. `dir`"]
        if _BLOCKED.search(cmd):
            return False, plan, [f"Command rejected as destructive: {cmd}"]
        notes.append("Command passed the safety filter.")
    elif tool == "web":
        if len(args.get("query", "")) < 2:
            return False, plan, ["Search query is empty."]
        notes.append(f"Query: “{args['query']}”.")
    else:
        notes.append(f"Skill input accepted: “{args.get('query', '')[:120]}”.")
    return True, plan, notes


def review_result(plan: dict, result: ToolResult) -> tuple[bool, str]:
    """Post-execution verification."""
    if not result.ok:
        return False, "Tool reported failure — output shown for diagnosis."
    if plan["tool"] == "file" and plan["action"] == "create":
        written = (WORKSPACE / plan["args"]["name"]).read_text(encoding="utf-8")
        if written != plan["args"].get("content", ""):
            return False, "Read-back mismatch: file content differs from request!"
        return True, "Read-back verified: file content matches exactly."
    if plan["tool"] == "python" and "Traceback" in result.output:
        return False, "Runtime traceback detected."
    if plan["tool"] == "web" and "🔗 http" not in result.output:
        return False, "No verifiable source returned."
    if plan["tool"] == "code" and "```" not in result.output:
        return False, "No code block in the answer."
    return True, "Result validated."
