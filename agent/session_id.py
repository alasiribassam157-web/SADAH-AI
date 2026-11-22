"""Visitor session ids: only an unguessable, browser-made id may address the server's conversation memory.

The UI sends crypto.randomUUID(). Anything shorter or with odd characters («1», «admin») gets no server memory at
all, so a guessed id can never read or overwrite another visitor's name, city or last subject.
"""
import re

_VALID = re.compile(r"[A-Za-z0-9_-]{16,64}")


def clean(raw: str) -> str:
    """The id itself when it looks browser-generated; '' (a throw-away memory, see Companion._state) otherwise."""
    return raw if _VALID.fullmatch(raw or "") else ""
