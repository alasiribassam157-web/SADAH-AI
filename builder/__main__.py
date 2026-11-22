"""Try the builder:  python -m builder "أبغى موقع لمطعم باسم بيت الشواء" [--out site.zip]"""
import argparse
import sys
from pathlib import Path

from builder.build import build, to_zip


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("request")
    ap.add_argument("--out", default="site.zip")
    args = ap.parse_args()
    r = build(args.request)
    if r.ok:
        Path(args.out).write_bytes(to_zip(r.files))
        print(f"تم: {args.out} ({', '.join(sorted(r.files))})")
        return 0
    print(r.question or r.message or "؛ ".join(r.problems), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
