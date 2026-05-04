import re
from pathlib import Path


def main() -> int:
    import app

    endpoints = {r.endpoint for r in app.app.url_map.iter_rules()}

    unknown: dict[str, set[str]] = {}
    for p in Path("templates").rglob("*.html"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"url_for\(\s*'([^']+)'", txt):
            ep = m.group(1)
            if ep not in endpoints:
                unknown.setdefault(ep, set()).add(str(p))

    print(f"Unknown endpoints: {len(unknown)}")
    for ep in sorted(unknown):
        print(ep)
        for f in sorted(unknown[ep]):
            print(f"  - {f}")

    return 0 if not unknown else 2


if __name__ == "__main__":
    raise SystemExit(main())

