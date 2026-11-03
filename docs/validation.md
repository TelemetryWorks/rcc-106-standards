# Archive validation

Python 3.11 or newer, standard library only:

```sh
python scripts/validate_manifest.py
python -m unittest discover -s scripts -p 'test_*.py' -v
```

These commands do not download documents. The validator checks required
metadata and types, positive sizes, lowercase SHA-256 values, dates, source
URLs, mirror repository/release/asset identity, and portable relative paths
under `files/`. Paths and edition/asset pairs must be unique, including when
case-folded for Windows. Distinct records can share identical bytes; identical
hashes must agree on size. Distribution A requires recorded marking evidence.
The validator does not judge that evidence or contact issuing organizations.

Output totals are computed from the manifest: record count/bytes, release
count, and distinct-hash count/bytes. No corpus count is hardcoded. An existing
saved audit inventory can also be checked without network access:

```sh
python scripts/validate_manifest.py --inventory files/audits/2026-11-03/inventory-before.json
```

That optional check compares asset names, missing/extra/duplicate assets,
sizes, URLs and upload states. Inventory metadata alone does not prove remote
bytes. Use the full audit for that purpose.

## Routine CI

`Archive validation` runs on pull requests and pushes to `main`, using
GitHub-hosted Ubuntu and Windows runners with Python 3.11. It runs only the
manifest validator and offline tests. There is no package installation or
document download step. Tests use temporary directories and mocked HTTP/API
responses to cover corruption, fallback, verify mode, errors, audit evidence,
inventory changes and bound checkpoint resume.

Both downloader commands validate the manifest before network access. The
ordinary fetch command can fall back to official sources after a failed or
corrupt mirror download. The audit command never does so: only bytes actually
received from GitHub release URLs can establish a mirror result.

## Manual full mirror audit

In GitHub Actions, select **Full GitHub mirror audit (manual)**, then **Run
workflow**. This workflow is `workflow_dispatch` only: no pull request, push,
schedule or Loop triggers it. It downloads roughly the manifest's reported
record-byte total (currently about 1 GB), streams hashes without retaining
document bodies, and limits both inventory and download concurrency to two.
Its job timeout is 45 minutes. The concurrency group permits at most one
running and one pending audit; a newer dispatch can replace an older pending
run. It is not a guaranteed FIFO queue.

The evidence artifact is named `mirror-audit-<run ID>-<attempt>`. It includes
manifest/tool snapshots, commit identity, inventories, checkpoints and final
results. The upload step runs even when a preceding step fails, so available
partial evidence can be inspected. Runner cancellation, a hard timeout or a
GitHub service failure can still prevent artifact delivery. Retention is
**30 days**; download evidence before it expires if it must be kept longer.
GitHub creates no release or document assets during this workflow.

Local interrupted audits can resume with `--resume` and the same output
directory. Successful checkpoints are reused only with the same manifest and
complete inventory binding; failed downloads are retried. GitHub workflow
reruns start fresh: no previous-run artifact is silently trusted as proof.

## Workflow security and action pins

Both workflows grant only `contents: read`, disable persisted checkout
credentials and use full commit SHA pins. The manual audit's `GH_TOKEN` is
scoped to its audit step for authenticated inventory reads. Evidence includes
public source URLs and final response hostnames, never redirect query strings
or token values. No repository secret is required. Neither workflow grants
write permission or uses `pull_request_target`.

Pins verified against official action repositories on 2026-11-03:

| Action | Release | Commit |
|---|---|---|
| actions/checkout | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/setup-python | [v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0) | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` |
| actions/upload-artifact | [v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |

The pinned action definitions use Node 24 on GitHub-hosted runners. Sources:
[GitHub workflow syntax and permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[GitHub secure use guidance](https://docs.github.com/en/actions/reference/security/secure-use),
[GitHub concurrency behavior](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency),
and [artifact retention and upload behavior](https://github.com/actions/upload-artifact).

The manual full-audit workflow was not dispatched as part of implementing
these checks. Offline tests and PR/push CI validate the lightweight path;
they do not claim an end-to-end execution of the manual network workflow.
