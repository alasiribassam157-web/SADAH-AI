"""Registry of text sources: a source may feed training only when its entry is human-written and approved."""
import json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "sources.json"


class SourceError(RuntimeError):
    pass


def load(path: Path = PATH) -> dict:
    return {k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items() if not k.startswith("_")}


def require(names, path: Path = PATH) -> dict:
    """Return the entries for `names`, or raise SourceError naming every source that is missing or not approved."""
    reg, bad = load(path), []
    for name in names:
        entry = reg.get(name)
        if entry is None:
            bad.append(f"{name}: not in registry")
        elif not entry.get("human_written", False):
            bad.append(f"{name}: not marked human-written")
        elif entry.get("status") != "approved":
            bad.append(f"{name}: status is {entry.get('status')!r}, needs 'approved'")
    if bad:
        raise SourceError("; ".join(bad))
    return {n: reg[n] for n in names}


def manifest(names, path: Path = PATH) -> list[dict]:
    """Compact record (name, license, url) stored beside a dataset so its provenance travels with it."""
    return [{"name": n, "license": e["license"], "url": e["url"]} for n, e in require(names, path).items()]
