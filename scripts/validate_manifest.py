#!/usr/bin/env python3
"""Validate archive metadata offline; optionally reconcile a saved asset inventory.

No document download or network access. Inventory checks compare listed metadata,
not received bytes; use audit_mirror.py for proof of GitHub mirror contents.
"""

import argparse
import collections
import datetime
import json
import pathlib
import re
import sys
import tomllib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "TelemetryWorks/rcc-106-standards"
KINDS = {"full", "front-matter", "chapter", "appendix", "annex", "handbook",
         "standard", "schema", "change-marked", "companion"}
TEXT = {"edition", "kind", "title", "path", "asset", "mirror_url", "sha256",
        "retrieved", "distribution"}
OPTIONAL_TEXT = {"chapter", "part", "appendix", "annex", "note", "pdf_created", "distribution_text"}


def safe_component(value):
    return (bool(value) and value not in {".", ".."} and
            not any(ord(c) < 32 or c in '<>:"/\\|?*' for c in value) and
            not value.endswith((".", " ")) and
            value.split(".")[0].upper() not in {"CON", "PRN", "AUX", "NUL",
                *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))})


def source_url(value):
    if not isinstance(value, str) or any(c.isspace() or ord(c) < 32 for c in value):
        return False
    try:
        parsed = urllib.parse.urlsplit(value)
        return (parsed.scheme in {"https", "http"} and bool(parsed.hostname) and
                parsed.username is None and parsed.password is None and parsed.port != 0)
    except ValueError:
        return False


def text_errors(doc, prefix):
    errors = []
    for field in sorted(TEXT):
        if not isinstance(doc.get(field), str) or not doc[field].strip():
            errors.append(f"{prefix}.{field}: required nonempty string")
    for field in sorted(OPTIONAL_TEXT & doc.keys()):
        if not isinstance(doc[field], str) or not doc[field].strip():
            errors.append(f"{prefix}.{field}: expected nonempty string")
    return errors


def source_errors(doc, prefix):
    errors = []
    fields = ["original_urls", "original_filenames"]
    if "archived_from" in doc:
        fields.append("archived_from")
    for field in fields:
        values = doc.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
            errors.append(f"{prefix}.{field}: required nonempty array of nonempty strings")
        elif field != "original_filenames" and not all(source_url(v) for v in values):
            errors.append(f"{prefix}.{field}: expected HTTP(S) URLs without credentials or whitespace")
    return errors


def number_errors(doc, prefix):
    errors = []
    for field in ["size", *(["pages"] if "pages" in doc else [])]:
        if type(doc.get(field)) is not int or doc[field] <= 0:
            errors.append(f"{prefix}.{field}: expected positive integer")
    return errors


def metadata_errors(doc, prefix):
    errors = []
    if doc["kind"] not in KINDS:
        errors.append(f"{prefix}.kind: unrecognized document kind")
    if not re.fullmatch(r"[0-9a-f]{64}", doc["sha256"]):
        errors.append(f"{prefix}.sha256: expected 64 lowercase hexadecimal characters")
    for field in ["retrieved", *(["pdf_created"] if "pdf_created" in doc else [])]:
        try:
            if datetime.date.fromisoformat(doc[field]).isoformat() != doc[field]:
                raise ValueError
        except ValueError:
            errors.append(f"{prefix}.{field}: expected YYYY-MM-DD date")
    if doc["distribution"] not in {"A", "unknown"}:
        errors.append(f"{prefix}.distribution: expected A or unknown")
    if doc["distribution"] == "A" and not doc.get("distribution_text") and not doc.get("note"):
        errors.append(f"{prefix}.distribution: A needs distribution_text or a note recording evidence")
    return errors


def path_errors(doc, prefix):
    errors = []
    for field in ["edition", "asset"]:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", doc[field]) or not safe_component(doc[field]):
            errors.append(f"{prefix}.{field}: expected safe release tag or asset name")
    parts = doc["path"].split("/")
    if len(parts) < 3 or parts[0] != "files" or not all(safe_component(p) for p in parts):
        errors.append(f"{prefix}.path: expected safe relative path under files/")
    return errors


