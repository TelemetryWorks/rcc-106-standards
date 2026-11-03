#!/usr/bin/env python3
"""Audit GitHub release inventories and stream every asset through SHA-256.

Requires Python 3.11+ and authenticated gh. Never uses official-source fallback,
cached document bytes, or executes archived files. Evidence defaults to ignored
files/audits/. Re-running with --resume reuses successful checkpoint rows only
when the manifest and complete initial release inventory have not changed.
"""

import argparse
import collections
import concurrent.futures
import datetime
import hashlib
import http.client
import json
import pathlib
import shutil
import subprocess
import urllib.parse
import urllib.request

from validate_manifest import parse_manifest

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "TelemetryWorks/rcc-106-standards"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def api(endpoint):
    result = subprocess.check_output(
        ["gh", "api", "--paginate", "--slurp", endpoint], cwd=ROOT
    )
    return [item for page in json.loads(result) for item in page]


def inventory():
    releases = api(f"repos/{REPO}/releases?per_page=100")

    def one(release):
        assets = api(f"repos/{REPO}/releases/{release['id']}/assets?per_page=100")
        return {
            "id": release["id"], "tag": release["tag_name"],
            "draft": release["draft"], "prerelease": release["prerelease"],
            "assets": sorted([
                {key: a.get(key) for key in (
                    "id", "name", "size", "state", "updated_at", "digest",
                    "browser_download_url"
                )} for a in assets
            ], key=lambda a: a["id"]),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        return sorted(pool.map(one, releases), key=lambda r: r["id"])


def download(task):
    tag, asset = task
    url = asset["browser_download_url"]
    for attempt in range(1, 4):
        result = {"release": tag, "asset_id": asset["id"],
                  "name": asset["name"], "url": url, "started": now(),
                  "attempt": attempt, "inventory_size": asset["size"]}
        sha = hashlib.sha256()
        size = 0
        try:
            request = urllib.request.Request(url, headers={
                "User-Agent": "rcc-106-standards-mirror-audit/1.0",
                "Accept-Encoding": "identity",
            })
            with urllib.request.urlopen(request, timeout=90) as response:
                result.update(http_status=response.status,
                              final_host=urllib.parse.urlsplit(response.url).hostname,
                              content_length=response.headers.get("Content-Length"),
                              content_type=response.headers.get("Content-Type"),
                              etag=response.headers.get("ETag"),
                              last_modified=response.headers.get("Last-Modified"))
                while block := response.read(1 << 20):
                    sha.update(block)
                    size += len(block)
            result.update(bytes=size, sha256=sha.hexdigest(), finished=now())
            result["status"] = "downloaded" if size == asset["size"] else "size_mismatch"
            return result
        except (OSError, ValueError, http.client.HTTPException) as exc:
            result.update(status="download_error", error_type=type(exc).__name__,
                          http_error=getattr(exc, "code", None), bytes=size,
                          finished=now())
    return result


def load_checkpoints(output, binding, resume):
    checkpoints = output / "downloads.jsonl"
    completed = {}
    if not checkpoints.exists():
        return completed
    if not resume:
        raise ValueError("Evidence already exists; use --resume or a new --output")
    if json.loads((output / "binding.json").read_text()) != binding:
        raise ValueError("Audit inputs changed")
    for line in checkpoints.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("Malformed checkpoint row; preserve evidence and use a new --output") from exc
        if row["status"] == "downloaded":
            completed[row["asset_id"]] = row
    return completed


def collect_downloads(tasks, completed, output):
    pending = [t for t in tasks if t[1]["id"] not in completed]
    rows = dict(completed)
    with (output / "downloads.jsonl").open("ab") as log, concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(download, pending):
            log.write(canonical(row) + b"\n")
            log.flush()
            rows[row["asset_id"]] = row
            if len(rows) % 25 == 0 or row["status"] != "downloaded":
                print(f"{len(rows)}/{len(tasks)}: {row['status']} "
                      f"{row['release']}/{row['name']}", flush=True)
    return rows


def mapping_failures(doc, paths, keys):
    failures = []
    parsed = urllib.parse.urlsplit(doc["mirror_url"])
    expected_path = f"/{REPO}/releases/download/{doc['edition']}/{doc['asset']}"
    if parsed.scheme != "https" or parsed.netloc != "github.com" or urllib.parse.unquote(parsed.path) != expected_path or parsed.query or parsed.fragment:
        failures.append("incorrect_mirror_url")
    local_path = pathlib.PurePosixPath(doc["path"])
    if local_path.is_absolute() or ".." in local_path.parts or local_path.parts[0] != "files":
        failures.append("unsafe_local_path")
    if paths[doc["path"]] != 1 or keys[doc["edition"], doc["asset"]] != 1:
        failures.append("duplicate_manifest_path_or_asset")
    return failures


def received_byte_failures(doc, matches, row):
    if row is None:
        return ["missing_download_evidence"] if len(matches) == 1 else []
    failures = []
    if row["status"] != "downloaded":
        failures.append(row["status"])
    if row.get("sha256") != doc["sha256"]:
        failures.append("sha256_mismatch")
    if row["bytes"] != doc["size"] or matches[0]["size"] != doc["size"]:
        failures.append("size_mismatch")
    if row["url"] != doc["mirror_url"]:
        failures.append("inventory_url_differs_from_manifest")
    if matches[0]["state"] != "uploaded":
        failures.append("asset_not_uploaded")
    return failures


def reconcile_records(docs, tasks, rows):
    by_key = collections.defaultdict(list)
    for tag, asset in tasks:
        by_key[tag, asset["name"]].append(asset)
    expected = {(d["edition"], d["asset"]) for d in docs}
    records = []
    paths = collections.Counter(d["path"] for d in docs)
    keys = collections.Counter((d["edition"], d["asset"]) for d in docs)
    for index, doc in enumerate(docs):
        key = doc["edition"], doc["asset"]
        matches = by_key[key]
        failures = []
        if len(matches) != 1:
            failures.append("missing_asset" if not matches else "duplicate_asset")
        failures.extend(mapping_failures(doc, paths, keys))
        row = rows.get(matches[0]["id"]) if len(matches) == 1 else None
        failures.extend(received_byte_failures(doc, matches, row))
        records.append({"index": index, "edition": doc["edition"], "asset": doc["asset"],
                        "path": doc["path"], "expected_size": doc["size"],
                        "expected_sha256": doc["sha256"], "asset_id": row["asset_id"] if row else None,
                        "local_filename_differs": pathlib.PurePosixPath(doc["path"]).name != doc["asset"],
                        "status": "FAIL" if failures else "PASS", "failures": failures})
    return {"records": records,
            "extra_assets": [{"release": tag, **a} for tag, a in tasks if (tag, a["name"]) not in expected],
            "duplicate_release_asset_names": [list(k) for k, v in by_key.items() if len(v) > 1]}


def build_summary(docs, initial, final, rows, reconciliation, metadata):
    records = reconciliation["records"]
    tasks = [(r["tag"], a) for r in initial for a in r["assets"]]
    unique = {d["sha256"]: d["size"] for d in docs}
    remote_unique = {r["sha256"]: r["bytes"] for r in rows.values() if r["status"] == "downloaded"}
    digest_mismatches = [a["id"] for _, a in tasks if a.get("digest") and
                         a["digest"] != "sha256:" + rows.get(a["id"], {}).get("sha256", "")]
    return {**metadata, "inventory_unchanged": initial == final,
               "records": len(docs), "record_bytes": sum(d["size"] for d in docs),
               "unique_manifest_blobs": len(unique), "unique_manifest_blob_bytes": sum(unique.values()),
               "unique_remote_blobs": len(remote_unique), "unique_remote_blob_bytes": sum(remote_unique.values()),
               "github_digest_mismatches": digest_mismatches,
               "local_filename_mappings": sum(r["local_filename_differs"] for r in records),
               "releases": len(initial), "assets": len(tasks), "extra_assets": reconciliation["extra_assets"],
               "download_evidence_rows": len(rows),
               "missing_download_asset_ids": [a["id"] for _, a in tasks if a["id"] not in rows],
               "duplicate_release_asset_names": reconciliation["duplicate_release_asset_names"],
               "download_statuses": dict(collections.Counter(r["status"] for r in rows.values())),
               "downloaded_bytes": sum(r["bytes"] for r in rows.values()),
               "passing_records": sum(r["status"] == "PASS" for r in records),
               "failed_records": [r for r in records if r["status"] != "PASS"]}


def audit_failed(summary):
    return int(bool(summary["failed_records"]) or bool(summary["extra_assets"]) or
               bool(summary["duplicate_release_asset_names"]) or bool(summary["missing_download_asset_ids"]) or
               bool(summary["github_digest_mismatches"]) or not summary["inventory_unchanged"] or
               any(status != "downloaded" for status in summary["download_statuses"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path,
                        default=ROOT / "files/audits" / now()[:10])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = (ROOT / "manifest.toml").read_bytes()
    try:
        docs = parse_manifest(manifest)
    except ValueError as exc:
        parser.error(str(exc))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    print("Enumerating all release assets (two inventory workers)...", flush=True)
    initial = inventory()
    binding = {"manifest_sha256": hashlib.sha256(manifest).hexdigest(), "inventory_sha256": digest(initial)}
    try:
        completed = load_checkpoints(output, binding, args.resume)
    except ValueError as exc:
        parser.error(str(exc))
    write_json(output / "binding.json", binding)
    write_json(output / "inventory-before.json", initial)
    tasks = [(r["tag"], a) for r in initial for a in r["assets"]]
    free = shutil.disk_usage(output).free
    print(f"{len(docs)} records; {len(initial)} releases; {len(tasks)} assets; "
          f"{free:,} free disk bytes; {len(completed)} reusable checkpoints", flush=True)
    rows = collect_downloads(tasks, completed, output)
    print("Re-enumerating release inventories to detect concurrent asset changes...", flush=True)
    final = inventory()
    write_json(output / "inventory-after.json", final)
    reconciliation = reconcile_records(docs, tasks, rows)
    metadata = {"completed": now(), "manifest_commit": commit, **binding,
                "disk_free_before_bytes": free, "reused_checkpoints": len(completed)}
    summary = build_summary(docs, initial, final, rows, reconciliation, metadata)
    write_json(output / "records.json", reconciliation["records"])
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    return audit_failed(summary)


if __name__ == "__main__":
    raise SystemExit(main())
