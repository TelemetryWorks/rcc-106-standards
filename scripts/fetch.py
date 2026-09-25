#!/usr/bin/env python3
"""Download and verify documents listed in manifest.toml.

Each document is fetched from this repository's GitHub Release copy
(``mirror_url``) and, if that fails, from each of its ``original_urls`` in
turn. Every download is checked against the manifest's ``size`` and
``sha256`` before it is kept; a file that is already present and verifies is
not downloaded again.

Standard library only (Python 3.11+ for ``tomllib``).

Usage:
    python scripts/fetch.py                          # everything (~711 MiB)
    python scripts/fetch.py --edition 106-24R1       # one edition
    python scripts/fetch.py --edition 106-22 --edition 106-23 --chapter 9
    python scripts/fetch.py --kind handbook          # RCC 123 / 124 handbooks
    python scripts/fetch.py --verify                 # check local files only
    python scripts/fetch.py --list --chapter 9       # show what would be fetched
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tomllib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.toml"
USER_AGENT = "rcc-106-standards-fetch/1.0 (+https://github.com/TelemetryWorks/rcc-106-standards)"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verifies(path: Path, doc: dict) -> bool:
    return path.is_file() and path.stat().st_size == doc["size"] and sha256_of(path) == doc["sha256"]


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response, dest.open("wb") as out:
        while block := response.read(1 << 20):
            out.write(block)


def fetch(doc: dict, dest_root: Path) -> str:
    """Fetch one document; return a status word."""
    target = dest_root / doc["path"]
    if verifies(target, doc):
        return "present"
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    for url in [doc["mirror_url"], *doc["original_urls"]]:
        try:
            download(url, partial)
        except OSError as exc:
            print(f"    {url}: {exc}", file=sys.stderr)
            continue
        if verifies(partial, doc):
            partial.replace(target)
            return "fetched"
        print(f"    {url}: size or sha256 mismatch", file=sys.stderr)
    partial.unlink(missing_ok=True)
    return "FAILED"


def selected(docs: list[dict], args: argparse.Namespace) -> list[dict]:
    out = []
    for doc in docs:
        if args.edition and doc["edition"] not in args.edition:
            continue
        if args.kind and doc["kind"] not in args.kind:
            continue
        if args.chapter and doc.get("chapter") not in args.chapter:
            continue
        out.append(doc)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--edition", action="append", help="edition / release tag, e.g. 106-24R1 or rcc-124-22 (repeatable)")
    parser.add_argument("--kind", action="append", help="full, chapter, appendix, annex, front-matter, handbook, schema (repeatable)")
    parser.add_argument("--chapter", action="append", help="chapter number, e.g. 9 (repeatable)")
    parser.add_argument("--dest", type=Path, default=ROOT, help="root directory for the files/ tree (default: repository root)")
    parser.add_argument("--verify", action="store_true", help="only verify local files; download nothing")
    parser.add_argument("--list", action="store_true", help="only list the selected documents")
    args = parser.parse_args(argv)

    docs = selected(tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["document"], args)
    if not docs:
        print("No documents match the selection.", file=sys.stderr)
        return 1

    failures = 0
    for doc in docs:
        if args.list:
            print(f"{doc['edition']:<12} {doc['kind']:<12} {doc['size']:>11,}  {doc['path']}")
            continue
        if args.verify:
            status = "ok" if verifies(args.dest / doc["path"], doc) else "BAD/MISSING"
        else:
            status = fetch(doc, args.dest)
        failures += status in ("FAILED", "BAD/MISSING")
        print(f"{status:<11} {doc['path']}")

    if not args.list:
        print(f"{len(docs) - failures} of {len(docs)} documents OK.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