def identity_errors(doc, prefix, paths, keys, blobs):
    errors = []
    # Case-folding catches collisions when the same archive is fetched on Windows.
    path_key = doc["path"].casefold()
    asset_key = (doc["edition"].casefold(), doc["asset"].casefold())
    if path_key in paths or asset_key in keys:
        errors.append(f"{prefix}: duplicate path or edition/asset pair")
    paths.add(path_key)
    keys.add(asset_key)
    expected = f"https://github.com/{REPO}/releases/download/{doc['edition']}/{doc['asset']}"
    if doc["mirror_url"] != expected:
        errors.append(f"{prefix}.mirror_url: repository, release and asset must match identity")
    if doc["sha256"] in blobs and blobs[doc["sha256"]] != doc["size"]:
        errors.append(f"{prefix}.size: identical hashes must have identical sizes")
    blobs[doc["sha256"]] = doc["size"]
    return errors


def validate(data):
    errors = []
    docs = data.get("document") if isinstance(data, dict) else None
    if not isinstance(docs, list) or not docs:
        return ["document must be a nonempty array of tables"]
    paths, keys, blobs = set(), set(), {}
    for index, doc in enumerate(docs):
        prefix = f"document[{index}]"
        if not isinstance(doc, dict):
            errors.append(f"{prefix}: must be a table")
            continue
        structural = text_errors(doc, prefix) + source_errors(doc, prefix) + number_errors(doc, prefix)
        if structural:
            errors.extend(structural)
            continue
        errors.extend(metadata_errors(doc, prefix))
        errors.extend(path_errors(doc, prefix))
        errors.extend(identity_errors(doc, prefix, paths, keys, blobs))
    return errors


def parse_manifest(contents):
    try:
        data = tomllib.loads(contents.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"Cannot parse manifest: {type(exc).__name__}") from exc
    errors = validate(data)
    if errors:
        raise ValueError("\n".join(errors))
    return data["document"]


def load_manifest(path):
    try:
        contents = pathlib.Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f"Cannot read manifest: {type(exc).__name__}") from exc
    return parse_manifest(contents)


def totals(docs):
    blobs = {d["sha256"]: d["size"] for d in docs}
    return {"records": len(docs), "releases": len({d["edition"] for d in docs}),
            "bytes": sum(d["size"] for d in docs), "unique_blobs": len(blobs),
            "unique_blob_bytes": sum(blobs.values())}


def inventory_errors(docs, releases):
    """Reconcile a saved audit inventory, without fetching asset bodies."""
    if not isinstance(releases, list):
        return ["inventory must be an array of releases"]
    expected = {(d["edition"], d["asset"]): d for d in docs}
    actual = collections.defaultdict(list)
    try:
        for release in releases:
            for asset in release["assets"]:
                actual[release["tag"], asset["name"]].append(asset)
        errors = []
        for key in expected.keys() | actual.keys():
            matches = actual[key]
            if key not in expected or len(matches) != 1:
                errors.append(f"inventory {key!r}: extra, missing or duplicate asset")
            elif (type(matches[0]["size"]) is not int or matches[0]["size"] != expected[key]["size"] or
                  matches[0]["browser_download_url"] != expected[key]["mirror_url"] or
                  matches[0]["state"] != "uploaded"):
                errors.append(f"inventory {key!r}: size, URL or state mismatch")
        return errors
    except (KeyError, TypeError):
        return ["inventory has malformed release/asset metadata"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=pathlib.Path, default=ROOT / "manifest.toml")
    parser.add_argument("--inventory", type=pathlib.Path, help="saved audit inventory JSON (metadata only)")
    args = parser.parse_args(argv)
    try:
        docs = load_manifest(args.manifest)
        if args.inventory:
            errors = inventory_errors(docs, json.loads(args.inventory.read_text(encoding="utf-8")))
            if errors:
                raise ValueError("\n".join(errors))
    except (ValueError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print(json.dumps(totals(docs), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
